"""한국어 조사 교정: 치환·용어집 단어 뒤 조사를 받침에 맞춤(합성 문장)."""
from types import SimpleNamespace

from GalTransl.KoreanText import fix_josa, has_batchim


def test_batchim():
    assert has_batchim("준") and not has_batchim("유이") and has_batchim("서울")
    assert has_batchim("하루카") is False and has_batchim("A") is None


def test_basic_pairs_after_known_words():
    assert fix_josa("준는 웃었다.", ["준"]) == "준은 웃었다."
    assert fix_josa("유이을 불렀다. 유이이 왔다.", ["유이"]) == "유이를 불렀다. 유이가 왔다."
    assert fix_josa("준와 유이과 함께.", ["준", "유이"]) == "준과 유이와 함께."
    assert fix_josa("준야, 유이아!", ["준", "유이"]) == "준아, 유이야!"
    assert fix_josa("준랑 놀았다.", ["준"]) == "준이랑 놀았다."
    assert fix_josa("유이예요. 준예요.", ["유이", "준"]) == "유이예요. 준이에요."


def test_euro_and_rieul():
    assert fix_josa("준로 정했다. 서울으로 간다. 유이으로는 안 돼.", ["준", "서울", "유이"]) == \
        "준으로 정했다. 서울로 간다. 유이로는 안 돼."


def test_does_not_touch_words_or_unknown_names():
    # 뒤가 다른 단어로 이어지거나(이번), 목록에 없는 단어는 건드리지 않음
    assert fix_josa("준 이번에 왔다.", ["준"]) == "준 이번에 왔다."
    assert fix_josa("준가방을 들었다.", ["준"]) == "준가방을 들었다."
    assert fix_josa("민수는 왔다.", ["준"]) == "민수는 왔다."
    assert fix_josa("Sakura는 왔다.", ["Sakura"]) == "Sakura는 왔다."
    # 더 긴 단어의 일부인 경우(준비)는 건드리지 않음
    assert fix_josa("준비는 끝났다.", ["준"]) == "준비는 끝났다."


def test_postprocess_applies_post_dict_and_glossary_for_korean():
    from GalTransl.CSentense import CSentense
    from GalTransl.Dictionary import CNormalDic
    from GalTransl.Frontend.LLMTranslate import postprocess_trans_list

    post = CNormalDic([])
    post.dic_list = [SimpleNamespace(is_situationsDic=False, is_conditionaDic=False, startswith_flag=False,
                                     onetime_flag=False, search_word="미나토", replace_word="준")]
    gpt = SimpleNamespace(_dic_list=[SimpleNamespace(replace_word="유이")])

    def run(target):
        tran = CSentense("湊は結衣を呼んだ。", "", 1)
        tran.post_dst = "미나토는 유이을 불렀다."
        cfg = SimpleNamespace(target_lang=target, gpt_dic=gpt)
        postprocess_trans_list([tran], cfg, post)
        return tran.post_dst

    assert run("ko") == "준은 유이를 불렀다."
    assert run("zh-cn") == "준는 유이을 불렀다."  # 다른 대상 언어는 그대로
