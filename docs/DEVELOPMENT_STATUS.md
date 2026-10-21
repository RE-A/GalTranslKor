# 개발 상태 및 다음 작업

최종 갱신: 2026-10-21 (Asia/Seoul)

## 저장소와 환경

- 개발 Fork: `RE-A/GalTranslKor`; 원본: `GalTransl/GalTransl` (Push 대상 아님)
- 현재 브랜치: `feature/ollama-ko-translation`
- PR 대상: Fork의 `main`; PR 생성은 현재 인수인계 문서 반영 후 진행 예정
- 구현 기준 커밋: `64a2f846511d73cf283d95ce6156a0ca7c04b2ab`
- 주요 구현 커밋: `a406021` (백엔드), `8e4715b` (Windows 실행/샘플),
  `afde31c` (리뷰 수정 및 검증 기록)
- 이번 작업 환경: Codex Cloud Linux, Python 3.11.17, Node.js 24.19.0
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

## 검증 결과

아래 결과는 `afde31c`에 포함된 구현을 Codex Cloud에서 실행한 결과다.
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

다음은 **로컬 Windows에서만** 수행한다. Cloud 작업을 막는 선행 조건은 아니다.

1. Python 3.11 및 설치된 Ollama 모델로 Windows `.cmd`의 최초 설치/실행 확인.
2. 실제 모델명만 샘플 설정에 넣고 native API 번역 실행. 모델/버전별 JSON·think
   옵션 지원, 길이 초과/타임아웃 동작 확인. 필요하면 OpenAI 호환 모드도 확인.
3. 한국어 번역 품질, 화자별 존대·말투·호칭·고유명사 및 긴 장면의 일관성 평가.
4. 하드웨어·모델명/버전·컨텍스트·배치 설정을 기록하고 GPU/VRAM·처리 속도를 측정.
   모델 파일·원문·번역 출력은 커밋하지 않고 필요한 집계 결과만 문서화.
5. 실제 게임 엔진의 추출/재삽입·제어코드·인코딩은 별도 승인된 작업에서 검증.

Mock 검증을 실제 모델의 품질/성능이나 Windows 네이티브 실행 성공으로 해석하지 않는다.
현재 전체 장면 영구 요약, GUI 전용 Ollama 설정 편집 화면, 게임별 패치 보장은 범위 밖이다.

## 다음 에이전트의 시작 순서

1. 루트 `AGENTS.md` → `docs/TRANSLATION_POLICY.md` → 이 문서를 읽는다.
2. 실제 브랜치/remote/작업 트리를 확인하고 문서에 없는 최신 변경을 조사한다.
3. Cloud에서는 기존 `.venv`로 Mock 테스트를 실행한다. Windows이면 이번 요청이
   실제 모델 검증인지 먼저 확인한다. 이전 프로세스/설치 경로가 남아 있다고 가정하지 않는다.
4. 요청된 작업을 마치면 이 문서에 환경·변경·실제 검증·미검증·다음 작업을 갱신하고
   같은 개발 브랜치에 커밋/Push한다. Fork 내부 PR을 유지하고 자동 병합하지 않는다.

## 작업 이력

- 2026-10-21 / Codex Cloud: Ollama 한국어 번역 구현, Mock/전체 회귀 테스트,
  독립 리뷰 수정 완료. `afde31c`까지 Fork 개발 브랜치에 Push.
- 2026-10-21 / Codex Cloud: 사용자 요청에 따라 Cloud/Windows/다른 AI 간 공통
  지침·번역 정책·상태 문서 및 Git 데이터 제외 정책을 추가. 문서 링크와 ignore 검증 통과.
  이 추가 변경은 문서/ignore만 포함하므로 Python 전체 테스트는 반복하지 않았으며,
  위 구현 테스트 결과를 유지한다. 실제 모델 연결은 수행하지 않음.
