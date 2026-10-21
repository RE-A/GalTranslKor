"""Scene TXT plugin, Korean prompt/context extensions, failure handling and tools.

All model traffic goes to the loopback HTTP Mock; no real Ollama is contacted.
"""
import asyncio
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest
import yaml

from GalTransl.Backend.OllamaQuality import fatal_problems, warning_problems
from GalTransl.Loader import load_transList
from ollama_mock import mock_ollama
from test_ollama_ko import batch, config, engine, rows

ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "examples" / "ollama_ko_scene"
sys.path.insert(0, str(ROOT / "plugins" / "file_vn_scene_txt"))
import file_vn_scene_txt as scene  # noqa: E402


def echo(payload):
    """Synthetic 'translation' that keeps markers, brackets and punctuation."""
    request = json.loads(payload["messages"][-1]["content"])
    return {"translations": [
        {"id": line["id"], "text": re.sub(r"[ぁ-ヿ一-鿿]+", "한국어", line["source"])}
        for line in request["input"]]}


def body(call):
    return json.loads(call[1]["messages"][-1]["content"])


def plugin(**settings):
    conf = yaml.safe_load((ROOT / "plugins/file_vn_scene_txt/file_vn_scene_txt.yaml").read_text(encoding="utf-8"))
    conf["Settings"].update(settings)
    instance = scene.file_plugin()
    instance.gtp_init(conf, {})
    return instance


# ---------------------------------------------------------------- TXT plugin

def test_scene_txt_roundtrip_preserves_bom_crlf_and_untranslated_lines(tmp_path):
    text = ("; コメント\r\n*label\r\n\r\n【葵】「おはよう。」\r\n湊「行こう。」\r\n"
            "  朝日が差し込んだ。  \r\n「名無しの台詞。」\r\n[wait]\r\n（独白だ。）")
    source = tmp_path / "scene.txt"
    source.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    p = plugin()
    entries = p.load_file(str(source))
    assert [e["message"] for e in entries] == [
        "", "", "", "おはよう。", "行こう。", "朝日が差し込んだ。", "「名無しの台詞。」", "", "（独白だ。）"]
    assert [e.get("name") for e in entries][3:5] == ["葵", "湊"]
    out = tmp_path / "out.txt"
    p.save_file(str(out), entries)
    assert out.read_bytes() == source.read_bytes()
    for e in entries:
        if e["message"]:
            e["message"] = "번역"
    entries[3]["name"] = "아오이"
    p.save_file(str(out), entries)
    lines = out.read_bytes().decode("utf-8-sig").split("\r\n")
    assert lines[:5] == ["; コメント", "*label", "", "【아오이】「번역」", "湊「번역」"]
    assert lines[5] == "  번역  " and lines[6] == "번역" and lines[7] == "[wait]"
    assert lines[8] == "번역" and not out.read_bytes().endswith(b"\r\n")


def test_scene_txt_reads_shift_jis_and_writes_utf8(tmp_path):
    source = tmp_path / "sjis.txt"
    source.write_bytes("【葵】「雨だね。」\n".encode("cp932"))
    p = plugin()
    entries = p.load_file(str(source))
    assert entries[0]["message"] == "雨だね。"
    entries[0]["message"] = "비가 오네."
    p.save_file(str(tmp_path / "out.txt"), entries)
    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "【葵】「비가 오네.」\n"


def test_scene_txt_rejects_pattern_without_required_groups():
    with pytest.raises(ValueError, match="name/text"):
        plugin(speakerPatterns=["^(?P<who>.+)$"])


# ------------------------------------------------------------ quality rules

@pytest.mark.parametrize("source,text,problem", [
    ("今日は雨が降っていて、とても寒い一日だった。", "죄송하지만 이 내용은 번역할 수 없습니다.", "refusal"),
    ("今日は雨が降っていて、とても寒い一日だった。", "I'm sorry, but I can't help with that.", "refusal"),
    ("今日は雨が降っていて、とても寒い一日だった。", "今天下雨了，非常寒冷的一天。", "Chinese"),
    ("今日は雨が降っていて、とても寒い一日だった。", "비.", "omission"),
    ("「行こう」と彼は言った。", "가자, 라고 그가 말했다.", "bracket"),
    ("おはよう。", "葵: 좋은 아침.", "speaker"),
    ("今日は雨。", "(Failed)今日は雨。", "failed"),
])
def test_fatal_problems_detect_bad_outputs(source, text, problem):
    found = " ".join(fatal_problems(source, text, speakers=("葵",)))
    assert problem.lower() in found.lower()


