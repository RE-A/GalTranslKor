"""한국어 대상에서 중국어 전용 모델(Sakura/GalTransl) 선택 시 경고."""

from GalTransl.Runner import chinese_only_model_warning


def test_korean_target_with_sakura_warns():
    for translator in ("sakura-v1.0", "galtransl-v3"):
        msg = chinese_only_model_warning(translator, "ja2ko")
        assert msg and "중국어" in msg and translator in msg


def test_other_cases_do_not_warn():
    assert chinese_only_model_warning("sakura-v1.0", "ja2zh-cn") is None
    assert chinese_only_model_warning("ForGal-json", "ja2ko") is None
    assert chinese_only_model_warning("galtransl-v3", "") is None
