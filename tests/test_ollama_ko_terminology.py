"""Q3: 용어집·캐릭터 사전·name 치환표의 한국어 표기 일관성 점검(합성 프로젝트)."""
from pathlib import Path

import yaml

from GalTransl.OllamaKoTools import build_report, check_terminology, write_report

CONFIG = """plugin:
  filePlugin: file_vn_scene_txt
backendSpecific:
  Ollama:
    characterFile: characters.yaml
dictionary:
  gpt.dict: ["(project_dir)glossary.txt", "(project_dir)项目GPT字典-生成.txt", "공통GPT사전.txt"]
"""


def _project(tmp_path: Path) -> Path:
    (tmp_path / "gt_input").mkdir()
    (tmp_path / "config.yaml").write_text(CONFIG, encoding="utf-8")
    (tmp_path / "glossary.txt").write_text(
        "# 합성 용어집\n湊\t미나또\t남자 주인공\n葵\t아오이\n白鷺結衣\t시라사기 유이\t인명, 여성\n結衣\t유이\n", encoding="utf-8")
    (tmp_path / "characters.yaml").write_text(
        "characters:\n  - ja: 湊\n    ko: 미나토\n  - ja: 葵\n    ko: 아오이\n", encoding="utf-8")
    (tmp_path / "项目GPT字典-生成.txt").write_text(
        "# 형식\n----------↓인명↓----------\n結衣\t유이\t인명, 여성\n白鷺葵\t시라사기 아오리\t인명, 여성\n"
        "----------↓조직↓----------\n職員室\t교무실\t조직\n", encoding="utf-8")
    (tmp_path / "name替换表.csv").write_text(
        "SRC_Name,DST_Name,Count\n白鷺結衣,시라사기유이,3\n葵,아오이,2\n", encoding="utf-8")
    return tmp_path


def _codes(issues):
    return {(i["code"], i["source"]) for i in issues}


def test_conflicts_and_name_parts_are_reported(tmp_path):
    issues, info = check_terminology(_project(tmp_path), yaml.safe_load(CONFIG))
    codes = _codes(issues)
    assert ("term_conflict", "湊") in codes  # 미나또 vs 미나토
    assert ("name_part_mismatch", "白鷺葵") in codes  # 葵=아오이 인데 아오리
    # 띄어쓰기만 다른 표기는 충돌이 아님
    assert ("term_conflict", "白鷺結衣") not in codes
    assert ("term_conflict", "葵") not in codes
    assert all(i["level"] == "warning" for i in issues)
    # 생성 사전에만 있는 항목은 확인 필요 목록으로
    assert [u["source"] for u in info["unreviewed"]] == ["白鷺葵", "職員室"]
    assert "공통GPT사전.txt" in info["skipped"]


def test_report_includes_terminology(tmp_path):
    project = _project(tmp_path)
    report = build_report(project)
    assert any(i["code"] == "term_conflict" for i in report["issues"])
    assert report["terminology"]["unreviewed"]
    md = write_report(project, report).read_text(encoding="utf-8")
    assert "확인 필요 용어" in md and "職員室" in md


def test_no_dictionaries_is_fine(tmp_path):
    (tmp_path / "gt_input").mkdir()
    issues, info = check_terminology(tmp_path, {})
    assert issues == [] and info["unreviewed"] == []