def test_quality_rules_accept_legitimate_translations():
    assert fatal_problems("すみません、翻訳できません。", "죄송해요, 번역할 수 없어요.") == []
    assert fatal_problems("ぷにぷにだ。", "ぷにぷに하다.", allow=["ぷにぷに"]) == []
    assert fatal_problems("「行こう」と彼は言った。", "「가자」라고 그가 말했다.") == []
    assert fatal_problems("……", "……") == []
    assert warning_problems("東京タワーを見た。", "東京 타워를 봤다.") == []
    assert "Han characters" in warning_problems("タワーを見た。", "塔 타워를 봤다.")[0]


# ------------------------------------------------------ prompt and context

def test_following_context_and_character_selection(tmp_path):
    (tmp_path / "characters.yaml").write_text(yaml.safe_dump({"characters": [
        {"ja": "葵", "ko": "아오이", "speech": "반말"},
        {"ja": "湊", "ko": "미나토", "aliases": ["湊くん"]},
        {"ja": "結衣", "ko": "유이"},
    ]}, allow_unicode=True), encoding="utf-8")
    source = load_transList([
        {"name": "葵", "message": "おはよう。"}, {"message": "朝の光が眩しい。"},
        {"message": "湊くんはまだ寝ている。"}, {"message": "窓を開けた。"}, {"message": "風が吹いた。"},
    ])[0]
    with mock_ollama() as (url, calls):
        async def run():
            e = engine(config(tmp_path, url, followingContext=2))
            try:
                await batch(e, source, tmp_path, size=2)
            finally:
                await e.shutdown()
        asyncio.run(run())
    first, second, last = (body(c) for c in calls)
    assert [r["source"] for r in first["following_context"]] == ["湊くんはまだ寝ている。", "窓を開けた。"]
    assert last["following_context"] == []
    # 葵 speaks and 湊 is mentioned in look-ahead; 結衣 never appears.
    assert [c["ja"] for c in first["characters"]] == ["葵", "湊"]
    assert first["characters"][0] == {"ja": "葵", "ko": "아오이", "speech": "반말"}
    # The last request's 3-line history no longer contains 葵.
    assert [c["ja"] for c in last["characters"]] == ["湊"]


def test_korean_guideline_sources(tmp_path):
    from GalTransl.Backend.OllamaPrompts import load_korean_guideline
    bundled = load_korean_guideline(None, str(tmp_path))
    assert "성인 대상 장면" in bundled and "翻译" not in bundled
    (tmp_path / "translation_guideline.md").write_text("湊는 항상 반말을 쓴다.", encoding="utf-8")
    assert load_korean_guideline("JapaneseToKorean.md", str(tmp_path)).endswith("湊는 항상 반말을 쓴다.\n")
    (tmp_path / "JapaneseToKorean.md").write_text("프로젝트 전용 지침", encoding="utf-8")
    assert load_korean_guideline("JapaneseToKorean.md", str(tmp_path)).startswith("프로젝트 전용 지침")
    with pytest.raises(ValueError, match="Chinese"):
        load_korean_guideline("Basic.md", str(tmp_path))


def test_system_prompt_uses_guideline_file_and_changes_cache_identity(tmp_path):
    cfg = config(tmp_path, "http://127.0.0.1:1")
    first = engine(cfg)
    assert "성인 대상 장면" in first.system_prompt and "following_context" in first.system_prompt
    (tmp_path / "translation_guideline.md").write_text("호칭은 이름만 쓴다.", encoding="utf-8")
    second = engine(config(tmp_path, "http://127.0.0.1:1"))
    assert "호칭은 이름만 쓴다." in second.system_prompt
    assert first.cache_identity != second.cache_identity
    asyncio.run(first.shutdown())
    asyncio.run(second.shutdown())


# ---------------------------------------------------------- failure policy

def test_repeated_invalid_batch_shrinks_before_failing(tmp_path):
    bad = (200, {"translations": [{"id": 1, "text": "한국어"}]})
    with mock_ollama([bad] * 3) as (url, calls):
        async def run():
            e = engine(config(tmp_path, url))
            source = rows(4)
            try:
                await batch(e, source, tmp_path, size=4)
                assert all(r.pre_dst.startswith("한국어") for r in source)
                assert e.stats["batch_shrinks"] == 1 and e.stats["retries"] == 2
            finally:
                await e.shutdown()
        asyncio.run(run())
    assert [len(body(c)["input"]) for c in calls] == [4, 4, 4, 2, 2]


def test_context_overflow_reported_by_ollama_shrinks_batch(tmp_path):
    def overflow(payload):
        content = json.dumps(echo(payload), ensure_ascii=False)
        return {"done": True, "done_reason": "stop", "prompt_eval_count": 8192, "message": {"content": content}}
    with mock_ollama([overflow] * 10, raw=True) as (url, calls):
        async def run():
            e = engine(config(tmp_path, url, maxAttempts=3, numCtx=8192))
            source = rows(2)
            try:
                await batch(e, source, tmp_path, size=2)
            finally:
                await e.shutdown()
        with pytest.raises(RuntimeError, match="context window overflow"):
            asyncio.run(run())
    assert [len(body(c)["input"]) for c in calls] == [2, 2, 2, 1, 1, 1]


