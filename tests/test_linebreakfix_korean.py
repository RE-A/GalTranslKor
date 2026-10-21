"""text_common_lineBreakFix must place breaks between Korean words, not only at the end."""
import importlib.util
from pathlib import Path

import pytest
import yaml

from GalTransl.CSentense import CSentense

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/text_common_lineBreakFix"
spec = importlib.util.spec_from_file_location("linebreak_ko", PLUGIN / "text_common_lineBreakFix.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Plugin = next(c for c in vars(module).values() if isinstance(c, type) and c.__module__ == module.__name__)

SOURCE = "放課後の教室には、[r]もう誰も残っていなかった。"
KOREAN = "방과 후 교실에는 이미 아무도 남아 있지 않았다."


def fix(mode, src=SOURCE, dst=KOREAN):
    conf = yaml.safe_load((PLUGIN / "text_common_lineBreakFix.yaml").read_text(encoding="utf-8"))
    conf["Settings"].update({"换行符": "[r]", "换行模式": mode})
    plugin = Plugin()
    plugin.gtp_init(conf, {})
    tran = CSentense(src, "", 1)
    tran.post_src = src
    tran.pre_dst = tran.post_dst = dst
    return plugin.after_dst_processed(tran).post_dst


@pytest.mark.parametrize("mode", ["保持位置", "平均", "切最长"])
def test_korean_breaks_fall_between_words(mode):
    result = fix(mode)
    assert result.count("[r]") == 1
    assert not result.endswith("[r]") and not result.startswith("[r]")
    assert result.replace("[r]", "") == KOREAN
    before, after = result.split("[r]")
    assert before.endswith(" ") or after.startswith(" ") or before[-1] in ".," , result


def test_chinese_text_still_uses_budoux():
    result = fix("保持位置", dst="放学后的教室里，已经没有任何人留下了。")
    assert result.count("[r]") == 1 and not result.endswith("[r]")
