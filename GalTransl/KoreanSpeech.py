"""Korean speech-level (존댓말/반말) checks for dialogue, using the optional Kiwi analyzer.

Warnings only: a polite Japanese line rendered in 반말, a line whose level differs from
the same speaker's other lines of the same source level in the scene, or a line that
contradicts the character file's speech_to rule for the addressee named in the line.
Without kiwipiepy installed every check returns nothing.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import re
from typing import Optional

from GalTransl import LOGGER

_kiwi = None
_kiwi_failed = False

_JA_END = re.compile(r"[。．！？!?…‥]+")
_JA_TRAIL = re.compile(r"[、。．！？!?…‥ー〜～」』）)\s♪☆★]+$")
_JA_POLITE = re.compile(r"(です|ます|ました|ません|ましょう|でした|でしょう|ください|下さい|ございます|ございました|まし|ませ)"
                        r"(?:か|よ|ね|な|わ|の|って|けど|から|が)*$")
_KO_SPLIT = re.compile(r"(?<=[.!?…~])\s+|\n")
_POLITE_ENDINGS = ("요", "죠", "습니다", "ᆸ니다", "습니까", "ᆸ니까", "시오", "세요", "ᆸ시다")


def get_kiwi():
    global _kiwi, _kiwi_failed
    if _kiwi is None and not _kiwi_failed:
        try:
            from kiwipiepy import Kiwi
            _kiwi = Kiwi()
        except Exception as exc:  # optional dependency
            _kiwi_failed = True
            LOGGER.info("kiwipiepy를 쓸 수 없어 존댓말·반말 검사를 건너뜁니다: %s", exc)
    return _kiwi


def ja_politeness(text: str) -> Optional[str]:
    """'polite' if any sentence ends in です/ます style, 'plain' if it ends in a kana
    predicate, None for noun-only lines."""
    found = None
    for sentence in _JA_END.split(text):
        body = _JA_TRAIL.sub("", sentence.strip().lstrip("「『（("))
        if not body:
            continue
        if _JA_POLITE.search(body):
            return "polite"
        if re.match(r"[ぁ-ゖ]", body[-1]):
            found = "plain"
    return found


def _sentence_level(tokens) -> Optional[str]:
    tail = [t for t in tokens if not t.tag.startswith("S")]
    if not tail:
        return None
    last = tail[-1]
    if last.tag == "JX" and last.form in ("요", "이요"):
        return "polite"
    endings = [t for t in tail if t.tag in ("EF", "EC")]
    if not endings or last.tag not in ("EF", "EC", "VCP", "XSV", "XSA", "VX"):
        # Noun-only sentence ("사에키 선생님.") carries no speech level.
        return "plain" if last.tag == "EF" else None
    form = endings[-1].form
    return "polite" if form.endswith(_POLITE_ENDINGS) else "plain"


def ko_politeness(text: str) -> Optional[str]:
    kiwi = get_kiwi()
    if kiwi is None:
        return None
    levels = set()
    for sentence in _KO_SPLIT.split(text):
        # A trailing vocative ("늦었잖아, 미나토.") does not decide the level.
        parts = [p for p in re.split(r"[,，、]\s*", sentence) if p.strip()]
        for part in reversed(parts):
            level = _sentence_level(kiwi.tokenize(part))
            if level:
                levels.add(level)
                break
    return levels.pop() if len(levels) == 1 else None


def _is_dialogue(line: dict) -> bool:
    return bool(line.get("speaker")) or line.get("source", "").lstrip().startswith("「")


def _expected(rule: str) -> Optional[str]:
    if "존댓말" in rule or "존대" in rule:
        return "polite"
    if "반말" in rule:
        return "plain"
    return None


def speech_level_warnings(lines: list[dict], profiles: list[dict] = (), names: dict = None) -> dict:
    """lines: dicts with index, speaker, source, translation, scene_break (file order).
    profiles: character profiles (ja, speech_to); names: ja name -> all names/aliases.
    Returns {index: [warning, ...]}."""
    if get_kiwi() is None:
        return {}
    names = names or {}
    speech_to = {p["ja"]: p.get("speech_to") or {} for p in profiles}
    warnings: dict = defaultdict(list)
    scene = 0
    groups: dict = defaultdict(list)
    for line in lines:
        if line.get("scene_break"):
            scene += 1
        text = line.get("translation") or ""
        if not _is_dialogue(line) or not text.strip():
            continue
        ja, ko = ja_politeness(line["source"]), ko_politeness(text)
        if ko is None:
            continue
        if ja == "polite" and ko == "plain":
            warnings[line["index"]].append("politeness_mismatch: 원문 존댓말, 번역 반말")
        rules = speech_to.get(line.get("speaker"), {})
        addressed = [k for k in rules if any(n in line["source"] for n in names.get(k, [k]))]
        if len(addressed) == 1 and (want := _expected(rules[addressed[0]])) and want != ko:
            label = {"polite": "존댓말", "plain": "반말"}
            warnings[line["index"]].append(
                f"politeness_speech_to: {addressed[0]}에게 {label[want]} 규칙, 번역 {label[ko]}")
        if ja:
            groups[(scene, line.get("speaker", ""), ja)].append((line["index"], ko))
    for members in groups.values():
        if len(members) < 3:
            continue
        level, count = Counter(ko for _, ko in members).most_common(1)[0]
        if count * 4 < len(members) * 3:
            continue  # no clear habit in this scene
        for index, ko in members:
            if ko != level and not any(w.startswith("politeness_") for w in warnings[index]):
                warnings[index].append("politeness_inconsistent: 같은 장면의 같은 화자와 말투가 다름")
    return {k: v for k, v in warnings.items() if v}
