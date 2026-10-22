"""Korean text helpers that need no morphological analyzer."""
from __future__ import annotations

import re
from typing import Iterable, Optional

# (form after a final consonant, form after a vowel), longest first.
_PAIRS = [
    ("이라고", "라고"), ("이라는", "라는"), ("이라서", "라서"), ("이에요", "예요"),
    ("이랑", "랑"), ("이나", "나"), ("이며", "며"), ("이여", "여"), ("이야", "야"),
    ("은", "는"), ("이", "가"), ("을", "를"), ("과", "와"), ("아", "야"),
]
_FORMS = sorted({f for pair in _PAIRS for f in pair}, key=len, reverse=True)
_HANGUL = re.compile(r"[가-힣]")
# (으)로 may carry a following particle: 로는, 로도, 로서, 로써, 로부터, 로만, 로의
_RO = re.compile(r"(으로|로)(?=(?:는|도|서|써|부터|만|의)?(?![가-힣]))")


def has_batchim(word: str) -> Optional[bool]:
    """Whether the last syllable has a final consonant; None if it is not Hangul."""
    if not word or not "가" <= word[-1] <= "힣":
        return None
    return (ord(word[-1]) - 0xAC00) % 28 != 0


def _rieul(word: str) -> bool:
    return (ord(word[-1]) - 0xAC00) % 28 == 8


def _fix_at(text: str, end: int, word: str) -> str:
    batchim = has_batchim(word)
    if batchim is None:
        return text
    rest = text[end:]
    ro = _RO.match(rest)
    if ro:
        want = "으로" if batchim and not _rieul(word) else "로"
        return text[:end] + want + rest[ro.end(1):]
    for form in _FORMS:
        if rest.startswith(form) and not _HANGUL.match(rest[len(form):len(form) + 1]):
            pair = next(p for p in _PAIRS if form in p)
            if form == "야" and rest[1:2] in (",", "、", "，"):
                pair = ("아", "야")  # vocative (준아, 유이야) rather than copula (준이야)
            want = pair[0] if batchim else pair[1]
            return text[:end] + want + rest[len(form):]
    return text


def fix_josa(text: str, words: Iterable[str]) -> str:
    """Correct the particle right after each listed word (e.g. names substituted by a
    post-translation dictionary). Occurrences inside longer words are left alone."""
    for word in sorted({w for w in words if w and has_batchim(w) is not None}, key=len, reverse=True):
        start = 0
        while (pos := text.find(word, start)) != -1:
            end = pos + len(word)
            before_ok = pos == 0 or not _HANGUL.match(text[pos - 1])
            if before_ok:
                text = _fix_at(text, end, word)
            start = end
    return text
