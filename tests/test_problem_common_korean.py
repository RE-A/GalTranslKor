"""problem_common must not flag normal Korean translations as problems."""
import importlib.util
from pathlib import Path

from GalTransl.CSentense import CSentense

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("problem_common_ko", ROOT / "plugins/problem_common/problem_common.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)
DEFAULTS = [m.name for m in pc.CProblemType if m.default_enabled]


class Cfg:
    def __init__(self, target, problems=DEFAULTS):
        self.target_lang, self.problems = target, problems

    def getProblemAnalyzeArinashiDict(self):
        return {}

    def getProblemAnalyzeConfig(self, key):
        return self.problems

    def getlbSymbol(self):
        return "auto"


def check(src, dst, target="ko", problems=DEFAULTS):
    tran = CSentense(src, "", 1)
    tran.post_src = src
    tran.pre_dst = tran.post_dst = dst
    return pc._check_problems(tran, Cfg(target, problems))


def test_normal_korean_translations_have_no_problems():
    for src, dst in [
        ("雨の駅で、彼女を待っていた。", "비 오는 역에서 그녀를 기다리고 있었다."),
        ("時間：午後三時", "시간: 오후 세 시"),
        ("彼は笑った。", "그는 웃었다."),
        ("放課後の教室には、もう誰も残っていなかった。", "방과 후 교실에는 이미 아무도 남아 있지 않았다."),
        ("（やっぱり、覚えていてくれたんだ。）", "(역시 기억하고 있었구나.)"),
    ]:
        assert check(src, dst) == [], (src, dst)


def test_korean_checks_still_find_real_problems():
    assert any(p.startswith("残留日文") for p in check("おはよう。", "おはよう 좋은 아침."))
    assert any(p.startswith("比日文长") for p in check("雨だ。", "비가 내리고 있다. 아주 많이 내리고 있어서 우산이 필요하다."))
    assert any(p.startswith("语言不通") for p in check("今日は雨が降っている。", "今天在下雨。"))
    assert "本有冒号" in check("時間：午後三時", "시간 오후 세 시")


def test_chinese_target_behaviour_is_unchanged():
    assert "本无韩文" in check("彼は笑った。", "他笑了。그", target="zh-cn")
    assert "本有冒号" in check("時間：午後三時", "时间:下午三点", target="zh-cn")
