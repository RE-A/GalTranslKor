import asyncio
import importlib.util
import json
import threading

import pytest
import yaml

from GalTransl.ConfigHelper import CProjectConfig
from GalTransl.Loader import load_transList
from ollama_mock import mock_ollama, translated


def config(tmp_path, endpoint, **options):
    data = {
        "common": {"language": "ja2ko", "splitFile": "no", "gpt.contextNum": 3},
        "backendSpecific": {"Ollama": {
            "endpoint": endpoint, "model": "mock-ko", "retryWait": 0,
            "maxAttempts": 3, **options,
        }},
    }
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    cfg = CProjectConfig(str(tmp_path))
    cfg.bar = lambda *a, **kw: None
    cfg.stop_event = threading.Event()
    return cfg


def engine(cfg):
    from GalTransl.Backend.OllamaTranslate import OllamaTranslate
    return OllamaTranslate(cfg)


def rows(n=7):
    return load_transList([
        {"message": f"雨の駅で、彼女を待っていた。{i}", **({"name": "葵"} if i % 2 else {})}
        for i in range(n)
    ])[0]


async def batch(e, source, path, size=2, hit=None, unhit=None, filename="scene.json"):
    return await e.batch_translate(filename, str(path / filename), source, size,
                                   translist_hit=hit or [],
                                   translist_unhit=source if unhit is None else unhit)


def test_engine_exists():
    assert importlib.util.find_spec("GalTransl.Backend.OllamaTranslate") is not None


@pytest.mark.parametrize("api,path", [("native", "/api/chat"), ("openai", "/v1/chat/completions")])
def test_http_batches_preserve_order_and_bilingual_context(tmp_path, api, path):
    with mock_ollama() as (url, calls):
        async def run():
            e = engine(config(tmp_path, url, api=api))
            try:
                source = rows()
                result = await batch(e, source, tmp_path)
                assert result == source
                assert all(r.pre_dst.startswith("한국어") for r in source)
                assert all(r.trans_by == e.cache_identity for r in source)
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert [p for p, _ in calls] == [path] * 4
        bodies = [json.loads(p["messages"][-1]["content"]) for _, p in calls]
        assert [len(b["input"]) for b in bodies] == [2, 2, 2, 1]
        assert bodies[0]["context"] == []
        assert len(bodies[-1]["context"]) == 3
        assert bodies[1]["context"][-1]["translation"].startswith("한국어")
        assert bodies[1]["context"][-1]["source"].endswith("1")
        assert bodies[0]["input"][1]["speaker"] == "葵"
        assert "한국어" in calls[0][1]["messages"][0]["content"]
        assert calls[0][1]["stream"] is False


@pytest.mark.parametrize("bad", [
    "not json", {"translations": []},
    {"translations": [{"id": 1, "text": "한국어"}, {"id": 1, "text": "한국어"}]},
    {"translations": [{"id": 2, "text": "한국어"}, {"id": 1, "text": "한국어"}]},
    {"translations": [{"id": 1, "text": ""}, {"id": 2, "text": "한국어"}]},
    {"translations": [{"id": 1, "text": "日本語です"}, {"id": 2, "text": "한국어"}]},
    {"translations": [{"id": 1, "text": "English only"}, {"id": 2, "text": "한국어"}]},
])
def test_invalid_batch_is_retried_atomically(tmp_path, bad):
    with mock_ollama([(200, bad)]) as (url, calls):
        async def run():
            e = engine(config(tmp_path, url))
            try:
                source = rows(2)
                await batch(e, source, tmp_path)
                assert all(r.pre_dst.startswith("한국어") for r in source)
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert len(calls) == 2


@pytest.mark.parametrize("status,attempts", [(429, 3), (503, 3), (400, 1), (404, 1)])
def test_http_errors_have_bounded_retries_and_no_cache(tmp_path, status, attempts):
    with mock_ollama([(status, {"error": "synthetic error"})] * 5) as (url, calls):
        async def run():
            e = engine(config(tmp_path, url))
            source = rows(2)
            try:
                with pytest.raises(RuntimeError):
                    await batch(e, source, tmp_path)
                assert all(r.pre_dst == "" for r in source)
                assert not list(tmp_path.glob("*.append.jsonl"))
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert len(calls) == attempts


def test_character_budget_shrinks_history_without_losing_lines(tmp_path):
    with mock_ollama() as (url, calls):
        async def run():
            e = engine(config(tmp_path, url, maxPromptChars=2400))
            try:
                source = rows(8)
                for r in source:
                    r.post_src *= 20
                await batch(e, source, tmp_path, size=8)
                assert all(r.pre_dst for r in source)
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert len(calls) > 1
        assert all(sum(len(m["content"]) for m in p["messages"]) <= 2400 for _, p in calls)


def test_oversized_single_line_is_not_truncated_or_sent(tmp_path):
    with mock_ollama() as (url, calls):
        async def run():
            e = engine(config(tmp_path, url, maxPromptChars=2000))
            source = rows(1)
            source[0].post_src = "あ" * 4000
            try:
                with pytest.raises(ValueError, match="maxPromptChars"):
                    await batch(e, source, tmp_path)
                assert source[0].pre_dst == ""
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert calls == []


