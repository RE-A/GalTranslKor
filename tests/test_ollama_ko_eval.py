"""Q1: 합성 평가 세트 형식과 블라인드 채점표 흐름(Mock Ollama, 품질 판정 아님)."""
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys

import yaml

from ollama_mock import mock_ollama
from GalTransl.OllamaKoEval import load_items, make_sheet, summarize, summary_markdown, validate

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "examples" / "ollama_ko_eval"


def test_committed_eval_set_is_complete_and_synthetic():
    assert validate(EVAL) == []
    items = load_items(EVAL)
    scenes = sorted((EVAL / "gt_input").glob("*.txt"))
    assert len(scenes) == 8 and len(items) >= 90
    assert {i["split"] for i in items} == {"dev", "test"}
    # dev/test는 장면 단위로 나뉜다
    assert all(len({i["split"] for i in items if i["file"] == s.name}) == 1 for s in scenes)
    tags = {t for i in items for t in i["tags"]}
    for needed in ("keigo_shift", "subject_drop", "negation", "double_negation", "giving_receiving",
                   "homonym_name", "wordplay", "scene_change", "monologue", "unattributed_quote", "control_code"):
        assert needed in tags, needed
    for scene in scenes:
        assert "合成" in scene.read_text(encoding="utf-8").splitlines()[0]


def test_validate_reports_missing_and_unknown_lines(tmp_path):
    shutil.copytree(EVAL, tmp_path / "set")
    data = yaml.safe_load((tmp_path / "set" / "items.yaml").read_text(encoding="utf-8"))
    data["items"][0]["line"] = 1  # comment line
    (tmp_path / "set" / "items.yaml").write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    errors = validate(tmp_path / "set")
    assert any("not a translatable line" in e for e in errors)
    assert any("line has no item" in e for e in errors)


def _translate(folder: Path, url: str):
    shutil.copytree(EVAL, folder)
    cfg = yaml.safe_load((folder / "config.yaml").read_text(encoding="utf-8"))
    cfg["backendSpecific"]["Ollama"].update(model="mock-ko", endpoint=url, maxAttempts=1)
    (folder / "config.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    result = subprocess.run([sys.executable, str(ROOT / "run_ollama_ko.py"), str(folder)],
                            capture_output=True, text=True, timeout=120)
    assert (folder / "transl_cache").is_dir(), result.stdout + result.stderr


def test_blind_sheet_and_summary_with_mock_translations(tmp_path):
    with mock_ollama() as (url, _calls):
        _translate(tmp_path / "base", url)
        _translate(tmp_path / "new", url)
    out = tmp_path / "sheet.csv"
    make_sheet(EVAL, {"base": tmp_path / "base", "new": tmp_path / "new"}, out, split="test", seed=1)
    key = json.loads(Path(f"{out}.key.json").read_text(encoding="utf-8"))
    with out.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    test_items = [i for i in load_items(EVAL) if i["split"] == "test"]
    assert [r["id"] for r in rows] == [i["id"] for i in test_items]
    assert "base" not in out.read_text(encoding="utf-8-sig")  # 시스템 이름은 키 파일에만
    assert {tuple(v) for v in key["items"].values()} == {("base", "new"), ("new", "base")}
    assert any(r["T1"].startswith("한국어 번역") for r in rows)  # Mock 응답이 읽힘
    assert rows[1]["context"]  # 앞 줄 문맥 포함

    # 채점자가 T1에는 4점, T2에는 2점과 부정 반전을 매겼다고 가정
    for row in rows:
        for axis in ("meaning", "fluency", "voice", "terms"):
            row[f"T1_{axis}"], row[f"T2_{axis}"] = "4", "2"
        row["T2_critical"] = "negation"
        row["preference"] = "T1"
    rows[0]["T1_meaning"] = "5"  # 잘못된 점수는 오류로 보고
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = summarize(out)
    t1_first = sum(1 for v in key["items"].values() if v[0] == "base")
    base, new = summary["systems"]["base"], summary["systems"]["new"]
    assert base["preferred"] + new["preferred"] == len(rows)
    assert base["preferred"] == t1_first
    assert base["critical"]["negation"] + new["critical"]["negation"] == len(rows)
    assert summary["errors"] == [f"{rows[0]['id']} T1_meaning: score must be 0-4", f"{rows[0]['id']} T1: incomplete scores"]
    assert "중대 오류" in summary_markdown(summary)


def test_cli_validate_and_single_system_sheet(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / "eval_ollama_ko.py"), "validate"],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    out = tmp_path / "one.csv"
    make_sheet(EVAL, {"only": tmp_path / "missing"}, out, split="dev")
    with out.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows and "T2" not in rows[0] and rows[0]["T1"] == ""
