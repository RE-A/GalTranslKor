"""Write the Korean translation quality report of a GalTransl project without translating.

Exit code 0: no fatal problems, 2: fatal problems found, 1: invalid project.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Ollama-ko 번역 결과 품질 검사")
    parser.add_argument("project", type=Path)
    parser.add_argument("--config", default="config.yaml", help="Project configuration filename")
    args = parser.parse_args(argv)
    project = args.project.resolve()
    if not (project / args.config).is_file():
        parser.error(f"설정 파일이 없습니다: {project / args.config}")
    from GalTransl.OllamaKoTools import build_report, write_report
    report = build_report(project, args.config)
    path = write_report(project, report)
    print(f"대상 {report['lines']}줄, 정상 {report['translated']}줄, "
          f"치명적 오류 {report['fatal']}건, 경고 {report['warning']}건 → {path}")
    return 2 if report["fatal"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
