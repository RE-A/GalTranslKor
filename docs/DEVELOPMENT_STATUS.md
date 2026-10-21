# 개발 상태 및 다음 작업

최종 갱신: 2026-10-21 (Asia/Seoul)

## 저장소와 환경

- 개발 Fork: `RE-A/GalTranslKor`; 원본: `GalTransl/GalTransl` (Push 대상 아님)
- 현재 통합 브랜치: `main`; 완료된 기능 브랜치: `feature/ollama-ko-translation` (보존)
- 2차 확장 브랜치: `claude/repo-commit-access-check-p1n66r` (Claude Cloud 세션이 지정한 개발 브랜치,
  `main` `6f02a04`에서 시작). 사용자가 "새 PR 없이 main에 올려 달라"고 요청해 PR 없이 Fork `main`에
  fast-forward로 반영함(`ea3fe90` Ollama 2차 확장, `81bc56c` 한국어화, 이 기록 커밋). 브랜치는 보존.
- PR: [RE-A/GalTranslKor #1](https://github.com/RE-A/GalTranslKor/pull/1)
  (`feature/ollama-ko-translation` → Fork의 `main`), 사용자 명시 요청으로 병합 완료.
- 병합 커밋: `a3106718d81ae0f95a76d0fe3b1efc03aa552530` (2026-10-21 15:33 KST).
- 구현 기준 커밋: `64a2f846511d73cf283d95ce6156a0ca7c04b2ab`
- 주요 구현 커밋: `a406021` (백엔드), `8e4715b` (Windows 실행/샘플),
  `afde31c` (리뷰 수정 및 검증 기록)
- 공통 개발 문서 커밋: `9b5362d`; 이후 문서 갱신은 현재 브랜치의 `git log`로 확인.
- 1차 작업 환경: Codex Cloud Linux, Python 3.11.17, Node.js 24.19.0
- 2차 작업 환경: Claude Cloud Linux, Python 3.11 `.venv`(세션에서 새로 생성), PowerShell 7.4.6 임시 설치(구문/Mock 점검용)
- 앞으로 사용할 환경: Codex Cloud, Claude Cloud, 로컬 Windows Codex.
  각 작업 시작 시 실제 환경과 Git 상태를 다시 확인할 것.

## 구현 완료

- `Ollama-ko` 엔진과 기존 GalTransl 작업/파일 플러그인 연결. 기본 엔진은 기존
  `auto-translate`로 유지.
- Ollama native `/api/chat`와 OpenAI 호환 `/v1/chat/completions` 지원.
- 한국어 전용 프롬프트, 대사·지문/화자 정보, 용어집 반영.
- 문장 수·문자 예산 기반 순차 배치, 최근 원문·번역 문맥, 파일별 격리.
- JSON ID·순서·개수·한국어·일본어 가나 잔류·변수/제어 표기·줄바꿈 검증.
- 제한된 재시도, 실패 출력 미저장, 기존 캐시 재개 및 설정/용어집 변경 시 무효화.
- 실패·취소 시 HTTP 클라이언트와 백그라운드 진행 작업 정리.
- `run_ollama_ko.py`, Windows `setup_ollama_ko.cmd`/`run_ollama_ko.cmd`,
  합성 24항목 샘플과 설정, [한국어 사용법](../README_KO_OLLAMA.md).
- 공통 [AGENTS.md](../AGENTS.md), Claude 진입 문서, 번역 정책과 이 상태 문서.
  기존 `/docs` 제외 규칙은 두 공통 문서만 추적하도록 제한적으로 조정.
- 실제 입력·모델·캐시·출력에 대한 Git 제외 규칙 강화. 기존 추적 파일/원본 구조 보존.

### 2차 확장 (2026-10-21, Claude Cloud)

원본 최신 `main`(`64a2f84`)이 Fork에 포함된 것을 확인한 뒤, 사용자 요구사항(장면 TXT, 한국어 지침 파일,
슬라이딩 윈도우, 캐릭터 사전, 안정성, 품질 검사, 성능 측정, PowerShell)에 맞춰 최소 확장했다.

- `plugins/file_vn_scene_txt`: 장면 TXT 파일 플러그인. 줄 구조·BOM·CRLF 보존, 화자/「」 분리,
  비번역 줄 통과, UTF-8/UTF-16/Shift-JIS 자동 판별. 기존 `file_plaintext_txt`는 변경하지 않음.
- `translation_guidelines/JapaneseToKorean.md`: 대사·지문·성인 장면·공통 규칙 한국어 지침.
  `common.gpt.translation_guideline`(원본 키)으로 선택, 프로젝트 사본 우선, 원본 프로젝트 규범 파일 덧붙임,
  중국어 지침 지정 시 오류. JSON 계약은 `OllamaPrompts.py`에 유지.
- `OllamaTranslate.py`: 이후 문맥(`followingContext`), 캐릭터 사전(`characterFile`, 등장 인물만 전달),
  반복 실패/컨텍스트 초과 시 배치 절반 축소, `onFailure: mark|stop`(기본 mark: `(Failed)` 표기 +
  `ollama_ko_logs/failures-*.jsonl`), 토큰·시간·재시도 통계 `stats-*.json`, openai 모드 `apiKey`,
  중국어 기본 사전 지정 경고. 캐시 계약 버전 1→2(이전 캐시는 재번역됨).
- `OllamaQuality.py`: 엔진과 리포트가 공유하는 검증. 거절 문구, 중국어 출력, 과도한 축약, 괄호 손실,
  화자 접두사를 치명적 오류로, 한자·길이·중복을 경고로 구분. `allowJapanese` 예외.
- `GalTransl/OllamaKoTools.py`, `check_ollama_ko.py`: 프로젝트 초기화(`run_ollama_ko.py --init`)와
  품질 리포트(`ollama_ko_logs/quality_report.md/json`). 실행기는 번역 후 자동 검사, 치명 오류 시 종료 코드 2.
- `benchmark_ollama_ko.py`: 발췌 N줄로 케이스(A/B/C) 실행, 시간·호출·토큰·재시도·실패·누락·GPU 비율 표.
- `scripts/check_environment.ps1`, `scripts/start_translation.ps1`(UTF-8 BOM): 환경 점검과 실행.
- `examples/ollama_ko_scene`: 합성 59줄 장면 TXT, 설정(배치 5/이전 8/이후 4/온도 0.2/numCtx 8192/worker 1),
  용어집, 캐릭터 사전. 실행기 기본 프로젝트를 이 예제로 변경. `**/ollama_ko_logs/` Git 제외.
- README_KO_OLLAMA.md 전면 갱신(설치~재개~모델 변경~설정, 기능 조사표, 한국어 확인 내용, 제약).

### 한국어화 (2026-10-21, Claude Cloud)

- 데스크톱 UI: `desktop/src/i18n/locales/ko/` 한국어 언어팩 7개(1,854개 원본 키 + `settings:appearance.korean`, 전부 채움).
  기본 UI 언어 `ko`, 대체 순서 ko → en → zh-CN. 설정 화면에 한국어 선택지 추가, 한국어 UI의 새 프로젝트 마법사는
  대상 언어 `ko`와 `JapaneseToKorean.md`를 기본 선택. `check-i18n.mjs`가 en과 ko를 모두 검사.
  파일 이름(`Basic.md` 등), 백엔드 문제 이름(`残留日文` 등), 설정 실제 값은 실제 값과 일치해야 하므로 번역하지 않음.
- 백엔드: `GalTransl/i18n.py` 사용자 메시지 59개와 번역 템플릿 설명(`TRANSLATOR_SUPPORTED`) 14개에 `ko` 추가.
  기본 `GT_LANG=ko`(환경 변수로 `zh-cn`/`en` 전환), 한국어가 없는 메시지는 en → zh-cn 대체. 서버의 템플릿 설명도 `GT_LANG`을 따름.
- 문서: `README.md`를 한국어로 번역(중국어 원본 `README_ZH.md`는 이후 삭제, 원본은 upstream 저장소 참조).
  `desktop/README.md`, `desktop/src/i18n/README.md`, `plugins/readme.md`, `plugins/SETTINGS_SCHEMA.md` 한국어화.
- 원본 테스트 보존: 원본 테스트는 중국어 문구를 검증하므로 pytest는 `tests/conftest.py`에서 `GT_LANG=zh-cn`,
  프런트엔드 테스트 로더는 저장된 UI 언어 `zh-CN`을 기본 제공. 한국어 기본값·대체 순서는 별도 테스트
  (`tests/test_korean_defaults.py`, `desktop/tests/i18n.test.mjs`)로 검증.
- 남은 중국어: 백엔드 코드에 하드코딩된 로그 문구(LOGGER 70여 곳), 내장 플러그인 YAML의 Name/Description
  (UI에서는 한국어 언어팩이 덮어씀, CLI·로그에는 원문 표시), 기본 중국어 사전·지침 파일(데이터/모델 입력이라 번역 대상 아님),
  `sampleProject` 설정 주석, 코드 주석.

## 중국어 잔여분 정리 (2026-10-21, Claude Cloud)

사용자 선택 범위: "사용자 메시지 번역" + "중국어 전용 데이터 삭제". 코드 주석 번역과 Git 이력 재작성은 하지 않음.

- 삭제: `README_ZH.md`, 중국어 기본 사전 5개(`Dict/00通用字典_*`, `01H字典_*`, `GPT字典.txt`), 중국어 지침
  `translation_guidelines/日译中_增强*.md`, 중국어 예제 `sampleProject/`, 일본어→중국어 평가 데이터
  `plugins/file_mtbench_aio/gal_mtbench_data/`. `Dict/`는 빌드·배포 검사가 비어 있지 않은 폴더를 요구하므로
  빈 한국어 공통 사전 `Dict/공통GPT사전.txt`(주석만)를 둠. Git 이력에는 남아 있어 저장소 크기는 줄지 않음.
- 새 프로젝트 기본 설정(`GalTransl/DefaultProjectConfig.py`): 주석 한국어화, 기본 대상 언어 `ko`,
  기본 지침 `JapaneseToKorean.md`, 삭제한 중국어 사전 참조 제거.
- 번역한 사용자 메시지: 백엔드 로그·예외·서버 오류 응답·진행 단계·CLI/빌드 스크립트 출력, 플러그인 로그,
  플러그인 YAML(이름·설명·라벨·주석), msg-tool README, Rust 데스크톱 셸 오류 문구, 데스크톱의 지침 예시와
  에이전트 추천 지시 칩. 서버의 "AI로 이름 번역" 프롬프트를 중국어 표기에서 한국어(한글) 표기로 변경.
- 화면이 백엔드 문자열을 비교하던 곳 보정: 서버 로그 필터(`Runner._ALLOWED_INFO_PREFIXES`)에 한국어 접두사 추가,
  `ProjectTranslatePage`의 가용성 확인 단계 비교에 한국어 값 추가, 완료 알림 플러그인의 성공 판별 문구 동기화.
- 일부러 유지한 중국어(실제 동작 값): 문제 이름과 문제 상세 문자열(`残留日文`, `翻译失败` 등, 캐시·필터·재번역 키워드와 비교),
  플러그인 설정 키와 선택값(`换行模式: 保持位置` 등), 파일 이름(`name替换表.csv`, `项目GPT字典*.txt`),
  `i18n.py`/`TRANSLATOR_SUPPORTED`/`zh-CN` 언어팩의 중국어 선택용 항목, msg-tool JIS 치환표 `subs_cn_jp.json`,
  모델 입력(GenDic·Sakura·ForGal 프롬프트와 ForGal-tool 도구 결과, `GalTransl/Agent/` 전체), 코드 주석.
- 테스트: 원본 테스트 중 바뀐 문구를 직접 비교하던 19개 테스트(서브테스트 포함 39건)의 기대값을 한국어로 갱신.
  Rust 테스트 3곳의 기대 문구도 갱신(이 환경에서는 crate가 없어 `cargo test` 미실행, `rustfmt`로 구문만 확인).
- 남은 일: GenDic(GPT 사전 자동 생성)은 프롬프트가 중국어 번역어를 만들도록 설계되어 한국어 용어집을 만들려면
  프롬프트 재설계가 필요. 에이전트 모드도 시스템 프롬프트가 중국어라 답변 언어 확인과 한국어화 검토 필요.
  백엔드 코드 주석과 CSS/Rust 주석은 중국어 그대로.

## 검증 결과

중국어 잔여분 정리(Claude Cloud): 전체 Python **1542 passed, 7 skipped(기존과 동일), 371 subtests passed**,
`npm test` **148 passed**, `npm run build` 성공, `npm run i18n:check` 오류 0, 플러그인 YAML 전부 `yaml.safe_load` 통과,
Rust `main.rs`/`backend.rs`는 `rustfmt` 구문 검사만 통과(`cargo check`/`cargo test`는 오프라인 crate 부재로 미실행).

한국어화(Claude Cloud): 전체 Python **1542 passed, 7 skipped, 371 subtests passed**, 프런트엔드 `npm test`
**148 passed**, `npm run build` 성공(기존 큰 청크 경고), `npm run i18n:check` 1854개 키(en/ko) 오류 0.
Vite 개발 서버 + 실제 백엔드를 띄워 Chromium으로 홈/설정 화면이 한국어로 표시되고 백엔드 템플릿 설명이 한국어로 오는 것을 확인
(확인용 한글 글꼴은 저장소 밖에 임시 설치). Windows 데스크톱(Tauri) 빌드에서의 표시는 미검증.

2차 확장(Claude Cloud): 신규 포함 Ollama Mock 테스트 **76 passed**, 전체 Python
**1538 passed, 7 skipped(기존과 동일), 371 subtests passed**. PowerShell 스크립트는 Linux pwsh 7.4.6에서
구문 오류 0, `check_environment.ps1`을 Mock 서버로 실행해 서버/모델 점검 경로 확인. 프런트엔드는 변경 없음.
상세: [검증 기록](../development/OLLAMA_KO_TEST_RESULTS.md)의 "2차 확장 검증".

아래 표는 `afde31c`에 포함된 1차 구현을 Codex Cloud에서 실행한 결과다.
그 이후 공통 지침/상태 문서와 ignore 규칙 변경은 문서 링크·Git 추적 여부를 검증한다.

| 검증 | 결과 |
| --- | --- |
| 신규 Ollama Mock 테스트 | 53개 통과, 건너뜀 없음 |
| 전체 Python 테스트 | 1515 passed, 7 skipped, 370 subtests passed |
| 프런트엔드 테스트 | 147개 통과 |
| TypeScript/Vite 빌드 | 성공, 기존 큰 청크 경고 있음 |
| 다국어 검사 | 1853개 키, 오류 0 |
| Python 의존성 검사 | 59개 패키지 호환성 통과 |
| 독립 코드 리뷰 | 중요 지적 3개를 재현 테스트 추가 후 수정 |
| 공통 문서/ignore 규칙 | 문서 4개와 상대 링크 유효, 비공개/생성 경로 14개 제외 확인, 합성 샘플 추적 가능 |

기존 skip 7개: Windows msg-tool 필요 6개, 플랫폼별 httpx/OpenAI close 동작 1개.
120항목 장면의 40배치 처리, 캐시 재실행 추가 호출 0, 실패 후 문맥 복원,
공백/한국어 경로의 실행기 subprocess까지 확인했다.
명령과 기능별 범위: [상세 검증 기록](../development/OLLAMA_KO_TEST_RESULTS.md).

## 미검증 / 남은 작업

Cloud 구현·Mock 검증·커밋/Push·Fork 내부 PR 생성과 사용자 요청에 따른 병합을 완료했다.
향후 PR도 사용자 요청 없이 병합하지 않는다. 이 문서의 테스트 결과는 Cloud에서 직접 실행한 결과로,
GitHub Actions의 별도 결과를 의미하지 않는다.

다음은 **로컬 Windows에서만** 수행한다. Cloud 작업을 막는 선행 조건은 아니다.

1. Python 3.11 및 설치된 Ollama 모델로 Windows `.cmd`·`.ps1`(Windows PowerShell 5.1 포함)의 최초 설치/실행 확인.
   `check_environment.ps1 -TestChat`으로 실제 모델 응답·`/api/ps` GPU 비율 확인.
2. 실제 모델명만 샘플 설정에 넣고 native API 번역 실행. 모델/버전별 JSON·think
   옵션 지원, 길이 초과/타임아웃 동작 확인. 필요하면 OpenAI 호환 모드도 확인.
3. 한국어 번역 품질, 화자별 존대·말투·호칭·고유명사 및 긴 장면의 일관성 평가.
4. `benchmark_ollama_ko.py`로 A(26B/5줄/8192), B(26B/10줄/8192), C(작은 모델/10줄/8192)를 50~100줄로 실행해
   하드웨어·모델명/버전·컨텍스트·배치 설정과 GPU/VRAM·처리 속도를 측정.
   모델 파일·원문·번역 출력은 커밋하지 않고 필요한 집계 결과만 문서화.
5. 실제 게임 엔진의 추출/재삽입·제어코드·인코딩은 별도 승인된 작업에서 검증.
6. 실제 장면 TXT의 화자 표기·명령 줄 형식에 맞게 `speakerPatterns`/`skipPatterns` 확인, 여러 줄 대사 처리 필요성 판단.
7. 실제 모델 출력으로 거절·중국어·누락 휴리스틱의 오탐/미탐 확인 후 `minLengthRatio` 등 기본값 조정.
8. 품질상 필요하면 장면 요약(장기 문맥) 기능 검토. 현재는 캐릭터 사전과 프로젝트 추가 지침으로 대체.

Mock 검증을 실제 모델의 품질/성능이나 Windows 네이티브 실행 성공으로 해석하지 않는다.
현재 전체 장면 영구 요약, GUI 전용 Ollama 설정 편집 화면, 게임별 패치 보장은 범위 밖이다.
Cloud에서 추가로 할 수 있는 일: 리뷰 반영, 여러 줄에 걸친 대사 결합 옵션(합성 fixture로 재현 후),
실제 Windows 검증 결과가 들어오면 기본값 조정.

## 다음 에이전트의 시작 순서

1. 루트 `AGENTS.md` → `docs/TRANSLATION_POLICY.md` → 이 문서를 읽는다.
2. 실제 브랜치/remote/작업 트리를 확인하고 문서에 없는 최신 변경을 조사한다.
3. Cloud에서는 기존 `.venv`로 Mock 테스트를 실행한다. Windows이면 이번 요청이
   실제 모델 검증인지 먼저 확인한다. 이전 프로세스/설치 경로가 남아 있다고 가정하지 않는다.
4. 요청된 작업을 마치면 이 문서에 환경·변경·실제 검증·미검증·다음 작업을 갱신하고
   같은 개발 브랜치에 커밋/Push한다. Fork 내부 PR을 유지하고 자동 병합하지 않는다.

## 작업 이력

- 2026-10-21 / Claude Cloud: 남은 중국어 사용자 메시지 번역과 중국어 전용 데이터 삭제(위 "중국어 잔여분 정리"). 같은 브랜치에 커밋 후 Fork `main`에 fast-forward 반영.

- 2026-10-21 / Claude Cloud: 사용자 요청으로 2차 확장·한국어화 커밋을 PR 없이 Fork `main`에 fast-forward 반영
  (강제 Push 없음, 원본 저장소 Push 없음). 반영 전 `main`은 `6f02a04`에서 변경 없음을 확인.

- 2026-10-21 / Claude Cloud: 사용자 요청으로 README·UI·백엔드 메시지 한국어화(위 "한국어화"). 같은 브랜치에 커밋/Push.

- 2026-10-21 / Claude Cloud: 커밋·Push 권한 확인(GitHub App 설치 후 지정 브랜치 Push 성공).
  사용자 요구사항에 따른 2차 확장 구현(위 "2차 확장"), Mock 76개·전체 1538개 통과, pwsh 구문 검사.
  브랜치 `claude/repo-commit-access-check-p1n66r`에 커밋/Push. PR은 사용자 요청 시 생성. 실제 모델/Windows 미검증.

- 2026-10-21 / Codex Cloud: Ollama 한국어 번역 구현, Mock/전체 회귀 테스트,
  독립 리뷰 수정 완료. `afde31c`까지 Fork 개발 브랜치에 Push.
- 2026-10-21 / Codex Cloud: 사용자 요청에 따라 Cloud/Windows/다른 AI 간 공통
  지침·번역 정책·상태 문서 및 Git 데이터 제외 정책을 추가. 문서 링크와 ignore 검증 통과.
  이 추가 변경은 문서/ignore만 포함하므로 Python 전체 테스트는 반복하지 않았으며,
  위 구현 테스트 결과를 유지한다. 실제 모델 연결은 수행하지 않음.
- 2026-10-21 / Codex Cloud: `9b5362d`까지 Fork에 Push하고 Fork 내부 PR #1 생성.
  마지막 상태/계획 갱신도 같은 브랜치에 반영. 원본 저장소 Push 및 PR 자동 병합 없음.
- 2026-10-21 / Codex Cloud: 사용자의 "병합해줘" 요청에 따라 PR #1을 Fork `main`에
  merge commit 방식으로 병합. GitHub API로 merged=true와 대상 저장소/커밋 확인.
  병합 트리는 검증된 PR 최종 커밋과 동일하며, 이번 후속 변경은 병합 상태 문서뿐이다.
  상태 문서를 `main`에 반영하고 기능 브랜치는 보존. 실제 모델/Windows 검증은 여전히 미수행.
