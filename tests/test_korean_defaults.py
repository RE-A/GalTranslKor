"""Korean is the default backend message language of this fork."""
import os
from pathlib import Path
import subprocess
import sys

from GalTransl import i18n

ROOT = Path(__file__).resolve().parents[1]


def test_backend_messages_default_to_korean_without_gt_lang():
    env = {k: v for k, v in os.environ.items() if k != "GT_LANG"}
    code = "from GalTransl.i18n import GT_LANG, get_text; print(GT_LANG); print(get_text('goodbye'))"
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["ko", "종료합니다."]


def test_every_backend_message_has_korean_with_same_placeholders():
    import re
    for key, texts in i18n.UI_TEXT.items():
        assert texts.get("ko", "").strip(), key
        fields = lambda text: sorted(re.findall(r"\{[^{}]*\}", text))
        assert fields(texts["ko"]) == fields(texts["en"]), key


def test_messages_missing_korean_fall_back_to_english():
    i18n.UI_TEXT["_test_only"] = {"zh-cn": "中文", "en": "English"}
    try:
        assert i18n.get_text("_test_only", "ko") == "English"
    finally:
        del i18n.UI_TEXT["_test_only"]


def test_translation_template_descriptions_follow_backend_language():
    from GalTransl import TRANSLATOR_SUPPORTED
    assert all(texts.get("ko", "").strip() for texts in TRANSLATOR_SUPPORTED.values())
    env = {k: v for k, v in os.environ.items() if k != "GT_LANG"}
    code = ("from GalTransl import TRANSLATOR_SUPPORTED as T; from GalTransl.server import _translator_description as d;"
            "print(d(T['ForNovel']))")
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "소설 번역용 템플릿."
