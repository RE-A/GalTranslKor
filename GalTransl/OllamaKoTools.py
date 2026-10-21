"""Project helpers for the Ollama-ko workflow: template setup and quality report.

The report reads what GalTransl already stores (input files, transl_cache and
gt_output) and never modifies them.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil

import yaml

from GalTransl.Backend.OllamaPrompts import DEFAULT_GUIDELINE, load_characters
from GalTransl.Backend.OllamaQuality import fatal_problems, warning_problems
from GalTransl.RuntimePaths import get_plugins_dir, get_resource_root, get_translation_guidelines_dir

TEMPLATE = "examples/ollama_ko_scene"
TEMPLATE_FILES = ("config.yaml", "glossary.txt", "characters.yaml")
REPORT_NAME = "quality_report"
LOG_FOLDER = "ollama_ko_logs"


def init_project(target: Path) -> Path:
    """Create a ready-to-edit TXT scene project without sample game text."""
    target = Path(target)
    if (target / "config.yaml").exists():
        raise FileExistsError(f"{target / 'config.yaml'} already exists")
    template = get_resource_root() / TEMPLATE
    (target / "gt_input").mkdir(parents=True, exist_ok=True)
    for name in TEMPLATE_FILES:
        shutil.copy2(template / name, target / name)
    shutil.copy2(get_translation_guidelines_dir() / DEFAULT_GUIDELINE, target / DEFAULT_GUIDELINE)
    return target


def _load_plugin_module(name: str):
    path = get_plugins_dir() / name / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_report_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _scene_plugin(cfg: dict):
    module = _load_plugin_module("file_vn_scene_txt")
    conf = yaml.safe_load((get_plugins_dir() / "file_vn_scene_txt" / "file_vn_scene_txt.yaml").read_text(encoding="utf-8"))
    conf["Settings"].update((cfg.get("plugin") or {}).get("file_vn_scene_txt") or {})
    plugin = module.file_plugin()
    plugin.gtp_init(conf, {})
    return module, plugin


def _read_cache(cache_dir: Path, rel: str) -> dict:
    # Same naming as GalTransl: "/" -> "-}", ".json" appended unless present.
    name = rel.replace("/", "-}")
    if not name.endswith(".json"):
        name += ".json"
    records = {}
    snapshot = cache_dir / name
    if snapshot.is_file():
        for row in json.loads(snapshot.read_text(encoding="utf-8")):
            records[row.get("index")] = row
    append = cache_dir / f"{name}.append.jsonl"
    if append.is_file():
        for line in append.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                records[row.get("index")] = {**records.get(row.get("index"), {}), **row}
    return records


def _issue(issues, level, file, index, code, detail="", source="", text=""):
    issues.append({"level": level, "file": file, "index": index, "code": code,
                   "detail": detail, "source": source, "translation": text})


def build_report(project: Path, config_name: str = "config.yaml") -> dict:
    project = Path(project)
    cfg = yaml.safe_load((project / config_name).read_text(encoding="utf-8")) or {}
    ollama = (cfg.get("backendSpecific") or {}).get("Ollama") or {}
    allow = ollama.get("allowJapanese") or []
    min_ratio = ollama.get("minLengthRatio", 0.2)
    character_file = ollama.get("characterFile", "characters.yaml")
    korean_names = {}
    for character in load_characters(project / character_file) if character_file else []:
        for name in character["names"]:
            korean_names[name] = character["profile"]["ko"]
    plugin_name = (cfg.get("plugin") or {}).get("filePlugin", "")
    input_dir, output_dir, cache_dir = project / "gt_input", project / "gt_output", project / "transl_cache"
    issues, files, summary = [], [], {"lines": 0, "translated": 0}
    scene = _scene_plugin(cfg) if plugin_name == "file_vn_scene_txt" else None
    for path in sorted(p for p in input_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(input_dir).as_posix()
        if scene:
            entries = scene[1].load_file(str(path))
        elif plugin_name == "file_galtransl_json":
            entries = [dict(e, index=e.get("index", i)) for i, e in
                       enumerate(json.loads(path.read_text(encoding="utf-8")), 1)]
        else:
            _issue(issues, "warning", rel, None, "unsupported_plugin", f"report supports file_vn_scene_txt/file_galtransl_json, not {plugin_name}")
            continue
        files.append(rel)
        cache = _read_cache(cache_dir, rel)
        previous = None
        for entry in entries:
            source = entry.get("message", "")
            if not source.strip():
                continue
            summary["lines"] += 1
            index = entry["index"]
            row = cache.get(index)
            if row is None:
                _issue(issues, "fatal", rel, index, "missing_translation", "no cached translation", source)
                previous = None
                continue
            if row.get("pre_src") != source:
                _issue(issues, "fatal", rel, index, "stale_cache", "source changed after translation", source)
            text = row.get("proofread_dst") or row.get("pre_dst") or ""
            speaker = entry.get("name") or ""
            names = tuple(n for n in (speaker, korean_names.get(speaker, "")) if n)
            fatal = fatal_problems(row.get("post_src", source), text, allow=allow,
                                   speakers=names, min_ratio=min_ratio)
            for code in fatal:
                _issue(issues, "fatal", rel, index, code, "", source, text)
            if not fatal:
                summary["translated"] += 1
                for code in warning_problems(row.get("post_src", source), text, allow=allow):
                    _issue(issues, "warning", rel, index, code, "", source, text)
            if previous and text and previous[1] == text and previous[0] != source:
                _issue(issues, "warning", rel, index, "duplicate_translation", "same as previous line", source, text)
            previous = (source, text)
        _check_output(issues, rel, entries, output_dir / rel, scene)
    counts = {level: sum(i["level"] == level for i in issues) for level in ("fatal", "warning")}
    return {"project": str(project), "files": files, **summary, **counts, "issues": issues}


def _check_output(issues, rel, entries, output, scene):
    if not output.is_file():
        _issue(issues, "fatal", rel, None, "output_missing", str(output))
        return
    try:
        if scene:
            produced = scene[1].load_file(str(output))
            if len(produced) != len(entries):
                _issue(issues, "fatal", rel, None, "output_line_count", f"{len(entries)} -> {len(produced)}")
                return
            for before, after in zip(entries, produced):
                if not before["message"] and before[scene[0].FRAME_KEY].get("raw") != after[scene[0].FRAME_KEY].get("raw"):
                    _issue(issues, "fatal", rel, before["index"], "untranslated_line_changed")
                elif ("name" in before) != ("name" in after):
                    _issue(issues, "fatal", rel, before["index"], "speaker_format_changed")
        else:
            produced = json.loads(output.read_text(encoding="utf-8"))
            if len(produced) != len(entries):
                _issue(issues, "fatal", rel, None, "output_entry_count", f"{len(entries)} -> {len(produced)}")
            elif any(("name" in a) != ("name" in b) for a, b in zip(entries, produced)):
                _issue(issues, "fatal", rel, None, "speaker_field_changed")
    except (ValueError, UnicodeError) as exc:
        _issue(issues, "fatal", rel, None, "output_format_error", str(exc))


def write_report(project: Path, report: dict) -> Path:
    folder = Path(project) / LOG_FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{REPORT_NAME}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 번역 품질 검사 결과", "",
        f"- 파일 {len(report['files'])}개, 번역 대상 {report['lines']}줄, 정상 {report['translated']}줄",
        f"- 치명적 오류 {report['fatal']}건, 경고 {report['warning']}건", "",
        "치명적 오류는 재번역이 필요합니다. 같은 명령으로 다시 실행하면 실패·누락된 줄만 다시 번역합니다.",
        "경고는 정상 번역일 수 있으므로 직접 확인하세요.", "",
        "| 수준 | 파일 | 줄 | 문제 | 원문 | 번역 |", "| --- | --- | --- | --- | --- | --- |",
    ]
    def cell(value):
        return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")[:120]
    for issue in report["issues"]:
        code = issue["code"] + (f" ({issue['detail']})" if issue["detail"] else "")
        lines.append(f"| {issue['level']} | {cell(issue['file'])} | {cell(issue['index'])} | {cell(code)} "
                     f"| {cell(issue['source'])} | {cell(issue['translation'])} |")
    path = folder / f"{REPORT_NAME}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
