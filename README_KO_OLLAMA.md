# GalTransl + Ollama 일본어 → 한국어 번역

이 Fork의 `Ollama-ko` 번역기는 일본어 대사와 지문을 한국어로 번역합니다.
GalTransl의 기존 파일 플러그인, 사전, 작업 실행기, 캐시와 출력 형식을 사용합니다.
Ollama SDK나 외부 API 키는 필요하지 않습니다.

## Windows에서 나중에 실행하기

아래 과정은 PC 사용이 가능해진 뒤를 위한 안내입니다. 현재 클라우드 개발에는
PC 접속, 게임 파일 또는 실제 모델이 필요하지 않습니다.

1. 이 Fork의 `feature/ollama-ko-translation` 브랜치를 내려받아 압축을 풉니다.
2. Python **3.11**(Windows Python Launcher 포함), Ollama와 일본어·한국어를 지원하는
   모델을 준비합니다. Ollama가 기본 주소 `http://127.0.0.1:11434`에서 실행 중이어야 합니다.
   모델 설치 자체는 이 저장소나 스크립트가 수행하지 않습니다.
3. [`examples/ollama_ko/config.yaml`](examples/ollama_ko/config.yaml)의
   `backendSpecific.Ollama.model`에 설치된 모델의 정확한 이름을 넣습니다.
   다른 기본 설정은 그대로 사용할 수 있습니다.
4. `run_ollama_ko.cmd`를 실행합니다. 처음에는 `setup_ollama_ko.cmd`를 호출해
   `.venv`와 Python 의존성을 설치합니다(최초 설치에는 인터넷 연결 필요).
5. 결과는 `examples/ollama_ko/gt_output/rainy_station.json`, 캐시는
   `examples/ollama_ko/transl_cache`에 저장됩니다. 중단되면 같은 명령으로 재개합니다.

의존성만 설치하려면 `setup_ollama_ko.cmd`를 실행합니다. 기본 샘플은 직접 작성한
24개 항목의 짧은 장면이며 실제 게임에서 추출한 내용이 아닙니다. 대사와 지문,
화자 전환, 앞선 대화의 약속을 뒤에서 참조하는 장면을 포함합니다.

별도 프로젝트를 사용할 때는 예제 폴더를 복사한 뒤 `gt_input`의 JSON을 교체합니다.
명령 프롬프트에서는 다음처럼 공백이 포함된 경로도 사용할 수 있습니다.

```bat
run_ollama_ko.cmd "D:\번역 작업\프로젝트"
```

입력 형식은 `[{"name":"葵","message":"おはよう。"},{"message":"朝日が差し込んだ。"}]`입니다.
`name`이 없으면 지문입니다. 화자 이름은 그대로 보존하며, 이름 번역이 필요하면
GalTransl의 이름 치환표/사전 기능을 사용합니다. 게임별 추출·재삽입은 해당 파일
플러그인의 별도 기능이며 이 JSON 샘플 검증만으로 게임 패치 호환성을 보장하지 않습니다.

## 연결과 설정

| 설정 | 기본값 / 역할 |
| --- | --- |
| `model` | 필수. Ollama에 설치된 모델명(태그 포함) |
| `endpoint` | `http://127.0.0.1:11434`; 다른 서버라면 주소 변경 |
| `api` | `native`: `/api/chat`; `openai`: `/v1/chat/completions` |
| `apiTimeout` | 180초, 한 HTTP 요청의 네트워크 타임아웃 |
| `maxAttempts` | 3회, 최초 요청 포함. 무한 재시도 없음 |
| `retryWait` | 1초부터 지수 백오프, 최대 30초 |
| `temperature` | 0.2 |
| `numCtx` | 8192, native 모드에만 `options.num_ctx`로 전달 |
| `numPredict` | 2048, 생성 토큰 상한 (`openai`에서는 `max_tokens`) |
| `maxPromptChars` | 6000, 시스템 프롬프트·JSON·문맥·용어집의 합계 문자 상한 |
| `think` | false, native 모드에서만 전달. null이면 파라미터 생략 |
| `common.gpt.numPerRequestTranslate` | 6개 문장/요청 상한 |
| `common.gpt.contextNum` | 최근 번역 8개를 원문·한국어 쌍으로 전달 |
| `common.splitFile` | 반드시 `"no"`. 요청 배치는 엔진에서 순차 분할 |
| `common.workersPerProject` | 1. 늘리면 파일끼리만 병렬 처리 |

