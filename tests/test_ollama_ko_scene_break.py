"""Q5: 장면 경계에서 이전/이후 문맥을 끊고 배치를 나눈다(Mock Ollama, 합성 문장)."""
import asyncio
import json
from pathlib import Path
import sys

from GalTransl.Loader import load_transList
from ollama_mock import mock_ollama
from test_ollama_ko import batch, config, engine
from test_ollama_ko_scene import plugin

ROOT = Path(__file__).resolve().parents[1]


def body(call):
    return json.loads(call[1]["messages"][-1]["content"])


def test_plugin_marks_labels_and_custom_break_lines(tmp_path):
    path = tmp_path / "s.txt"
    path.write_text("*scene_a\n朝だ。\n*scene_b\n――そして、現在。\n夜だ。\n", encoding="utf-8")
    entries = plugin().load_file(str(path))
    assert [bool(e.get("scene_break")) for e in entries] == [True, False, True, False, False]
    custom = plugin(sceneBreakPatterns=[r"^\s*\*", r"^――"]).load_file(str(path))
    assert custom[3]["scene_break"] and custom[3]["message"] == "――そして、現在。"  # still translated
    assert [bool(e.get("scene_break")) for e in plugin(sceneBreakPatterns=[]).load_file(str(path))] == [False] * 5


def test_loader_keeps_scene_break():
    trans = load_transList([{"message": "a"}, {"message": "", "scene_break": True}])[0]
    assert not getattr(trans[0], "scene_break", False) and trans[1].scene_break


def _run(tmp_path, items, size=5, **options):
    source = load_transList(items)[0]
    with mock_ollama() as (url, calls):
        async def run():
            e = engine(config(tmp_path, url, followingContext=4, **options))
            try:
                await batch(e, source, tmp_path, size=size, unhit=[r for r in source if r.pre_src])
            finally:
                await e.shutdown()
        asyncio.run(run())
    return [body(c) for c in calls]


def test_context_and_lookahead_stop_at_scene_label(tmp_path):
    first, second = _run(tmp_path, [
        {"message": "朝の教室。"}, {"name": "葵", "message": "おはよう。"},
        {"message": "", "scene_break": True},
        {"message": "放課後の屋上。"}, {"name": "湊", "message": "話がある。"},
    ])
    assert [r["source"] for r in first["input"]] == ["朝の教室。", "おはよう。"]
    assert first["following_context"] == []  # 다음 장면을 미리 보지 않음
    assert [r["source"] for r in second["input"]] == ["放課後の屋上。", "話がある。"]
    assert second["context"] == []  # 이전 장면 번역을 문맥으로 쓰지 않음


def test_translatable_break_line_starts_a_new_batch(tmp_path):
    first, second = _run(tmp_path, [
        {"message": "五年前の夏。"}, {"message": "泣かないで。"},
        {"message": "――そして、現在。", "scene_break": True}, {"message": "クローバーは手帳にある。"},
    ])
    assert [r["source"] for r in first["input"]] == ["五年前の夏。", "泣かないで。"]
    assert [r["source"] for r in second["input"]] == ["――そして、現在。", "クローバーは手帳にある。"]
    assert second["context"] == []
