"""존댓말·반말 검사(Kiwi). 합성 문장, 경고만 낼 뿐 번역을 바꾸지 않음."""
import pytest

pytest.importorskip("kiwipiepy")

from GalTransl.KoreanSpeech import ja_politeness, ko_politeness, speech_level_warnings


def test_japanese_politeness():
    assert ja_politeness("進路希望の紙を持ってきました。") == "polite"
    assert ja_politeness("もう少しだけ考えさせてください。") == "polite"
    assert ja_politeness("お二人様ですか？") == "polite"
    assert ja_politeness("遅いよ、湊くん。") == "plain"
    assert ja_politeness("なんで黙ってたんだよ！") == "plain"
    assert ja_politeness("佐伯先生。") is None


@pytest.mark.parametrize("text,level", [
    ("진로 희망서 가져왔습니다.", "polite"), ("조금만 더 생각해 보겠습니다.", "polite"),
    ("세트로 두 개 주세요.", "polite"), ("아니에요. 계절 쪽이요.", "polite"),
    ("미안. 선생님한테 붙잡혀 있었어.", "plain"), ("늦었잖아, 미나토.", "plain"),
    ("왜 말 안 한 거야!", "plain"), ("이쪽으로 오렴.", "plain"),
    ("거절할 수 없죠.", "polite"), ("갑니까?", "polite"), ("하여튼 솔직하지 못하다니까.", "plain"),
    ("사에키 선생님.", None), ("……", None),
])
def test_korean_politeness(text, level):
    assert ko_politeness(text) == level


def _line(index, speaker, source, translation, scene_break=False):
    return {"index": index, "speaker": speaker, "source": source, "translation": translation,
            "scene_break": scene_break}


def test_polite_source_translated_as_plain_is_flagged():
    warnings = speech_level_warnings([_line(1, "湊", "持ってきました。", "가져왔어.")])
    assert warnings[1][0].startswith("politeness_mismatch")


def test_inconsistent_level_for_same_speaker_and_source_level():
    lines = [_line(i, "葵", src, dst) for i, (src, dst) in enumerate([
        ("遅いよ。", "늦었잖아."), ("また進路の話なの？", "또 진로 얘기야?"), ("決めたよ。", "정했어."),
        ("待ってたの。", "기다렸어요."),  # 혼자 존댓말
    ], 1)]
    warnings = speech_level_warnings(lines)
    assert list(warnings) == [4] and warnings[4][0].startswith("politeness_inconsistent")
    # 장면이 바뀌면 다른 그룹
    lines[3]["scene_break"] = True
    assert speech_level_warnings(lines) == {}


def test_speech_to_expectation():
    profiles = [{"ja": "湊", "ko": "미나토", "speech_to": {"先生": "존댓말", "葵": "반말"}},
                {"ja": "先生", "ko": "선생님", "aliases": ["佐伯先生"]}, {"ja": "葵", "ko": "아오이"}]
    names = {"先生": ["先生", "佐伯先生"], "葵": ["葵"]}
    lines = [_line(1, "湊", "佐伯先生、これ。", "사에키 선생님, 이거 받아."),
             _line(2, "湊", "葵、これ。", "아오이, 이거 받아.")]
    warnings = speech_level_warnings(lines, profiles, names)
    assert list(warnings) == [1] and warnings[1][0].startswith("politeness_speech_to")


def test_narration_is_ignored():
    assert speech_level_warnings([_line(1, "", "彼は笑いました。", "그는 웃었다.")]) == {}


def test_engine_review_includes_politeness_warning(tmp_path):
    import asyncio
    import json

    from GalTransl.Loader import load_transList
    from ollama_mock import mock_ollama
    from test_ollama_ko import batch, config, engine

    def translate(payload):
        body = json.loads(payload["messages"][-1]["content"])
        return {"translations": [{"id": l["id"], "text": "진로 희망서 가져왔어."} for l in body["input"]]}

    seen = []

    def review(payload):
        body = json.loads(payload["messages"][-1]["content"])
        seen.extend(body["items"])
        return {"reviews": [{"id": i["id"], "changed": True, "text": "진로 희망서 가져왔습니다.", "reason": "존댓말"}
                            for i in body["items"]]}

    source = load_transList([{"name": "湊", "message": "進路希望の紙を持ってきました。"}])[0]
    with mock_ollama([translate, review]) as (url, _calls):
        async def run():
            e = engine(config(tmp_path, url, followingContext=0, reviewWarnings=True))
            try:
                await batch(e, source, tmp_path, size=1)
            finally:
                await e.shutdown()
        asyncio.run(run())
    assert any(w.startswith("politeness_mismatch") for w in seen[0]["warnings"])
    assert source[0].post_dst == "진로 희망서 가져왔습니다." and source[0].pre_dst == "진로 희망서 가져왔어."


def test_quality_report_lists_politeness_warning(tmp_path):
    import json

    from GalTransl.OllamaKoTools import build_report

    (tmp_path / "gt_input").mkdir()
    (tmp_path / "transl_cache").mkdir()
    (tmp_path / "config.yaml").write_text("plugin:\n  filePlugin: file_vn_scene_txt\n", encoding="utf-8")
    (tmp_path / "gt_input" / "a.txt").write_text(
        "*s1\n【湊】「進路希望の紙を持ってきました。」\n", encoding="utf-8")
    (tmp_path / "transl_cache" / "a.txt.json").write_text(json.dumps([
        {"index": 2, "name": "湊", "pre_src": "進路希望の紙を持ってきました。",
         "post_src": "進路希望の紙を持ってきました。", "pre_dst": "진로 희망서 가져왔어."}], ensure_ascii=False),
        encoding="utf-8")
    report = build_report(tmp_path)
    assert any(i["code"].startswith("politeness_mismatch") and i["index"] == 2 for i in report["issues"])
