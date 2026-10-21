"""Blind A/B scoring sheets for the synthetic Korean quality set (examples/ollama_ko_eval).

The evaluation set holds scene TXT files plus items.yaml (what each line must keep,
acceptable and forbidden renderings). `make_sheet` reads translations from one or two
translated copies of the set, hides which system produced which column and writes a
CSV for a human rater. `summarize` joins the filled sheet with the hidden key.
Nothing here calls a model or judges quality by itself.
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

import yaml

from GalTransl.OllamaKoTools import _read_cache, _scene_plugin

AXES = ("meaning", "fluency", "voice", "terms")
AXIS_LABELS = {"meaning": "의미 정확성", "fluency": "한국어 자연스러움", "voice": "말투·관계", "terms": "용어 일관성"}
CRITICAL = {"omission": "누락", "addition": "추가", "actor": "행위자 반전", "negation": "부정 반전",
            "number": "숫자", "control": "제어코드 손상", "name": "이름·호칭"}
SPLITS = ("dev", "test")


def load_items(eval_dir: Path) -> list[dict]:
    data = yaml.safe_load((Path(eval_dir) / "items.yaml").read_text(encoding="utf-8")) or {}
    return data.get("items") or []


def _scenes(eval_dir: Path) -> dict[str, list[dict]]:
    plugin = _scene_plugin({})[1]
    return {p.name: plugin.load_file(str(p)) for p in sorted((Path(eval_dir) / "gt_input").glob("*.txt"))}


def validate(eval_dir: Path) -> list[str]:
    """Every translatable scene line needs exactly one item and every item one line."""
    errors = []
    items = load_items(eval_dir)
    scenes = _scenes(eval_dir)
    lines = {(f, e["index"]) for f, entries in scenes.items() for e in entries if e.get("message", "").strip()}
    seen_ids, seen_lines = set(), set()
    for item in items:
        key = (item.get("file"), item.get("line"))
        if item.get("id") in seen_ids:
            errors.append(f"{item.get('id')}: duplicate id")
        if key in seen_lines:
            errors.append(f"{item.get('id')}: duplicate line {key}")
        seen_ids.add(item.get("id"))
        seen_lines.add(key)
        if key not in lines:
            errors.append(f"{item.get('id')}: {key} is not a translatable line")
        if item.get("split") not in SPLITS:
            errors.append(f"{item.get('id')}: split must be dev or test")
        if not str(item.get("meaning", "")).strip():
            errors.append(f"{item.get('id')}: meaning is required")
    for key in sorted(lines - seen_lines):
        errors.append(f"{key}: line has no item")
    return errors


def _line_text(entry: dict) -> str:
    speaker = entry.get("name") or ""
    return f"{speaker}: {entry['message']}" if speaker else entry["message"]


def make_sheet(eval_dir: Path, systems: dict[str, Path], out_csv: Path, *, split: str = "test",
               seed: int = 0, context_lines: int = 2) -> Path:
    """Write the rating CSV and `<out>.key.json` (which system is T1/T2 per item)."""
    if not 1 <= len(systems) <= 2:
        raise ValueError("compare one or two systems")
    scenes = _scenes(eval_dir)
    caches = {label: {} for label in systems}
    rng = random.Random(seed)
    rows, key = [], {}
    columns = [f"T{n}" for n in range(1, len(systems) + 1)]
    for item in load_items(eval_dir):
        if split != "all" and item["split"] != split:
            continue
        entries = [e for e in scenes[item["file"]] if e.get("message", "").strip()]
        position = next(i for i, e in enumerate(entries) if e["index"] == item["line"])
        context = " / ".join(_line_text(e) for e in entries[max(0, position - context_lines):position])
        labels = list(systems)
        rng.shuffle(labels)
        key[item["id"]] = labels
        row = {"id": item["id"], "split": item["split"], "tags": ",".join(item.get("tags", [])),
               "context": context, "source": _line_text(entries[position]), "meaning": item["meaning"],
               "acceptable": " | ".join(item.get("acceptable", [])),
               "forbidden": " | ".join(f"{f['text']} ({f['reason']})" for f in item.get("forbidden", []))}
        for column, label in zip(columns, labels):
            cache = caches[label].setdefault(
                item["file"], _read_cache(Path(systems[label]) / "transl_cache", item["file"]))
            record = cache.get(item["line"]) or {}
            row[column] = record.get("proofread_dst") or record.get("pre_dst") or ""
        for column in columns:
            for axis in AXES:
                row[f"{column}_{axis}"] = ""
            row[f"{column}_critical"] = ""
        row["preference"] = ""
        row["comment"] = ""
        rows.append(row)
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["id"])
        writer.writeheader()
        writer.writerows(rows)
    Path(f"{out_csv}.key.json").write_text(
        json.dumps({"systems": list(systems), "columns": columns, "items": key}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return out_csv


def summarize(sheet_csv: Path) -> dict:
    """Aggregate a filled sheet per system; critical errors are counted, not averaged away."""
    key = json.loads(Path(f"{sheet_csv}.key.json").read_text(encoding="utf-8"))
    with Path(sheet_csv).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    result = {label: {"scored": 0, "sums": dict.fromkeys(AXES, 0), "critical": dict.fromkeys(CRITICAL, 0),
                      "preferred": 0, "tags": {}} for label in key["systems"]}
    ties, errors = 0, []
    for row in rows:
        labels = key["items"].get(row["id"])
        if labels is None:
            errors.append(f"{row['id']}: not in key")
            continue
        for column, label in zip(key["columns"], labels):
            scores = {}
            for axis in AXES:
                value = (row.get(f"{column}_{axis}") or "").strip()
                if value:
                    if value not in ("0", "1", "2", "3", "4"):
                        errors.append(f"{row['id']} {column}_{axis}: score must be 0-4")
                        continue
                    scores[axis] = int(value)
            stats = result[label]
            if len(scores) == len(AXES):
                stats["scored"] += 1
                for axis, value in scores.items():
                    stats["sums"][axis] += value
                for tag in filter(None, row.get("tags", "").split(",")):
                    tag_stats = stats["tags"].setdefault(tag, [0, 0])
                    tag_stats[0] += scores["meaning"]
                    tag_stats[1] += 1
            elif scores:
                errors.append(f"{row['id']} {column}: incomplete scores")
            for code in filter(None, (c.strip() for c in (row.get(f"{column}_critical") or "").split(","))):
                if code in CRITICAL:
                    stats["critical"][code] += 1
                else:
                    errors.append(f"{row['id']} {column}_critical: unknown code {code}")
        preference = (row.get("preference") or "").strip().lower()
        if preference == "tie":
            ties += 1
        elif preference.upper() in key["columns"]:
            result[labels[key["columns"].index(preference.upper())]]["preferred"] += 1
        elif preference:
            errors.append(f"{row['id']}: preference must be {'/'.join(key['columns'])}/tie")
    for stats in result.values():
        n = stats["scored"]
        stats["means"] = {axis: round(stats["sums"][axis] / n, 2) if n else None for axis in AXES}
        stats["tag_meaning"] = {tag: round(s / c, 2) for tag, (s, c) in sorted(stats.pop("tags").items())}
        del stats["sums"]
    return {"items": len(rows), "systems": result, "ties": ties, "errors": errors}


def summary_markdown(summary: dict) -> str:
    systems = summary["systems"]
    lines = ["# 한국어 번역 품질 평가 집계", "",
             f"- 항목 {summary['items']}개, 동률 {summary['ties']}건, 입력 오류 {len(summary['errors'])}건", "",
             "| 시스템 | 채점 항목 | " + " | ".join(AXIS_LABELS[a] for a in AXES) + " | 선호 |",
             "| --- | --- | " + " | ".join("---" for _ in AXES) + " | --- |"]
    for label, s in systems.items():
        lines.append(f"| {label} | {s['scored']} | " + " | ".join(str(s["means"][a]) for a in AXES) + f" | {s['preferred']} |")
    lines += ["", "## 중대 오류 건수", "", "| 시스템 | " + " | ".join(CRITICAL.values()) + " |",
              "| --- | " + " | ".join("---" for _ in CRITICAL) + " |"]
    for label, s in systems.items():
        lines.append(f"| {label} | " + " | ".join(str(s["critical"][c]) for c in CRITICAL) + " |")
    if summary["errors"]:
        lines += ["", "## 입력 오류", ""] + [f"- {e}" for e in summary["errors"]]
    return "\n".join(lines) + "\n"
