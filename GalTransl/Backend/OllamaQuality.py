"""Japanese-to-Korean output checks shared by the Ollama-ko engine and report tool.

These are structural/heuristic checks, not a measure of literary quality.
Fatal problems reject a model response (and are retried); warnings only appear
in the quality report so that legitimate translations are never discarded for
a mere length difference or an intentional foreign word.
"""
from __future__ import annotations

from collections import Counter
import re

MARKERS = re.compile(
    r"\{[^{}\r\n]+\}|%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[sdfiuoxX]|"
    r"\[[^\[\]\r\n]+\]|</?[^<>\r\n]+>|\\(?:[A-Za-z]+(?:\[[^\]\r\n]*\])?|.)"
)
KANA = re.compile(r"[ぁ-ゖァ-ヺｦ-ﾝ]")
HANGUL = re.compile(r"[가-힣ㄱ-ㆎ]")
HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
JAPANESE = re.compile(r"[ぁ-ヺ一-鿿]")
LETTER = re.compile(r"[\w]", re.UNICODE)
FAILED_PREFIX = "(Failed)"

# (pattern in translation, pattern that legitimately explains it in the source)
_REFUSALS = [
    (re.compile(r"번역(할|해 ?드릴|을 제공할|이 불가능)|번역을 거부"), re.compile(r"翻訳|訳")),
    (re.compile(r"(AI|인공지능) ?(언어 ?)?모델|언어 모델로서"), re.compile(r"AI|言語モデル|人工知能")),
    (re.compile(r"콘텐츠 ?정책|가이드라인에 (따라|위배)|부적절한 (내용|콘텐츠|요청)"),
     re.compile(r"ポリシー|ガイドライン|不適切")),
    (re.compile(r"도와드릴 수 없|제공할 수 없습니다"), re.compile(r"手伝|助け|提供")),
    (re.compile(r"(?i)\b(i'?m sorry|i am sorry|i cannot|i can'?t|as an ai|language model)\b"),
     re.compile(r"(?i)sorry|cannot|can'?t|\bai\b|language")),
    (re.compile(r"[(\[]\s*(번역\s*)?(생략|검열|삭제)(됨)?\s*[)\]]"), None),
]


def _letters(text: str) -> int:
    return len(LETTER.findall(MARKERS.sub("", text)))


def _strip_allowed(text: str, allow) -> str:
    for word in allow:
        if word:
            text = text.replace(word, "")
    return text


def fatal_problems(source: str, text, *, allow=(), speakers=(), min_ratio=0.2) -> list[str]:
    """Problems that make a translation unusable. Empty list means acceptable."""
    if not isinstance(text, str):
        return ["empty/non-string translation"]
    if source.strip() and not text.strip():
        return ["empty/non-string translation"]
    if text.startswith(FAILED_PREFIX):
        return ["translation failed"]
    problems = []
    if Counter(MARKERS.findall(source)) != Counter(MARKERS.findall(text)):
        problems.append("placeholder/control marker mismatch")
    if re.findall(r"\r\n|\r|\n", source) != re.findall(r"\r\n|\r|\n", text):
        problems.append("line break mismatch")
    if any(source.count(q) != text.count(q) for q in "「」『』"):
        problems.append("dialogue bracket mismatch")
    plain_source = MARKERS.sub("", source)
    plain_text = _strip_allowed(MARKERS.sub("", text), allow)
    if KANA.search(plain_text):
        problems.append("Japanese kana remains")
    if JAPANESE.search(_strip_allowed(plain_source, allow)) and not HANGUL.search(plain_text):
        problems.append("Korean translation required")
    new_han = [c for c in HAN.findall(plain_text) if c not in plain_source]
    if new_han and len(new_han) > len(HANGUL.findall(plain_text)):
        problems.append("Chinese output suspected")
    stripped = text.strip()
    if stripped.startswith("```") or "<think>" in text:
        problems.append("model commentary is not a translation")
    for pattern, explained_by in _REFUSALS:
        if pattern.search(text) and not (explained_by and explained_by.search(source)):
            problems.append("refusal/notice text instead of translation")
            break
    for name in speakers:
        if name and not source.lstrip().startswith(name) and re.match(
                rf"\s*[【\[]?{re.escape(name)}[】\]]?\s*[:：]", text):
            problems.append("speaker name prefix added")
            break
    src_len = _letters(source)
    if min_ratio and src_len >= 12 and _letters(text) < src_len * min_ratio:
        problems.append("translation much shorter than source (omission suspected)")
    return problems


def warning_problems(source: str, text: str, *, allow=()) -> list[str]:
    """Suspicious but possibly legitimate results, for human review only."""
    warnings = []
    plain_text = _strip_allowed(MARKERS.sub("", text), allow)
    new_han = [c for c in HAN.findall(plain_text) if c not in source]
    if new_han:
        warnings.append("Han characters not present in source: " + "".join(dict.fromkeys(new_han)))
    src_len, dst_len = _letters(source), _letters(text)
    if src_len >= 8 and dst_len < src_len * 0.45:
        warnings.append(f"short translation ({dst_len}/{src_len} letters)")
    if src_len >= 4 and dst_len > src_len * 3 + 10:
        warnings.append(f"long translation ({dst_len}/{src_len} letters)")
    return warnings


def validate_translation(source: str, text, **options) -> None:
    problems = fatal_problems(source, text, **options)
    if problems:
        raise ValueError("; ".join(problems))