@pytest.mark.parametrize("source,target", [
    ("名前は{name}です。", "이름입니다."),
    ("数は%02dです。", "수는 %d입니다."),
    ("上\n下", "위 아래"),
    (r"待って\n次へ[wait]", "기다려"),
    ("<b>こんにちは</b>", "안녕하세요"),
])
def test_placeholder_and_linebreak_validation(tmp_path, source, target):
    with mock_ollama([(200, {"translations": [{"id": 1, "text": target}]})] * 3) as (url, calls):
        async def run():
            e = engine(config(tmp_path, url))
            values = load_transList([{"message": source}])[0]
            try:
                with pytest.raises(RuntimeError):
                    await batch(e, values, tmp_path)
                assert values[0].pre_dst == ""
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert len(calls) == 3


def test_cancellation_does_not_send_or_cache(tmp_path):
    from GalTransl.Service import JobCancelledError
    with mock_ollama() as (url, calls):
        async def run():
            cfg = config(tmp_path, url)
            cfg.stop_event.set()
            e = engine(cfg)
            try:
                with pytest.raises(JobCancelledError):
                    await batch(e, rows(), tmp_path)
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert calls == []


@pytest.mark.parametrize("option,value", [("model", ""), ("api", "bad"), ("maxAttempts", 0), ("apiTimeout", -1), ("maxPromptChars", 0)])
def test_invalid_configuration_rejected_before_io(tmp_path, option, value):
    with pytest.raises(ValueError):
        engine(config(tmp_path, "http://127.0.0.1:1", **{option: value}))


@pytest.mark.parametrize("api,body", [
    ("native", []), ("native", {"done": False, "message": {"content": "{}"}}),
    ("native", {"done": True, "done_reason": "length", "message": {"content": "{}"}}),
    ("openai", {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}),
    ("openai", {"choices": [None]}),
])
def test_malformed_or_truncated_envelope_has_bounded_retries(tmp_path, api, body):
    with mock_ollama([(200, body)] * 3, raw=True) as (url, calls):
        async def run():
            e = engine(config(tmp_path, url, api=api))
            try:
                with pytest.raises(RuntimeError, match="after 3 attempts"):
                    await batch(e, rows(1), tmp_path)
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert len(calls) == 3


def test_valid_placeholders_and_linebreaks_survive(tmp_path):
    source = "{name}さん、%02d個です。\n<b>待って</b>[wait]\\n次へ。"
    target = "{name} 씨, %02d개입니다.\n<b>기다려</b>[wait]\\n다음으로."
    with mock_ollama([(200, {"translations": [{"id": 1, "text": target}]})]) as (url, calls):
        async def run():
            e = engine(config(tmp_path, url))
            values = load_transList([{"message": source}])[0]
            try:
                await batch(e, values, tmp_path)
                assert values[0].pre_dst == target
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert len(calls) == 1


def test_timeout_retries_are_bounded(tmp_path):
    import time
    def slow(payload):
        time.sleep(0.2)
        return translated(payload)
    with mock_ollama([slow] * 3) as (url, calls):
        async def run():
            e = engine(config(tmp_path, url, apiTimeout=0.03))
            try:
                with pytest.raises(RuntimeError, match="after 3 attempts"):
                    await batch(e, rows(1), tmp_path)
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert len(calls) == 3


def test_cancel_during_inflight_request(tmp_path):
    import time
    from GalTransl.Service import JobCancelledError
    started = threading.Event()
    def slow(payload):
        started.set()
        time.sleep(0.5)
        return translated(payload)
    with mock_ollama([slow]) as (url, calls):
        async def run():
            cfg = config(tmp_path, url)
            e = engine(cfg)
            values = rows(1)
            task = asyncio.create_task(batch(e, values, tmp_path))
            try:
                assert await asyncio.to_thread(started.wait, 2)
                cfg.stop_event.set()
                with pytest.raises(JobCancelledError):
                    await asyncio.wait_for(task, timeout=1)
                assert values[0].pre_dst == ""
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert len(calls) == 1


def test_large_glossary_is_budgeted_only_for_selected_batch(tmp_path):
    from GalTransl.Dictionary import CGptDict
    dictionary = tmp_path / "glossary.txt"
    dictionary.write_text("猫\t고양이\t" + "설명" * 190 + "\n犬\t개\t" + "설명" * 190 + "\n", encoding="utf-8")
    with mock_ollama() as (url, calls):
        async def run():
            cfg = config(tmp_path, url, maxPromptChars=1400)
            cfg.gpt_dic = CGptDict([str(dictionary)])
            e = engine(cfg)
            source = load_transList([{"message": "猫です。"}, {"message": "犬です。"}])[0]
            try:
                await e.batch_translate("scene", str(tmp_path / "scene"), source, 2,
                                        gpt_dic=cfg.gpt_dic, translist_unhit=source)
                assert all(r.pre_dst for r in source)
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert len(calls) == 2
        first = json.loads(calls[0][1]["messages"][-1]["content"])
        assert "고양이" in first["glossary"] and "개" not in first["glossary"]
        assert all(sum(len(m["content"]) for m in p["messages"]) <= 1400 for _, p in calls)


def test_malformed_openai_choice_recovers_on_next_response(tmp_path):
    good = {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(
        {"translations": [{"id": 1, "text": "한국어 번역"}]}, ensure_ascii=False)}}]}
    with mock_ollama([(200, {"choices": [None]}), (200, good)], raw=True) as (url, calls):
        async def run():
            e = engine(config(tmp_path, url, api="openai"))
            source = rows(1)
            try:
                await batch(e, source, tmp_path)
                assert source[0].pre_dst == "한국어 번역"
            finally:
                await e.shutdown()
        asyncio.run(run())
        assert len(calls) == 2
