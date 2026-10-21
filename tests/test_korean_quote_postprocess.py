"""Shared post-processing must keep ASCII quotes in Korean translations."""
from GalTransl.Backend.BaseTranslate import BaseTranslate
from GalTransl.CSentense import CSentense


class Engine(BaseTranslate):
    def __init__(self, target_lang):
        self.target_lang = target_lang


def normalize(target, src, dst):
    tran = CSentense(src, "", 1)
    tran.post_src = src
    return Engine(target)._normalize_parsed_translation_text(dst, tran, "")


def test_korean_keeps_ascii_quotes():
    assert normalize("Korean", "彼は「行こう」と言った。", '그는 "가자"라고 말했다.') == '그는 "가자"라고 말했다.'


def test_non_korean_behaviour_is_unchanged():
    assert normalize("English", "彼は「行こう」と言った。", 'He said "let\'s go".') == "He said let's go."
