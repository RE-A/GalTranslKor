# GalTransl + Ollama 일본어 → 한국어 비주얼 노벨 번역

이 Fork의 `Ollama-ko` 번역기는 로컬 Ollama 모델로 장면별 일본어 스크립트(TXT)를 한국어로 번역합니다.
GalTransl의 기존 작업 실행기, 파일 플러그인, 용어집(GPT 사전), 이름 치환표, 번역 캐시와
출력 구조를 그대로 사용하고 한국어 번역에 필요한 부분만 추가했습니다.
번역 데이터와 프롬프트는 설정한 Ollama 주소로만 전송되며 외부 상용 API를 사용하지 않습니다.

> 현재 저장소의 테스트는 Linux 클라우드에서 **HTTP Mock 서버**로 수행했습니다. 실제 Ollama 모델의
> 번역 품질, 속도, GPU 사용량과 Windows 실행은 아직 검증되지 않았습니다([알려진 제약](#알려진-제약과-개선-가능-사항)).

## 빠른 시작 (Windows)

```bat
:: 1) 최초 설치: Python 3.11(py 런처 포함)과 Ollama 설치 후, 저장소 폴더에서
setup_ollama_ko.cmd

:: 2) 새 번역 프로젝트 만들기 (projects\ 폴더는 Git에서 제외됨)
run_ollama_ko.cmd projects\mygame --init

:: 3) projects\mygame\config.yaml의 model 값 입력, gt_input 폴더에 장면 TXT 복사

:: 4) 환경 점검 후 번역
powershell -ExecutionPolicy Bypass -File scripts\check_environment.ps1 -Project projects\mygame -TestChat
powershell -ExecutionPolicy Bypass -File scripts\start_translation.ps1 -Project projects\mygame
```

`.cmd`와 `.ps1`은 같은 Python 실행기(`run_ollama_ko.py`)를 호출합니다. 편한 쪽을 쓰면 됩니다.

## 1. 최초 설치

1. 이 Fork(`RE-A/GalTranslKor`)의 `main` 브랜치를 내려받아 압축을 풉니다.
2. [Python 3.11](https://www.python.org/downloads/)을 설치합니다. 설치 화면에서 *py launcher*를 포함합니다.
3. [Ollama](https://ollama.com/download)를 설치합니다.
4. 저장소 폴더에서 `setup_ollama_ko.cmd`를 실행합니다. `.venv` 가상환경과 `requirements.txt` 의존성을
   설치합니다(인터넷 필요). `start_translation.ps1`과 `run_ollama_ko.cmd`도 `.venv`가 없으면 자동으로 실행합니다.

## 2. Ollama 실행과 모델 확인

```bat
ollama serve          :: 트레이 앱이 이미 실행 중이면 생략
ollama list           :: 설치된 모델과 정확한 이름(태그 포함) 확인
ollama ps             :: 현재 적재된 모델과 GPU/CPU 배분 확인
```

커스텀 모델은 `ollama create 내모델 -f Modelfile`로 등록한 이름을 그대로 씁니다.
`scripts\check_environment.ps1`은 Python, 가상환경, `nvidia-smi`, Ollama 서버(`/api/version`),
설치 모델 목록(`/api/tags`), 설정 모델의 설치 여부, OpenAI 호환 API(`/v1/models`)를 점검합니다.
`-TestChat`을 붙이면 짧은 일본어 문장을 실제로 번역해 응답 시간, 토큰 수와 GPU 적재 비율(`/api/ps`)을 보여 줍니다.

## 3. 번역할 파일 넣는 위치

GalTransl 프로젝트 구조를 그대로 씁니다.

```
projects\mygame\
├── config.yaml            모든 설정 (모델, 주소, 배치, 문맥, 온도, 재시도 ...)
├── JapaneseToKorean.md    한국어 번역 지침 (프롬프트) - 자유롭게 수정
├── glossary.txt           용어집: 원어<TAB>한국어<TAB>설명
├── characters.yaml        캐릭터 사전: 이름, 성격, 말투, 관계, 존댓말 규칙
├── gt_input\              ← 번역할 장면 TXT를 여기에 넣음 (scene_001.txt ...)
├── gt_output\             → 번역 결과 (같은 파일명)
├── transl_cache\          → 줄 단위 번역 캐시 (중단 후 재개용)
├── name替换表.csv          → 화자 이름 표 (GalTransl 자동 생성)
└── ollama_ko_logs\        → 품질 리포트, 실패 줄 기록, 통계, 벤치마크
```

원본 파일은 `gt_input`에서 읽기만 하며 수정하지 않습니다. 하위 폴더도 지원합니다.

### 지원하는 TXT 형식 (`file_vn_scene_txt` 플러그인)

| 원문 줄 | 처리 |
| --- | --- |
| `【葵】「おはよう。」` | 화자 `葵`, 번역 대상 `おはよう。` → `【아오이】「좋은 아침.」` |
| `湊「行こう。」` | 화자 `湊` (이름 바로 뒤에 「」 대사가 줄 끝까지 있을 때) |
| `「名無しの台詞。」` | 화자 미표시 대사. 괄호를 포함해 번역하고 괄호 보존을 검사 |
| `放課後の教室には…` / `（独白…）` | 지문·독백으로 번역 |
| 빈 줄, `;`, `//`, `#`, `*`, `@`로 시작하는 줄, `[명령]`만 있는 줄 | 모델에 보내지 않고 원문 그대로 출력 |

- 줄 순서와 줄 수, 들여쓰기, 줄 끝 공백, CRLF/LF, 마지막 줄바꿈 유무, UTF-8 BOM을 보존합니다.
- 인코딩은 UTF-8(BOM 포함), UTF-16(BOM), Shift-JIS(cp932)를 자동 판별합니다. 출력은 UTF-8입니다
  (한국어는 Shift-JIS로 저장할 수 없음).
- 문장 안의 `{name}`, `%s`, `[wait]`, `<tag>`, `\n` 같은 제어 표기는 번역문에서 같은 개수로 보존돼야 합니다.
- 다른 화자 표기나 명령 문법이 있으면 `config.yaml`의 `plugin.file_vn_scene_txt.speakerPatterns`,
  `skipPatterns`에 정규식을 추가합니다(`name`, `text` 그룹 필수).
- 화자 이름은 `useGPTDictInName: true`일 때 `glossary.txt`의 한국어 이름으로 바뀝니다.
  원래 이름을 유지하려면 `false`로 바꾸거나 GalTransl의 `name替换表.csv`(SRC_Name, DST_Name)를 편집합니다.

기존 GalTransl JSON(`[{"name":"葵","message":"…"}]`)은 `examples/ollama_ko` 예제처럼
`filePlugin: file_galtransl_json`으로 그대로 쓸 수 있습니다.

## 4. 번역 명령

```bat
run_ollama_ko.cmd projects\mygame
:: 또는
powershell -ExecutionPolicy Bypass -File scripts\start_translation.ps1 -Project projects\mygame
```

번역이 끝나면 자동으로 품질 검사를 실행합니다. 종료 코드: `0` 정상, `2` 번역은 끝났지만
치명적 품질 오류가 있음, `1` 설정·연결 오류 등으로 중단.
품질 검사만 다시 하려면 `.venv\Scripts\python.exe check_ollama_ko.py projects\mygame`
또는 `start_translation.ps1 -CheckOnly`를 사용합니다.

## 5. 결과 확인

- 번역 결과: `gt_output\<원본과 같은 파일명>`
- 품질 리포트: `ollama_ko_logs\quality_report.md` (표), `quality_report.json`
  - 용어 점검: 프로젝트 용어집(`(project_dir)` GPT 사전), `characters.yaml`, `name替换表.csv`에서 같은 원문의
    한국어 표기가 다르면 `term_conflict`, 등록된 이름이 풀네임 표기와 어긋나면 `name_part_mismatch` 경고를 냅니다
    (띄어쓰기 차이는 허용). GenDic 생성 사전에만 있는 항목은 "확인 필요 용어" 표로 따로 보여 줍니다. 파일은 수정하지 않습니다.
- 실패 줄 기록: `ollama_ko_logs\failures-<실행시각>.jsonl` (파일, 줄 번호, 화자, 원문, 실패 이유)
- 실행 통계: `ollama_ko_logs\stats-<실행시각>.json` (요청·재시도·실패 수, 입력/출력 토큰, 모델 처리 시간, 줄/분)
- GalTransl 실행 로그: 프로젝트 폴더의 `GalTransl.log` (`saveLog: true`)

번역에 끝내 실패한 줄은 출력 파일에 `(Failed)원문` 형태로 남습니다(GalTransl 기존 표기).

설정이나 모델을 바꿨을 때 품질이 좋아졌는지는 합성 평가 세트 `examples/ollama_ko_eval`과
`eval_ollama_ko.py`(블라인드 A/B 채점표·집계)로 비교합니다. 사용법은 [평가 세트 README](examples/ollama_ko_eval/README.md)를 보세요.

## 6. 중단된 번역 재개

같은 명령을 다시 실행하면 됩니다.

- 검증을 통과한 배치는 즉시 `transl_cache`에 저장됩니다. 재실행하면 저장된 줄은 모델을 다시 호출하지 않고,
  이전 문맥도 캐시에서 복원합니다.
- `(Failed)`로 남은 줄, 검증에 실패한 캐시, 원문이 바뀐 줄만 다시 번역합니다.
- 모델 이름, Ollama 주소, 번역 지침, 용어집, 캐릭터 사전, 온도·문맥·컨텍스트 설정을 바꾸면 이전 번역과
  섞이지 않도록 캐시 식별자가 달라져 **전체를 다시 번역**합니다. 일부만 다시 하려면 해당 파일의
  `transl_cache` 항목을 지우는 대신 설정을 유지한 채 실행하세요.

## 7. 다른 커스텀 모델로 변경

`config.yaml`의 `backendSpecific.Ollama.model`을 `ollama list`의 다른 이름으로 바꾸면 됩니다.
모델마다 토크나이저와 속도가 다르므로 아래 설정을 함께 조정하고 [벤치마크](#9-성능-실험)로 비교하세요.

- 오래된 Ollama가 `think` 파라미터를 거부하면 `think: null`로 바꿉니다.
- JSON 구조화 출력을 잘 따르지 못하는 모델은 재시도가 늘어납니다. 배치를 줄이거나 다른 모델을 사용하세요.

## 8. 품질과 속도 설정

모든 값은 `config.yaml`에서 바꾸며 소스코드를 수정할 필요가 없습니다.

| 설정 | 기본값 | 설명 |
| --- | --- | --- |
| `backendSpecific.Ollama.model` | (필수) | Ollama 모델 이름 |
| `endpoint` | `http://127.0.0.1:11434` | 서버 루트, `/api`, `/v1` 모두 가능 |
| `api` | `native` | `native`=`/api/chat`(권장), `openai`=`/v1/chat/completions` |
| `apiKey` | `ollama` | openai 모드의 `Authorization` 값. 로컬 Ollama는 임의 값 |
| `temperature` | 0.2 | 0.1~0.2 권장 |
| `numCtx` | 8192 | Ollama 컨텍스트 창. native 모드에서 요청마다 `options.num_ctx`로 전달 |
| `numPredict` | 2048 | 응답 최대 토큰 (`openai`에서는 `max_tokens`) |
| `maxPromptChars` | 6000 | 지침+용어집+캐릭터+문맥+원문의 문자 수 상한 |
| `followingContext` | 4 | 번역 대상 뒤 원문 몇 줄을 참고로 보낼지 |
| `characterFile` | `characters.yaml` | 캐릭터 사전 파일 (없으면 생략) |
| `apiTimeout` | 300 | 요청 하나의 제한 시간(초) |
| `maxAttempts` / `retryWait` | 3 / 2 | 총 시도 횟수 / 재시도 대기(지수 증가, 최대 30초) |
| `onFailure` | `mark` | `mark`: 실패 줄 기록 후 계속, `stop`: 즉시 중단 |
| `minLengthRatio` | 0.2 | 원문 대비 너무 짧은 번역을 누락으로 판단 (0이면 끔) |
| `allowJapanese` | `[]` | 번역문에 일본어로 남겨도 되는 표기 |
| `common.gpt.numPerRequestTranslate` | 5 | 한 요청의 번역 대상 줄 수 (배치) |
| `common.gpt.contextNum` | 8 | 이전 문맥 줄 수 (원문+확정 번역) |
| `common.gpt.translation_guideline` | `JapaneseToKorean.md` | 번역 지침 파일 |
| `common.workersPerProject` | 1 | 동시 요청 수. 파일 단위 병렬. GPU 1장에서는 1 |
| `common.splitFile` | `"no"` | 필수. 파일 내부 순서·문맥 보장 |
| `plugin.file_vn_scene_txt.*` | | 인코딩, 화자/제외 정규식 |

### 컨텍스트 창 맞추기

GalTransl 쪽 예산(`maxPromptChars`, 배치, 문맥 줄 수)과 Ollama 쪽 창(`numCtx`)은 별개이므로 함께 맞춰야 합니다.
일본어·한국어는 대략 1글자가 0.5~1토큰이므로 `maxPromptChars`(문자) + `numPredict`(토큰)가 `numCtx`보다
충분히 작게 유지하세요. 기본값 6000자 + 2048토큰은 8192 창에 맞춘 값입니다. `numCtx`를 16384로 올리면
`maxPromptChars`를 12000 정도까지 올릴 수 있지만 KV 캐시 메모리도 늘어납니다.

- 프롬프트가 예산을 넘으면 배치를 줄이고 오래된 이전 문맥 → 먼 이후 문맥 순으로 덜어냅니다. 원문은 자르지 않으며,
  한 줄조차 들어가지 않으면 줄 번호와 함께 오류로 중단합니다.
- Ollama가 응답 길이 초과(`done_reason: length`)를 보고하거나 입력 토큰(`prompt_eval_count`)이 `numCtx`에 도달하면
  잘린 것으로 보고 실패 처리합니다. 같은 배치가 반복 실패하면 배치를 절반씩 줄여 다시 시도합니다.
- `openai` 모드는 요청에서 `num_ctx`를 지정할 수 없어 서버나 Modelfile의 설정을 따릅니다. 이 모드를 쓸 때는
  Modelfile의 `PARAMETER num_ctx 8192` 등으로 맞추세요. 특별한 이유가 없으면 `native`를 권장합니다.

### RTX 3070 8GB + 26B급 모델

26B급 모델은 4비트 양자화에서도 8GB VRAM을 크게 넘으므로 Ollama가 일부 계층을 시스템 RAM/CPU로 나눠 실행합니다.
`ollama ps`의 PROCESSOR 열(예: `55%/45% CPU/GPU`) 또는 `check_environment.ps1 -TestChat`의 GPU 비율로 확인합니다.
CPU 비중이 클수록 느려지며 장시간 실행이 필요할 수 있습니다. 동시 요청은 1(`workersPerProject: 1`)을 유지하세요.
`numCtx`를 키우면 KV 캐시가 늘어 GPU에 올라가는 계층이 줄어들 수 있습니다.
속도 수치는 실제 PC에서 측정해야 하며 이 문서는 수치를 보장하지 않습니다.

## 번역 지침, 용어집, 캐릭터 사전

- **`JapaneseToKorean.md`**: 대사(구어체, 말투·존대 유지), 지문(소설체, 시점 유지, 생략·요약 금지),
  성인 대상 장면(검열·순화·생략 금지, 거절 문구 금지), 공통 규칙(누락·순서 변경 금지, 용어집 우선, 제어문자 보존)을
  담은 한국어 지침입니다. 프로젝트 폴더의 파일을 고치면 다음 실행부터 적용됩니다. 기본 원본은
  `translation_guidelines/JapaneseToKorean.md`입니다. 프로젝트 폴더에 `translation_guideline.md`(GalTransl의
  프로젝트 규범 파일)가 있으면 지침 뒤에 "프로젝트 추가 지침"으로 덧붙습니다.
  JSON 입출력 형식 규칙은 응답 검증과 맞물려 있어 코드(`GalTransl/Backend/OllamaPrompts.py`)에 있습니다.
- **`glossary.txt`**: GalTransl GPT 사전 형식(`원어<TAB>번역<TAB>설명`). 현재 요청 원문에 등장하는 항목만 전송됩니다.
- **`characters.yaml`**: `ja`(필수), `ko`, `aliases`, `personality`, `speech`, `honorifics`, `relationships`, `note`.
  현재 요청의 화자이거나 번역 대상·이전/이후 문맥에 이름(또는 별칭)이 나온 인물만 전송됩니다.

## 문맥 관리

- 장면 파일은 `splitFile: "no"`로 파일 단위로 처리하며, 엔진이 파일 안을 순서대로 배치(기본 5줄)로 나눕니다.
  전체 장면을 한 번에 보내지 않으므로 수천 줄 장면도 처리할 수 있습니다.
- 매 요청: 이전 문맥 = 최근 8줄의 원문과 **검증된 한국어 번역**, 번역 대상 = 5줄, 이후 문맥 = 다음 4줄 원문.
  이전·이후 문맥은 참고용이며 응답에는 번역 대상만 포함됩니다.
- 캐시 재개 시에도 이전 문맥을 캐시에서 복원합니다. 실패한 줄은 문맥에 넣지 않습니다. 다른 파일의 문맥은 섞지 않습니다.
- 장기 문맥(장면 요약)은 아직 구현하지 않았습니다. 캐릭터 사전과 지침의 "프로젝트 추가 지침"에 인물 관계·현재 상황을
  적는 방식으로 먼저 운영하고, 실제 번역 품질상 필요할 때 요약 기능을 추가하는 것을 권장합니다.

## 검증, 재시도, 품질 검사

번역 중(치명적이면 같은 배치를 재시도):
JSON 구조, ID·개수·순서, 빈 번역, 일본어 가나 잔류, 한국어 없음, 중국어 출력 의심, 제어 표기·줄바꿈·「」『』 괄호 불일치,
화자 이름 접두사 추가, 번역 거절·안내 문구(원문에 근거가 없는 경우만), 원문 대비 지나치게 짧은 번역(누락 의심),
코드블록·추론 텍스트 혼입. HTTP 408/429/5xx와 통신 오류는 제한 횟수만 재시도하고, 400/404 같은 설정 오류는 즉시 중단합니다.
같은 배치가 반복 실패하면 배치를 절반으로 줄이고, 한 줄도 실패하면 `onFailure`에 따라 기록 후 계속하거나 중단합니다.
통신 오류가 계속되면(서버 중지 등) 줄을 실패로 표시하지 않고 중단합니다.

번역 후 품질 리포트:

| 수준 | 항목 |
| --- | --- |
| 치명적 | 번역 누락, 실패 줄, 원문 변경 후 미번역, 위 번역 중 검사 항목, 출력 파일 없음/줄 수 불일치/제외 줄 변경/화자 형식 손상 |
| 경고 | 원문에 없는 한자 포함, 짧거나 긴 번역, 직전 줄과 같은 번역(중복 의심) |

경고는 정상 번역일 수 있으므로 사람이 확인합니다. 의도적으로 남긴 일본어 표기는 `allowJapanese`에 등록합니다.
문장 의미·말투의 정확성은 자동 검사로 보장할 수 없습니다.

## 9. 성능 실험

```bat
.venv\Scripts\python.exe benchmark_ollama_ko.py projects\mygame --lines 80 ^
  --case A:-:5:8192 --case B:-:10:8192 --case C:작은모델이름:10:8192
```

케이스 형식은 `이름:모델:배치:numCtx`이며 모델 `-`는 config.yaml의 모델입니다. 각 케이스는 프로젝트 입력의 앞부분
N줄(번역 대상 기준)을 `ollama_ko_logs\benchmark\<시각>\<케이스>\`에 복사해 실행하므로 원래 프로젝트의 캐시와 출력은
건드리지 않습니다. 결과 `benchmark.md`/`benchmark.json`에는 모델, 줄 수, 총 시간, 줄/분, API 호출 수, 재시도,
배치 축소, 입력/출력 토큰(Ollama `prompt_eval_count`/`eval_count`), 오류·실패·누락 줄 수, 품질 경고 수,
GPU 적재 비율(`/api/ps`), `nvidia-smi` 스냅숏이 기록됩니다.

## GalTransl 기능 조사 결과 (원본 `64a2f84` 기준)

| 요구 기능 | GalTransl 기존 기능 | 이 Fork에서 한 일 |
| --- | --- | --- |
| OpenAI 호환 API | 있음(OpenAI 토큰 풀, 중국어 프롬프트 중심) | 독립 `Ollama-ko` 엔진: native/OpenAI 호환 둘 다 |
| 일본어→한국어 | `language: ja2ko` 표기 지원. 기존 엔진 프롬프트·지침은 중국어 출력용 | 한국어 전용 지침과 입출력 계약 |
| TXT 입력 | `file_plaintext_txt`(줄 앞뒤 공백 제거, 화자 미분리, 빈 줄도 번역 대상) | `file_vn_scene_txt` 플러그인 추가 |
| 파일 내부 배치 | 있음(`numPerRequestTranslate`, `splitFile`) | 순차 배치와 문자 예산, 실패 시 배치 축소 |
| 이전 문맥 | 엔진별 이전 번역 전달 | 원문+검증된 번역 쌍, 캐시 재개 시 복원 |
| 이후 문맥 | 없음 | `followingContext` 추가 |
| 사전 | 번역 전/후 사전, GPT 사전, 이름 치환표 | GPT 사전을 용어집으로 사용, 캐릭터 사전 추가 |
| 캐시·중간 저장·재개 | 있음(줄 단위 append 캐시) | 그대로 사용, 설정 지문으로 무효화 |
| 재시도 | 엔진별 | 상한 있는 재시도와 오류 분류 |
| 실패 기록·재번역 | `(Failed)` 표기와 `retranslFail` | 같은 표기 사용 + 실패 로그 파일 |
| 결과 검증 | 문제 플러그인(중국어 기준 항목 포함) | 한국어 전용 검증과 품질 리포트 |

### 한국어 지원 확인 내용

- `language`는 GalTransl에서 `원본2대상` 형식입니다. `ko`만 쓰면 원본도 한국어로 해석되므로 `ja2ko`를 사용합니다.
  `Ollama-ko`는 `ja2ko`(또는 `ko`)만 허용하며 실제 번역 방향은 일본어→한국어로 고정됩니다.
- `Ollama-ko`는 기존 중국어 엔진 프롬프트와 기본 지침(`Basic.md`, `日译中_*`)을 사용하지 않습니다. 이 지침을
  `gpt.translation_guideline`에 지정하면 오류로 중단합니다. GalTransl 프로젝트 규범의 중국어 머리말 대신 한국어 머리말을 씁니다.
- 원본의 중국어 기본 사전(`00通用字典_*`, `GPT字典.txt` 등)과 중국어 번역 지침(`日译中_*.md`)은 이 Fork에서 삭제했습니다. 다른 곳에서 가져와 설정에 넣으면 `Ollama-ko`가 경고합니다. `Dict/`에는 빈 한국어 공통 사전(`공통GPT사전.txt`)만 있습니다.
- 중국어 텍스트 플러그인과 문제 플러그인(`problemPlugins`)은 비활성화하고 한국어 검증으로 대체합니다.
  간체/번체 변환(OpenCC)은 대상 언어가 중국어일 때만 기존 엔진에서 동작하며 이 엔진과 무관합니다.
- 「」 대사 괄호 분리·복원은 GalTransl의 JSON 플러그인 처리와 TXT 플러그인 모두에서 언어와 무관하게 동작합니다.

## 알려진 제약과 개선 가능 사항

- **미검증**: 실제 Ollama 모델 번역 품질, 26B 모델의 속도·메모리, Windows에서 `.cmd`/`.ps1` 실행.
  `.ps1`은 Linux의 PowerShell 7로 구문 분석과 Mock 서버 점검만 확인했습니다(Windows PowerShell 5.1 미확인).
- 실제 게임 스크립트는 형식이 다양합니다. 처음에는 장면 하나에서 50~100줄로 시험하고 `quality_report.md`와
  출력 파일을 직접 비교하세요. 확인할 것: 화자 표기 방식, 명령/주석 줄, 한 대사가 여러 줄에 걸치는 경우
  (현재는 줄마다 독립 번역), 루비·특수 태그, 원본 인코딩. 필요하면 정규식 설정을 조정합니다.
- 게임 엔진으로의 재삽입(패치)은 이 도구의 범위가 아닙니다. 출력은 원본과 같은 줄 구조의 TXT입니다.
- 장면 요약 기반 장기 문맥, 의미 수준의 누락 검출(문장 정렬), GUI 설정 화면은 구현하지 않았습니다.
- 품질 검사의 중국어·누락·거절 판단은 휴리스틱입니다. 오탐이 있으면 `minLengthRatio`, `allowJapanese`로 조정합니다.
- 캐시 식별자에 설정·지침·사전이 포함되어 있어, 지침을 조금만 고쳐도 전체 재번역이 일어납니다.

## 개발자용: Mock 검증

```sh
.venv/bin/python -m pytest -q tests/test_ollama_ko.py tests/test_ollama_ko_integration.py \
  tests/test_ollama_ko_cli.py tests/test_ollama_ko_scene.py
```

테스트는 임시 loopback 포트에 Ollama Mock 서버를 띄워 실제 HTTP 직렬화, 파일 입출력, 캐시 재개, 실패 처리,
품질 리포트, 벤치마크를 실행합니다. Mock의 정해진 응답은 번역 품질의 증거가 아닙니다.
기능별 기록: [`development/OLLAMA_KO_TEST_RESULTS.md`](development/OLLAMA_KO_TEST_RESULTS.md)
