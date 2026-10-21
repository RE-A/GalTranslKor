"""Noninteractive, portable entry point for the Ollama Korean workflow."""
from __future__ import annotations

import argparse
import os
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="GalTransl 일본어 → 한국어 (Ollama)")
    parser.add_argument("project", nargs="?", type=Path,
                        default=Path(__file__).resolve().parent / "examples" / "ollama_ko")
    parser.add_argument("--config", default="config.yaml", help="Project configuration filename")
    args = parser.parse_args(argv)
    project = args.project.resolve()
    if not (project / args.config).is_file():
        parser.error(f"설정 파일이 없습니다: {project / args.config}")
    # Supported upstream override: portable sample data stays in the project.
    os.environ.setdefault("GALTRANSL_DATA_DIR", str(project / ".galtransl-data"))
    from GalTransl.Service import JobSpec, run_job

    state = run_job(JobSpec(str(project), "Ollama-ko", config_file_name=args.config))
    if state.success:
        print(f"번역 완료: {project / 'gt_output'}")
        return 0
    print(f"번역 실패: {state.error or state.status}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
