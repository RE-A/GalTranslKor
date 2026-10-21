"""Compare Ollama-ko settings on a small excerpt of a project.

Each case copies the project settings and the first N translatable lines into
<project>/ollama_ko_logs/benchmark/<run>/<case>/, runs a full translation there,
and collects the engine statistics, quality report and Ollama memory placement.
The original project, its cache and its output are never touched.

Case format: NAME:MODEL:BATCH:NUMCTX  (MODEL "-" = model from config.yaml)
Default cases: A:-:5:8192 and B:-:10:8192. Add C with --case C:<small model>:10:8192.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import yaml

ROOT = Path(__file__).resolve().parent
COPY_FILES = ("glossary.txt", "characters.yaml", "JapaneseToKorean.md", "translation_guideline.md")


def parse_case(text: str) -> dict:
    parts = text.split(":")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(f"case must be NAME:MODEL:BATCH:NUMCTX, got {text}")
    name, model, batch, num_ctx = parts
    try:
        return {"name": name, "model": model, "batch": int(batch), "numCtx": int(num_ctx)}
    except ValueError:
        raise argparse.ArgumentTypeError(f"BATCH and NUMCTX must be integers: {text}") from None


def excerpt_inputs(project: Path, target: Path, cfg: dict, limit: int) -> int:
    """Copy whole leading lines until `limit` translatable lines are included."""
    from GalTransl.OllamaKoTools import _scene_plugin
    plugin_name = (cfg.get("plugin") or {}).get("filePlugin", "")
    target.mkdir(parents=True, exist_ok=True)
    total = 0
    for path in sorted(p for p in (project / "gt_input").rglob("*") if p.is_file()):
        if total >= limit:
            break
        rel = path.relative_to(project / "gt_input")
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        if plugin_name == "file_vn_scene_txt":
            module, plugin = _scene_plugin(cfg)
            kept = []
            for entry in plugin.load_file(str(path)):
                if total >= limit:
                    break
                kept.append(entry)
                total += bool(entry["message"].strip())
            (target / rel).write_text(module.render_lines(kept), encoding="utf-8")
        elif plugin_name == "file_galtransl_json":
            kept = []
            for entry in json.loads(path.read_text(encoding="utf-8")):
                if total >= limit:
                    break
                kept.append(entry)
                total += bool(str(entry.get("message", "")).strip())
            (target / rel).write_text(json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            raise SystemExit(f"benchmark supports file_vn_scene_txt/file_galtransl_json, not {plugin_name}")
    return total


def ollama_root(endpoint: str) -> str:
    endpoint = endpoint.rstrip("/")
    for suffix in ("/v1/chat/completions", "/api/chat", "/v1", "/api"):
        if endpoint.endswith(suffix):
            return endpoint[:-len(suffix)]
    return endpoint


def memory_placement(endpoint: str, model: str) -> dict:
    """Ollama /api/ps reports how much of the loaded model sits in VRAM."""
    import httpx
    try:
        response = httpx.get(ollama_root(endpoint) + "/api/ps", timeout=5, trust_env=False)
        response.raise_for_status()
        for item in response.json().get("models", []):
            if {model, f"{model}:latest"} & {item.get("name"), item.get("model")}:
                size, vram = item.get("size") or 0, item.get("size_vram") or 0
                return {"size_bytes": size, "vram_bytes": vram,
                        "gpu_share": round(vram / size, 3) if size else None,
                        "context_length": item.get("context_length")}
        return {"note": "model not loaded"}
    except Exception as exc:  # informational only
        return {"note": f"/api/ps unavailable: {type(exc).__name__}"}


def gpu_snapshot() -> str:
    if not shutil.which("nvidia-smi"):
        return ""
    try:
        return subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader"], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def run_case(project: Path, cfg: dict, case: dict, folder: Path, lines: int) -> dict:
    work = folder / case["name"]
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    for name in COPY_FILES:
        if (project / name).is_file():
            shutil.copy2(project / name, work / name)
    case_cfg = json.loads(json.dumps(cfg))
    ollama = case_cfg.setdefault("backendSpecific", {}).setdefault("Ollama", {})
    if case["model"] != "-":
        ollama["model"] = case["model"]
    ollama["numCtx"] = case["numCtx"]
    case_cfg.setdefault("common", {})["gpt.numPerRequestTranslate"] = case["batch"]
    (work / "config.yaml").write_text(yaml.safe_dump(case_cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    count = excerpt_inputs(project, work / "gt_input", case_cfg, lines)
    started = time.monotonic()
    result = subprocess.run([sys.executable, str(ROOT / "run_ollama_ko.py"), str(work)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    elapsed = time.monotonic() - started
    stats_files = sorted((work / "ollama_ko_logs").glob("stats-*.json"))
    stats = json.loads(stats_files[-1].read_text(encoding="utf-8")) if stats_files else {}
    report_file = work / "ollama_ko_logs" / "quality_report.json"
    report = json.loads(report_file.read_text(encoding="utf-8")) if report_file.is_file() else {}
    missing = sum(i["code"] in ("missing_translation", "translation failed") for i in report.get("issues", []))
    return {
        "case": case["name"], "model": ollama.get("model", ""), "batch": case["batch"],
        "numCtx": case["numCtx"], "lines": count, "exit_code": result.returncode,
        "seconds": round(elapsed, 2),
        "lines_per_minute": round(stats.get("lines_translated", 0) * 60 / elapsed, 2) if elapsed else 0,
        "requests": stats.get("requests", 0), "retries": stats.get("retries", 0),
        "batch_shrinks": stats.get("batch_shrinks", 0),
        "prompt_tokens": stats.get("prompt_tokens", 0), "output_tokens": stats.get("output_tokens", 0),
        "model_seconds": stats.get("model_seconds", 0), "errors": sum((stats.get("errors") or {}).values()),
        "failed_lines": stats.get("lines_failed", 0), "missing_lines": missing,
        "fatal": report.get("fatal"), "warnings": report.get("warning"),
        "memory": memory_placement(ollama.get("endpoint", "http://127.0.0.1:11434"), ollama.get("model", "")),
        "gpu": gpu_snapshot(),
        "log_tail": (result.stdout + result.stderr)[-400:] if result.returncode else "",
    }


def write_summary(folder: Path, results: list) -> Path:
    (folder / "benchmark.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    head = ["case", "model", "batch", "numCtx", "lines", "exit_code", "seconds", "lines_per_minute",
            "requests", "retries", "batch_shrinks", "prompt_tokens", "output_tokens", "errors",
            "failed_lines", "missing_lines", "fatal", "warnings"]
    rows = ["| " + " | ".join(head) + " | GPU 비율 | GPU |", "|" + " --- |" * (len(head) + 2)]
    for r in results:
        share = r["memory"].get("gpu_share", r["memory"].get("note", ""))
        rows.append("| " + " | ".join(str(r[k]) for k in head) + f" | {share} | {r['gpu'] or '-'} |")
    path = folder / "benchmark.md"
    path.write_text("# Ollama-ko 벤치마크\n\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Ollama-ko 설정별 속도·안정성 비교")
    parser.add_argument("project", type=Path)
    parser.add_argument("--lines", type=int, default=80, help="케이스마다 번역할 줄 수 (기본 80)")
    parser.add_argument("--case", action="append", type=parse_case, dest="cases",
                        help="NAME:MODEL:BATCH:NUMCTX, 여러 번 지정 가능")
    args = parser.parse_args(argv)
    project = args.project.resolve()
    if not (project / "config.yaml").is_file():
        parser.error(f"설정 파일이 없습니다: {project / 'config.yaml'}")
    if not 1 <= args.lines <= 1000:
        parser.error("--lines must be between 1 and 1000")
    cases = args.cases or [parse_case("A:-:5:8192"), parse_case("B:-:10:8192")]
    cfg = yaml.safe_load((project / "config.yaml").read_text(encoding="utf-8")) or {}
    folder = project / "ollama_ko_logs" / "benchmark" / time.strftime("%Y%m%d-%H%M%S")
    results = []
    for case in cases:
        print(f"[{case['name']}] model={case['model']} batch={case['batch']} numCtx={case['numCtx']} ...", flush=True)
        results.append(run_case(project, cfg, case, folder, args.lines))
        r = results[-1]
        print(f"  {r['seconds']}s, {r['lines_per_minute']} lines/min, exit {r['exit_code']}, "
              f"retries {r['retries']}, failed {r['failed_lines']}", flush=True)
    print(f"결과: {write_summary(folder, results)}")
    return 0 if all(r["exit_code"] == 0 for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
