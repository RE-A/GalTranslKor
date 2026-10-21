"""Q7: 한국어 대상 경고 보강 — 숫자 누락, 사전 적용 검사의 띄어쓰기 허용(합성 문장)."""
from types import SimpleNamespace

from GalTransl.CSentense import CSentense
from GalTransl.Dictionary import CGptDict
from tests.test_problem_common_korean import DEFAULTS, check, pc


def test_number_type_is_enabled_by_default():
    assert "数字不符" in DEFAULTS


def test_missing_source_number_is_flagged_for_korean():
    assert any(p.startswith("数字不符") for p in check("３人で10時に会おう。", "셋이서 열 시에 만나자."))
    assert not any(p.startswith("数字不符") for p in check("３人で10時に会おう。", "3명이서 10시에 만나자."))
    # 원문에 아라비아 숫자가 없으면 번역에서 숫자로 바꿔도 정상
    assert not any(p.startswith("数字不符") for p in check("三人で会おう。", "3명이서 만나자."))


def test_numbers_inside_control_codes_are_ignored():
    assert not any(p.startswith("数字不符") for p in check("%02dです[wait=20]", "%02d입니다[wait=20]"))
    assert not any(p.startswith("数字不符") for p in check("{name2}は来た。", "{name2}이 왔다."))


def test_number_check_is_korean_only():
    assert not any(p.startswith("数字不符") for p in check("10時だ。", "十点了。", target="zh-cn"))


def _dic(lines):
    gd = CGptDict.__new__(CGptDict)
    gd._dic_list = [SimpleNamespace(search_word=s, replace_word=r, note="", dic_name="GPT 사전") for s, r in lines]
    return gd


def _tran(src, dst):
    tran = CSentense(src, "", 1)
    tran.post_src = src
    tran.pre_dst = tran.post_dst = dst
    return tran


def test_dictionary_check_ignores_korean_spacing():
    gd = _dic([("白鷺ユイ", "시라사기 유이")])
    tran = _tran("白鷺ユイです。", "시라사기유이입니다.")
    assert gd.check_dic_use(tran.pre_dst, tran) != ""
    assert gd.check_dic_use(tran.pre_dst, tran, ignore_spaces=True) == ""
    assert gd.check_dic_use("유이입니다.", tran, ignore_spaces=True) != ""


def test_problem_common_uses_spacing_tolerant_dictionary_check_for_korean():
    gd = _dic([("白鷺ユイ", "시라사기 유이")])
    tran = _tran("白鷺ユイです。", "시라사기유이입니다.")
    from tests.test_problem_common_korean import Cfg
    assert not any("미사용" in p for p in pc._check_problems(tran, Cfg("ko"), gd))
    assert any("미사용" in p for p in pc._check_problems(tran, Cfg("zh-cn"), gd))
