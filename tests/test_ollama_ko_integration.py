"""Full GalTransl jobs with real files/cache and a synthetic HTTP model."""
import asyncio
import json
from pathlib import Path

import pytest
import yaml

from GalTransl import TRANSLATOR_SUPPORTED
from GalTransl.Service import JobSpec, run_job_async
from ollama_mock import mock_ollama, translated


@pytest.fixture(autouse=True)
def isolated_app_data(tmp_path, monkeypatch):
    monkeypatch.setenv("GALTRANSL_DATA_DIR", str(tmp_path / ".galtransl-data"))


def project(root, endpoint, count=12):
    root.mkdir(parents=True, exist_ok=True)
    (root / "gt_input").mkdir(exist_ok=True)
    cfg = {
        "common": {
            "language": "ja2ko", "splitFile": "no", "workersPerProject": 2,
            "gpt.numPerRequestTranslate": 3, "gpt.contextNum": 4,
            "sortBy": "name", "loggingLevel": "warning", "save_steps": 1,
            "linebreakSymbol": "auto",
        },
        "backendSpecific": {"Ollama": {"model": "mock-ko", "endpoint": endpoint, "retryWait": 0}},
        "plugin": {"filePlugin": "file_galtransl_json", "textPlugins": [], "problemPlugins": []},
        "dictionary": {"defaultDictFolder": "Dict", "preDict": [], "postDict": [], "gpt.dict": []},
        "proxy": {"enableProxy": False},
    }
    (root / "config.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    data = [{"message": f"雨が降り続く駅で、約束の人を待っていた。{i}",
             **({"name": "葵"} if i % 2 else {})} for i in range(count)]
    (root / "gt_input" / "scene.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return cfg, data


def run(root):
    return asyncio.run(run_job_async(JobSpec(str(root), "Ollama-ko")))


def test_engine_is_registered():
    assert "Ollama-ko" in TRANSLATOR_SUPPORTED


@pytest.mark.parametrize("count", [12, 120])
def test_mixed_scene_job_and_cache_only_rerun(tmp_path, count):
    with mock_ollama() as (url, calls):
        _, original = project(tmp_path, url, count)
        state = run(tmp_path)
        assert state.success, state.error
        assert len(calls) == count // 3
        output = json.loads((tmp_path / "gt_output" / "scene.json").read_text())
        assert len(output) == len(original)
        assert [r.get("name") for r in output] == [r.get("name") for r in original]
        assert all("한국어" in r["message"] for r in output)
        second = run(tmp_path)
        assert second.success, second.error
        assert len(calls) == count // 3  # zero additional model calls


def test_partial_failure_resumes_from_cache_with_context(tmp_path):
    with mock_ollama([translated] + [(503, {"error": "busy"})] * 3) as (url, calls):
        project(tmp_path, url)
        state = run(tmp_path)
        assert not state.success
        assert len(calls) == 4
        state = run(tmp_path)
        assert state.success, state.error
        assert len(calls) == 7  # first three lines were already cached
        resumed = json.loads(calls[4][1]["messages"][-1]["content"])
        assert len(resumed["context"]) == 3
        assert resumed["context"][-1]["translation"].startswith("한국어")
        assert resumed["input"][0]["source"].endswith("3")


@pytest.mark.parametrize("change", ["model", "temperature", "context", "glossary", "bad_cache"])
def test_cache_invalidation(tmp_path, change):
    with mock_ollama() as (url, calls):
        cfg, _ = project(tmp_path, url, 3)
        assert run(tmp_path).success
        assert len(calls) == 1
        if change == "model":
            cfg["backendSpecific"]["Ollama"]["model"] = "new-model"
        elif change == "temperature":
            cfg["backendSpecific"]["Ollama"]["temperature"] = 0.4
        elif change == "context":
            cfg["common"]["gpt.contextNum"] = 1
        elif change == "glossary":
            (tmp_path / "glossary.txt").write_text("駅\t역\t장소\n", encoding="utf-8")
            cfg["dictionary"]["gpt.dict"] = ["(project_dir)glossary.txt"]
        else:
            cache_file = next((tmp_path / "transl_cache").glob("*.json"))
            data = json.loads(cache_file.read_text())
            for row in data:
                row["pre_dst"] = "日本語です"
            cache_file.write_text(json.dumps(data), encoding="utf-8")
        (tmp_path / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
        state = run(tmp_path)
        assert state.success, state.error
        assert len(calls) == 2
        if change == "glossary":
            assert "역" in calls[-1][1]["messages"][-1]["content"]


def test_concurrent_files_do_not_share_context(tmp_path):
    with mock_ollama() as (url, calls):
        project(tmp_path, url, 9)
        other = [{"message": f"海辺を歩いて、貝殻を拾った。{i}"} for i in range(9)]
        (tmp_path / "gt_input" / "sea.json").write_text(json.dumps(other), encoding="utf-8")
        state = run(tmp_path)
        assert state.success, state.error
        assert len(calls) == 6
        for _, payload in calls:
            body = json.loads(payload["messages"][-1]["content"])
            is_sea = "海辺" in body["input"][0]["source"]
            assert all(("海辺" in row["source"]) == is_sea for row in body["context"])


def test_parallel_file_chunking_fails_with_actionable_configuration_error(tmp_path):
    with mock_ollama() as (url, calls):
        cfg, _ = project(tmp_path, url, 20)
        cfg["common"].update(splitFile="Num", splitFileNum=12)
        (tmp_path / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
        state = run(tmp_path)
        assert not state.success
        assert "splitFile: no" in state.error
        assert calls == []


@pytest.mark.parametrize("outcome", ["failed", "cancelled"])
def test_job_closes_http_client_after_failure_or_cancellation(tmp_path, monkeypatch, outcome):
    import threading
    from GalTransl.Frontend import LLMTranslate
    original_factory = LLMTranslate.init_gptapi
    engines = []

    async def tracking_factory(cfg):
        instance = await original_factory(cfg)
        engines.append(instance)
        return instance

    monkeypatch.setattr(LLMTranslate, "init_gptapi", tracking_factory)
    stop = threading.Event()
    def cancelled(payload):
        stop.set()
        return translated(payload)

    actions = [(404, {"error": "missing model"})] if outcome == "failed" else [cancelled]
    with mock_ollama(actions) as (url, calls):
        project(tmp_path, url, 3)
        async def run_and_inspect():
            state = await run_job_async(JobSpec(str(tmp_path), "Ollama-ko"), stop_event=stop)
            background = [task for task in asyncio.all_tasks()
                          if task is not asyncio.current_task() and not task.done()
                          and any(name in task.get_coro().__qualname__
                                  for name in ("update_progress_title", "auto_tune_workers"))]
            assert background == []
            return state
        state = asyncio.run(run_and_inspect())
        assert state.status == outcome
        assert len(engines) == 1
        assert engines[0].client.is_closed
