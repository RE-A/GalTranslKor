# 한국어 번역 품질 평가 세트 (합성)

직접 작성한 합성 장면 8개(97줄)와 줄마다의 채점 기준입니다. 실제 게임 원문이 아닙니다.
자동 검사(품질 리포트)는 구조·표기 오류만 봅니다. 이 세트는 **사람이 의미·말투를 채점해 설정끼리 비교**하는 용도입니다.

- `gt_input/s01~s08_*.txt`: 장면 TXT (`file_vn_scene_txt` 형식)
- `items.yaml`: 줄마다 `meaning`(반드시 보존할 의미), `acceptable`(허용 예), `forbidden`(금지 오역과 이유), `tags`(오류 유형)
- `split`: s01~s03은 `dev`(지침·사전 조정에 참고 가능), s04~s08은 `test`(최종 비교용). **test의 허용/금지 예시를 프롬프트·용어집에 넣지 마세요.**
- `config.yaml`, `characters.yaml`, `glossary.txt`: 평가용 프로젝트 설정(모델 이름만 바꾸면 실행 가능)

## 사용 순서 (로컬 Windows)

1. 이 폴더를 비교할 설정 수만큼 복사합니다. 예: `projects\eval_base`, `projects\eval_new`
2. 각 복사본의 `config.yaml`에서 비교할 항목 **하나만** 바꾸고 번역합니다.
   `.venv\Scripts\python.exe run_ollama_ko.py projects\eval_base`
3. 블라인드 채점표를 만듭니다. 어느 열이 어느 설정인지는 항목마다 무작위이며 `.key.json`에만 기록됩니다.
   `.venv\Scripts\python.exe eval_ollama_ko.py sheet --system base=projects\eval_base --system new=projects\eval_new --out projects\eval_sheet.csv`
4. CSV를 엑셀 등으로 열어 `T1_*`, `T2_*`, `preference`, `comment` 열을 채웁니다. 채점이 끝날 때까지 키 파일은 열지 않습니다.
5. 집계: `.venv\Scripts\python.exe eval_ollama_ko.py summarize projects\eval_sheet.csv` → `eval_sheet.csv.summary.md`

세트를 고친 뒤에는 `eval_ollama_ko.py validate`로 항목과 장면 줄이 맞는지 확인합니다.

## 채점 기준 (각 0~4점)

| 점수 | 의미 정확성 `meaning` | 자연스러움 `fluency` | 말투·관계 `voice` | 용어 `terms` |
| --- | --- | --- | --- | --- |
| 4 | `meaning`을 모두 보존 | 원어민 문장 | 화자·상대에 맞는 말투·호칭 | 용어집·인명 일치 |
| 3 | 사소한 뉘앙스 차이 | 약간 어색 | 사소한 어긋남 | 사소한 표기 흔들림 |
| 2 | 일부 의미 손실 | 번역투가 눈에 띔 | 존대/반말 등 한 번 어긋남 | 다른 표기 사용 |
| 1 | 핵심 의미 손실 | 읽기 불편 | 관계가 틀리게 읽힘 | 다른 인물·용어로 읽힘 |
| 0 | 반대 의미·무관 | 이해 불가 | 완전히 다른 인물 같음 | 용어 무시 |

`T*_critical`에는 해당하는 중대 오류 코드를 쉼표로 적습니다. 평균 점수와 별도로 집계됩니다.
`omission`(누락) `addition`(추가) `actor`(행위자 반전) `negation`(부정 반전) `number`(숫자) `control`(제어코드 손상) `name`(이름·호칭)

`preference`는 `T1`, `T2`, `tie` 중 하나입니다. 원문과 `context`(앞 줄)를 함께 보고 판단하세요.
모델이 매긴 점수는 참고로만 쓰고, 사람이 확인한 결과를 기록합니다. 단일 문자열 유사도나 자동 오류 0건으로 품질을 판정하지 않습니다.
