"""Korean quality evaluation helpers for the synthetic set in examples/ollama_ko_eval.

  validate   check that items.yaml covers every scene line
  sheet      write a blind rating CSV from one or two translated copies of the set
  summarize  aggregate a filled CSV (uses <sheet>.key.json written by `sheet`)

Model translation itself is done with run_ollama_ko.py on copies of the set.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_SET = Path(__file__).resolve().parent / "examples" / "ollama_ko_eval"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Ollama-ko 한국어 품질 평가 채점표")
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate", help="평가 세트 항목 확인")
    v.add_argument("eval_dir", type=Path, nargs="?", default=DEFAULT_SET)
    s = sub.add_parser("sheet", help="블라인드 채점표 만들기")
    s.add_argument("--eval", dest="eval_dir", type=Path, default=DEFAULT_SET)
    s.add_argument("--system", action="append", required=True, metavar="이름=프로젝트폴더",
                   help="번역을 마친 평가 세트 복사본. 1~2개")
    s.add_argument("--split", choices=("dev", "test", "all"), default="test")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--out", type=Path, required=True)
    m = sub.add_parser("summarize", help="채점한 CSV 집계")
    m.add_argument("sheet", type=Path)
    args = parser.parse_args(argv)

    from GalTransl.OllamaKoEval import make_sheet, summarize, summary_markdown, validate
    if args.command == "validate":
        errors = validate(args.eval_dir)
        for error in errors:
            print(error)
        print(f"오류 {len(errors)}건")
        return 1 if errors else 0
    if args.command == "sheet":
        systems = {}
        for spec in args.system:
            label, sep, folder = spec.partition("=")
            if not sep or not label or not folder:
                parser.error(f"--system은 이름=폴더 형식이어야 합니다: {spec}")
            systems[label] = Path(folder)
        path = make_sheet(args.eval_dir, systems, args.out, split=args.split, seed=args.seed)
        print(f"채점표: {path}  (정답 키: {path}.key.json — 채점이 끝날 때까지 열지 마세요)")
        return 0
    summary = summarize(args.sheet)
    md = Path(f"{args.sheet}.summary.md")
    md.write_text(summary_markdown(summary), encoding="utf-8")
    Path(f"{args.sheet}.summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"집계: {md}  입력 오류 {len(summary['errors'])}건")
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