def test_mark_policy_records_failure_and_continues_without_poisoning_context(tmp_path):
    def fail_line_two(payload):
        result = echo(payload)
        for item, line in zip(result["translations"], json.loads(payload["messages"][-1]["content"])["input"]):
            if line["source"].endswith("1"):
                item["text"] = "죄송하지만 번역할 수 없습니다."
        return result
    with mock_ollama([fail_line_two] * 20) as (url, calls):
        async def run():
            e = engine(config(tmp_path, url, onFailure="mark"))
            source = rows(4)
            try:
                await batch(e, source, tmp_path, size=2)
                return source, e
            finally:
                await e.shutdown()
        source, e = asyncio.run(run())
        endpoint = url
    assert source[1].pre_dst == "(Failed)" + source[1].post_src
    assert source[1].problem == "翻译失败"
    assert all("한국어" in r.pre_dst for r in (source[0], source[2], source[3]))
    log = next((tmp_path / "ollama_ko_logs").glob("failures-*.jsonl")).read_text(encoding="utf-8")
    assert json.loads(log)["index"] == source[1].index and "refusal" in log
    later = [body(c) for c in calls if body(c)["input"][0]["source"].endswith("2")][0]
    assert all(not row["translation"].startswith("(Failed)") for row in later["context"])
    stats = json.loads(next((tmp_path / "ollama_ko_logs").glob("stats-*.json")).read_text())
    assert stats["lines_failed"] == 1 and stats["lines_translated"] == 3
    # A failed line is never accepted as a cache hit on the next run.
    again = engine(config(tmp_path, endpoint, onFailure="mark"))
    hits, misses = again.validate_cache_hits(source, list(source), [])
    assert misses == [source[1]]
    asyncio.run(again.shutdown())


def test_token_statistics_and_openai_api_key(tmp_path):
    def native(payload):
        return {"done": True, "done_reason": "stop", "prompt_eval_count": 100, "eval_count": 20,
                "total_duration": 2_000_000_000,
                "message": {"content": json.dumps(echo(payload), ensure_ascii=False)}}
    with mock_ollama([native] * 2, raw=True) as (url, calls):
        async def run():
            e = engine(config(tmp_path, url))
            try:
                await batch(e, rows(4), tmp_path, size=2)
                return dict(e.stats)
            finally:
                await e.shutdown()
        stats = asyncio.run(run())
    assert stats["prompt_tokens"] == 200 and stats["output_tokens"] == 40
    assert stats["model_seconds"] == pytest.approx(4.0)
    headers = []
    with mock_ollama(headers=headers) as (url, calls):
        async def run_openai():
            e = engine(config(tmp_path / "o", url, api="openai", apiKey="local-key"))
            try:
                await batch(e, rows(1), tmp_path)
            finally:
                await e.shutdown()
        asyncio.run(run_openai())
    assert headers[0]["Authorization"] == "Bearer local-key"


# ------------------------------------------------------ full project flow

