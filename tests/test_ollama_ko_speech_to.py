"""Q2: 캐릭터 사전의 상대별 말투(speech_to) — 등장한 상대의 규칙만 전달(합성 인물)."""
from pathlib import Path

import pytest

from GalTransl.Backend.OllamaPrompts import (
    SPEECH_TO_CONTRACT, build_system_prompt, load_characters, select_characters,
)

YAML = """characters:
  - ja: 湊
    ko: 미나토
    speech: 무뚝뚝한 반말
    speech_to:
      葵: 반말, "아오이"라고 부름
      先生: 존댓말, "선생님"이라고 부름
      春香: 존댓말, "하루카 선배"라고 부름
  - ja: 葵
    ko: 아오이
    aliases: [葵さん]
  - ja: 先生
    ko: 선생님
  - ja: 春香
    ko: 하루카
"""


def _chars(tmp_path, text=YAML):
    path = tmp_path / "characters.yaml"
    path.write_text(text, encoding="utf-8")
    return load_characters(path)


def test_speech_to_only_lists_addressees_in_the_request(tmp_path):
    chars = _chars(tmp_path)
    profiles = select_characters(chars, ["湊", "葵"], ["「葵さん、待ってた。」"])
    minato = next(p for p in profiles if p["ja"] == "湊")
    assert minato["speech_to"] == {"葵": '반말, "아오이"라고 부름'}
    # 상대가 아무도 없으면 speech_to 자체를 보내지 않음
    alone = select_characters(chars, ["湊"], ["独り言だ。"])
    assert "speech_to" not in alone[0]
    assert alone[0]["speech"] == "무뚝뚝한 반말"


def test_alias_mention_selects_addressee(tmp_path):
    profiles = select_characters(_chars(tmp_path), ["湊"], ["葵さんはまだ？"])
    assert list(next(p for p in profiles if p["ja"] == "湊")["speech_to"]) == ["葵"]


def test_invalid_speech_to_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="speech_to"):
        _chars(tmp_path, "characters:\n  - ja: 湊\n    speech_to: [葵]\n")


def test_contract_text_only_when_used():
    assert build_system_prompt("지침") == build_system_prompt("지침", speech_to=False)
    assert SPEECH_TO_CONTRACT not in build_system_prompt("지침")
    assert SPEECH_TO_CONTRACT in build_system_prompt("지침", speech_to=True)


def test_engine_sends_speech_to_and_contract(tmp_path):
    import json

    from ollama_mock import mock_ollama
    from test_ollama_ko_integration import project, run

    with mock_ollama() as (url, calls):
        project(tmp_path, url, 4)  # 화자 葵, 문장에 다른 인물 없음
        (tmp_path / "characters.yaml").write_text(
            "characters:\n  - ja: 葵\n    ko: 아오이\n    speech_to:\n      湊: 반말\n      先生: 존댓말\n"
            "  - ja: 湊\n    ko: 미나토\n", encoding="utf-8")
        run(tmp_path)
    request = calls[0][1]
    system = request["messages"][0]["content"]
    body = json.loads(request["messages"][1]["content"])
    assert SPEECH_TO_CONTRACT in system
    aoi = next(c for c in body["characters"] if c["ja"] == "葵")
    assert "speech_to" not in aoi  # 湊·先生이 이 요청에 없음
