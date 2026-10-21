# Ollama 한국어 번역 검증 기록

검증일: 2026-10-21. Codex Cloud Linux, Python 3.11.17, Node.js 24.19.0.
개발 기준: `RE-A/GalTranslKor`의 `64a2f846511d73cf283d95ce6156a0ca7c04b2ab`.
작업 브랜치: `feature/ollama-ko-translation`.

## 실제 실행 결과

| 명령 | 결과 |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/test_ollama_ko.py tests/test_ollama_ko_integration.py tests/test_ollama_ko_cli.py` | **53 passed**, 26.81초 |
| `.venv/bin/python -m pytest -q -ra` | **1515 passed, 7 skipped, 370 subtests passed**, 62.67초 |
| `npm --prefix desktop test` | **147 passed**, 실패·건너뜀 없음 |
| `npm --prefix desktop run build` | TypeScript 검사 및 Vite 빌드 성공 |
| `npm --prefix desktop run i18n:check` | 1853개 키 검사, 오류 0 |
| `uv pip check --python .venv/bin/python` | 설치된 59개 패키지 호환성 검사 통과 |
| `.venv/bin/python run_ollama_ko.py --help` | 정상 종료 |

Python 건너뜀 7개는 기존 테스트입니다: Windows msg-tool 바이너리가 필요한
6개와 현재 httpx/OpenAI 클라이언트의 플랫폼별 close 동작에 관한 1개입니다.
신규 Ollama 테스트는 건너뛰지 않았습니다. Vite의 기존 큰 청크(500 kB 초과)
경고는 남아 있으며 빌드는 성공했습니다.

## 기능별 검증 범위

| 기능 | 실제 검증 방법 |
| --- | --- |
| Ollama API | 임시 loopback HTTP 서버에 native `/api/chat` 및 OpenAI 호환 `/v1/chat/completions` 요청, JSON 직렬화와 응답 처리 |
| 한국어 프롬프트 | 실제 전송된 system 메시지와 원문·화자 구조 확인 |
| 대사·지문 혼합 | 직접 작성한 24개 항목 샘플을 실행기 subprocess → GalTransl 작업 → 파일 플러그인 → 출력까지 실행 |
| 긴 장면 | 120개 항목을 3개씩 40배치로 처리, 입력 순서·전체 출력 개수·캐시 재실행의 추가 호출 0 확인 |
| 문맥 유지 | 최근 원문·번역 쌍 전달, 문맥 수 제한, 캐시에서 재개한 직전 대사 복원 |
| 동시 파일 | 두 파일의 병렬 작업에서 다른 파일의 문맥이 섞이지 않음 확인 |
| 크기 제한 | 문장 수 및 시스템/입력/문맥/용어집 문자 상한; 개별 긴 줄의 명시적 실패; 용어집을 포함한 배치 축소 |
| 결과 검증 | 빈 값·잘못된 JSON·항목 누락·ID 중복/역순·일본어 가나 잔류·한글 없는 번역 거부 |
| 제어문자 | `{name}`, `%02d`, HTML 형태 태그, `[wait]`, 리터럴 `\\n`, 실제 줄바꿈의 정상 보존 및 손실 거부 |
| 응답 오류 | malformed envelope/choice, 출력 길이 초과, 미완료 응답의 재시도·한도 초과 및 정상 응답으로 회복 |
| 재시도 | 429/503 및 타임아웃의 제한 횟수 재시도; 400/404 즉시 실패; 실패 결과 미저장 |
| 캐시 | 기존 GalTransl 캐시 저장·재사용, 모델·설정·용어집 변경 및 잘못된 캐시 무효화 |
| 중단 복구 | 성공한 앞 배치만 보존한 실패 작업을 재실행해 남은 항목만 번역 |
| 취소/정리 | 요청 전·생성 중 취소, 실패/취소된 실제 작업에서 HTTP 클라이언트와 진행률 백그라운드 작업 종료 |
| 실행기 | 공백·한국어 경로, 현재 작업 폴더와 무관한 실행, 실패 시 nonzero 종료, 모델명이 없는 설정의 명시적 실패 |

Mock은 정해진 한국어 문자열을 반환합니다. 위 검증은 전송·처리·보존·실패 복구
기능의 증거이며 실제 LLM의 번역 정확도나 문학적 품질의 증거는 아닙니다.

## 리뷰 및 수정

독립 코드 리뷰에서 발견한 세 가지 문제를 먼저 실패하는 테스트로 재현한 뒤
수정했습니다: 실패/취소 시 클라이언트 정리 누락, 축소 전 전체 후보의 용어집이
예산을 차지하는 문제, null OpenAI choice가 재시도 처리를 벗어나는 문제.
수정 후 신규 기능 테스트와 전체 Python 테스트가 위 결과로 통과했습니다.
기존 기본 번역기가 `auto-translate`로 유지되는 회귀 테스트도 통과했습니다.

## 실제 모델/Windows에서 남은 검증

- 설치된 실제 Ollama 모델의 한국어 번역 정확도, 존대·말투·고유명사 일관성
- 모델/버전별 JSON 및 think 옵션 지원, 실제 컨텍스트 한계와 잘림 동작
- GPU/VRAM 사용량, 처리 속도, 모델 적재 시간에 맞는 타임아웃
- Windows에서 `.cmd` 실행과 최초 의존성 설치(파일은 CRLF로 작성)
- 실제 게임 엔진별 추출·재삽입 및 제어코드/인코딩 호환성

사용자의 PC나 실제 Ollama에는 접속하지 않았으며 실제 게임 파일을 사용하지
않았습니다. 위 미검증 항목을 Mock 통과 결과로 대체하지 않습니다.
