"""Noninteractive, portable entry point for the Ollama Korean workflow.

Exit codes: 0 success, 1 job/configuration error,
2 finished but the quality report found fatal problems (rerun to retry them).
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="GalTransl 일본어 → 한국어 (Ollama)")
    parser.add_argument("project", nargs="?", type=Path,
                        default=Path(__file__).resolve().parent / "examples" / "ollama_ko_scene")
    parser.add_argument("--config", default="config.yaml", help="Project configuration filename")
    parser.add_argument("--init", action="store_true",
                        help="새 TXT 장면 프로젝트(설정·용어집·캐릭터·번역 지침)를 만들고 종료")
    parser.add_argument("--no-check", action="store_true", help="번역 후 품질 검사를 생략")
    args = parser.parse_args(argv)
    project = args.project.resolve()
    if args.init:
        from GalTransl.OllamaKoTools import init_project
        try:
            init_project(project)
        except FileExistsError as exc:
            parser.error(str(exc))
        print(f"프로젝트 생성: {project}")
        print(f"1) {project / 'config.yaml'}의 model 값을 설정  2) {project / 'gt_input'}에 TXT 투입  3) 다시 실행")
        return 0
    if not (project / args.config).is_file():
        parser.error(f"설정 파일이 없습니다: {project / args.config}")
    # Supported upstream override: portable sample data stays in the project.
    os.environ.setdefault("GALTRANSL_DATA_DIR", str(project / ".galtransl-data"))
    from GalTransl.Service import JobSpec, run_job

    state = run_job(JobSpec(str(project), "Ollama-ko", config_file_name=args.config))
    if not state.success:
        print(f"번역 실패: {state.error or state.status}")
        print("같은 명령으로 다시 실행하면 저장된 번역은 건너뛰고 남은 줄부터 이어서 번역합니다.")
        return 1
    print(f"번역 완료: {project / 'gt_output'}")
    if args.no_check:
        return 0
    from GalTransl.OllamaKoTools import build_report, write_report
    report = build_report(project, args.config)
    path = write_report(project, report)
    print(f"품질 검사: 대상 {report['lines']}줄, 치명적 오류 {report['fatal']}건, 경고 {report['warning']}건 → {path}")
    if report["fatal"]:
        print("치명적 오류가 있습니다. 같은 명령으로 다시 실행하면 실패·누락된 줄만 다시 번역합니다.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