`endpoint`는 서버 루트, `/api/chat`, `/v1`, `/v1/chat/completions` 형태를 받습니다.
별도 인증을 요구하는 원격 프록시는 이 기본 로컬 Ollama 구성의 대상이 아닙니다.
로컬 요청에 시스템 프록시를 자동 적용하지 않습니다.

문자 수는 토큰 수와 다릅니다. 토크나이저는 모델마다 다르므로 실제 모델의 창 크기와
VRAM에 맞게 `maxPromptChars`, 배치 수, `numCtx`, `numPredict`를 조절해야 합니다.
`openai` 모드는 Ollama 서버 측 컨텍스트 크기 설정을 사용합니다.
입력이 길면 배치를 줄이고 필요하면 오래된 문맥부터 제거하지만 원문은 자르지 않습니다.
단일 항목조차 들어가지 않으면 해당 줄 번호와 설정명을 포함한 오류로 중단합니다.
서버가 출력 길이 초과를 보고하면 성공으로 취급하지 않습니다.

용어집은 프로젝트 안의 UTF-8 탭 구분 파일에 `원어<TAB>한국어<TAB>설명`을 적고
`dictionary.gpt.dict: ["(project_dir)glossary.txt"]`로 연결합니다.
한국어 지침은 [`OllamaPrompts.py`](GalTransl/Backend/OllamaPrompts.py)에 있습니다.
일반 중국어 프롬프트/기본 번역 규범을 이 엔진에 섞지 않습니다.

## 검증·캐시·실패 처리

- 요청마다 JSON 항목 수, 정수 ID와 순서, 빈 출력, 일본어 가나 잔류,
  한국어 포함 여부를 검사합니다. 숫자·기호만 있는 원문에는 한글을 강제하지 않습니다.
- `{name}`, `%02d`, `[wait]`, `<tag>`, `\\n` 등 변수·제어 표기와 실제 줄바꿈을
  검사합니다. 모든 게임 엔진의 제어문법을 인식하는 것은 아닙니다.
- 한 배치 전체가 검증된 뒤에만 문장에 결과를 반영하고 기존 GalTransl 캐시에 기록합니다.
  실패한 배치는 캐시에 성공으로 저장하지 않습니다. 앞서 성공한 배치는 재개 시 복원됩니다.
- 408/429/5xx, 통신·타임아웃, JSON/내용 검증 오류는 제한 횟수만 재시도합니다.
  400/404 같은 설정·모델 오류는 즉시 종료합니다. 실행기는 실패 시 0이 아닌 종료 코드를 반환합니다.
- 모델·주소·프롬프트·용어집·생성/문맥 설정이 바뀌면 캐시 식별자가 달라져 재번역합니다.
  캐시 내용이 검증에 실패해도 재번역합니다. 입력 변경 여부는 기존 GalTransl 캐시 검사를 사용합니다.
- 캐시 결과를 포함한 직전 번역을 다음 배치의 문맥으로 사용합니다. 다른 파일의 문맥은 섞지 않습니다.
  장면의 전체 요약을 무한히 보존하는 기능은 아니며 설정한 최근 문맥만 전달합니다.
- 문장 내용의 의미·말투·정확성은 구조 검사로 보장할 수 없습니다. 실제 모델 품질 검토가 필요합니다.

샘플의 출력·캐시·이름표와 `.galtransl-data`는 Git에서 제외됩니다.
독립 실행기는 기존 `GALTRANSL_DATA_DIR` 설정이 없으면 프로젝트의 `.galtransl-data`에
앱 데이터를 저장하므로 현재 작업 폴더나 사용자 홈의 쓰기 권한에 의존하지 않습니다.

## Codex Cloud에서 Mock 검증

설정은 기존 `.venv`와 `requirements.txt`를 사용하며 테스트 도구는 pytest입니다.

```sh
.venv/bin/python -m pytest -q tests/test_ollama_ko.py tests/test_ollama_ko_integration.py tests/test_ollama_ko_cli.py
.venv/bin/python -m pytest -q
```

테스트는 임시 포트에 `ThreadingHTTPServer` 기반 Ollama Mock 서버를 띄웁니다.
실제 HTTP 직렬화, 한국어 응답 처리, 파일 출력과 캐시 재개를 실행하지만 실제 Ollama나
사용자의 PC로 연결하지 않습니다. Mock의 정해진 한국어 응답은 모델 번역 품질의 증거가 아닙니다.

기능별 결과는 [`development/OLLAMA_KO_TEST_RESULTS.md`](development/OLLAMA_KO_TEST_RESULTS.md)에 기록합니다.
실제 모델의 한국어 품질, GPU/VRAM·속도, Windows `.cmd`의 네이티브 실행은 별도 검증 항목입니다.