def scene_project(root, url):
    shutil.copytree(SCENE, root, dirs_exist_ok=True)
    cfg = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    cfg["backendSpecific"]["Ollama"].update(model="mock-ko", endpoint=url, retryWait=0)
    (root / "config.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    return cfg


def cli(*args, cwd=None):
    return subprocess.run([sys.executable, str(ROOT / args[0]), *map(str, args[1:])],
                          capture_output=True, text=True, timeout=120, cwd=cwd)


def test_scene_project_translates_preserves_format_and_resumes(tmp_path):
    project = tmp_path / "장면 프로젝트"
    with mock_ollama([echo] * 200) as (url, calls):
        scene_project(project, url)
        result = cli("run_ollama_ko.py", project)
        assert result.returncode == 0, result.stdout + result.stderr
        first_calls = len(calls)
        source_lines = (project / "gt_input" / "scene_001.txt").read_text(encoding="utf-8").split("\n")
        output_lines = (project / "gt_output" / "scene_001.txt").read_text(encoding="utf-8").split("\n")
        assert len(output_lines) == len(source_lines)
        for before, after in zip(source_lines, output_lines):
            if not before or before[0] in ";*@/[":
                assert after == before
        assert "【아오이】「한국어、한국어。」" in output_lines
        assert not any(re.search(r"[ぁ-ヿ]", line) for line in output_lines
                       if line and line[0] not in ";*@/[")
        report = json.loads((project / "ollama_ko_logs" / "quality_report.json").read_text(encoding="utf-8"))
        assert report["fatal"] == 0 and report["lines"] == report["translated"] > 40
        requests = [body(c) for c in calls]
        assert max(len(b["input"]) for b in requests) == 5
        assert max(len(b["context"]) for b in requests) == 8
        assert any(len(b["following_context"]) == 4 for b in requests)
        assert "아오이" in requests[1]["glossary"] or any("아오이" in b["glossary"] for b in requests)
        again = cli("run_ollama_ko.py", project)
        assert again.returncode == 0, again.stdout + again.stderr
        assert len(calls) == first_calls  # resumed entirely from cache


def test_failed_lines_give_exit_code_2_and_rerun_retranslates_only_them(tmp_path):
    project = tmp_path / "p"
    refusing = [True]

    def refuse_one(payload):
        result = echo(payload)
        for item, line in zip(result["translations"], json.loads(payload["messages"][-1]["content"])["input"]):
            if refusing[0] and "野球部" in line["source"]:
                item["text"] = "I'm sorry, I can't translate this."
        return result
    with mock_ollama([refuse_one] * 300) as (url, calls):
        scene_project(project, url)
        result = cli("run_ollama_ko.py", project)
        assert result.returncode == 2, result.stdout + result.stderr
        report = json.loads((project / "ollama_ko_logs" / "quality_report.json").read_text(encoding="utf-8"))
        fatal = [i for i in report["issues"] if i["level"] == "fatal"]
        assert [(i["code"], i["index"]) for i in fatal] == [("translation failed", 6)]
        output = (project / "gt_output" / "scene_001.txt").read_text(encoding="utf-8").split("\n")
        assert output[5].startswith("(Failed)")
        refusing[0] = False
        before = len(calls)
        result = cli("run_ollama_ko.py", project)
        assert result.returncode == 0, result.stdout + result.stderr
        retried = [body(c) for c in calls[before:]]
        assert [[r["source"] for r in b["input"]] for b in retried] == \
            [["窓の外では、野球部の掛け声が遠くに聞こえる。"]]
        assert retried[0]["context"][-1]["source"] == "放課後の教室には、もう誰も残っていなかった。"


def test_init_project_and_check_before_translation(tmp_path):
    project = tmp_path / "새 게임"
    result = cli("run_ollama_ko.py", project, "--init")
    assert result.returncode == 0, result.stdout + result.stderr
    assert {p.name for p in project.iterdir()} == {
        "config.yaml", "glossary.txt", "characters.yaml", "JapaneseToKorean.md", "gt_input"}
    assert list((project / "gt_input").iterdir()) == []
    assert cli("run_ollama_ko.py", project, "--init").returncode != 0
    shutil.copy2(SCENE / "gt_input" / "scene_001.txt", project / "gt_input" / "a.txt")
    check = cli("check_ollama_ko.py", project)
    assert check.returncode == 2
    report = json.loads((project / "ollama_ko_logs" / "quality_report.json").read_text(encoding="utf-8"))
    assert {i["code"] for i in report["issues"]} == {"missing_translation", "output_missing"}


def test_benchmark_runs_cases_on_excerpt_without_touching_project(tmp_path):
    project = tmp_path / "bench"
    with mock_ollama([echo] * 200) as (url, calls):
        scene_project(project, url)
        result = cli("benchmark_ollama_ko.py", project, "--lines", 12,
                     "--case", "A:-:5:8192", "--case", "B:-:10:8192")
        assert result.returncode == 0, result.stdout + result.stderr
    assert not (project / "gt_output").exists() and not (project / "transl_cache").exists()
    summary = next((project / "ollama_ko_logs" / "benchmark").glob("*/benchmark.json"))
    results = json.loads(summary.read_text(encoding="utf-8"))
    assert [r["case"] for r in results] == ["A", "B"]
    assert all(r["lines"] == 12 and r["failed_lines"] == 0 and r["fatal"] == 0 for r in results)
    assert [r["requests"] for r in results] == [3, 2]
    assert results[0]["memory"]["gpu_share"] == 0.75
    assert (summary.parent / "benchmark.md").is_file()


def test_report_reads_cache_of_files_in_subfolders(tmp_path):
    project = tmp_path / "nested"
    with mock_ollama([echo] * 100) as (url, calls):
        scene_project(project, url)
        (project / "gt_input" / "chapter1").mkdir()
        shutil.move(project / "gt_input" / "scene_001.txt", project / "gt_input" / "chapter1" / "scene_001.txt")
        result = cli("run_ollama_ko.py", project)
        assert result.returncode == 0, result.stdout + result.stderr
    assert (project / "transl_cache" / "chapter1-}scene_001.txt.json").is_file()
    assert (project / "gt_output" / "chapter1" / "scene_001.txt").is_file()
    report = json.loads((project / "ollama_ko_logs" / "quality_report.json").read_text(encoding="utf-8"))
    assert report["fatal"] == 0 and report["files"] == ["chapter1/scene_001.txt"]
