# 공통 개발 지침

이 지침은 Codex Cloud, Claude Cloud, 로컬 Windows Codex 등 저장소에서 작업하는
모든 개발 에이전트에 적용한다. 환경이나 이전 대화의 기억을 현재 상태로 가정하지 않는다.

## 작업 시작

1. 이 파일과 [번역 정책](docs/TRANSLATION_POLICY.md),
   [현재 개발 상태](docs/DEVELOPMENT_STATUS.md)를 먼저 읽는다.
2. `git status --short`, 현재 브랜치, 원격 저장소와 최근 커밋을 확인한다.
   기존 변경·미추적 파일·다른 개발자의 작업을 보존한다.
3. 실행 환경(OS, Python, 의존성, 권한)을 확인하고 기존 가상환경을 우선 사용한다.
   Cloud의 설치 경로나 실행 중인 프로세스가 다른 환경에도 있다고 가정하지 않는다.
4. 상태 문서의 남은 작업 중 현재 요청 범위를 진행한다. 실제 코드와 문서가 다르면
   확인한 근거로 상태 문서를 정정한다. 확인하지 않은 항목은 미검증으로 기록한다.

Claude용 진입 문서는 `CLAUDE.md`에서 이 공통 지침을 참조한다. 도구별 지침을
별도로 복제해 서로 다른 정책이 생기게 하지 않는다.

## 저장소와 브랜치

- 원본은 `https://github.com/GalTransl/GalTransl`, 개발 대상은 사용자 Fork
  `https://github.com/RE-A/GalTranslKor`이다. 원본에는 Push하지 않는다.
- 현재 기능 브랜치는 `feature/ollama-ko-translation`, PR 대상은 **Fork의 `main`**이다.
  다른 작업 브랜치를 사용하라는 요청이 있으면 그 요청을 따르고 상태 문서에 기록한다.
- Push/PR 전에 실제 remote와 대상 저장소를 확인한다. upstream으로 자동 선택되는
  도구 기본값에 의존하지 말고 `RE-A/GalTranslKor`를 명시한다.
- 사용자가 요청한 변경을 해당 개발 브랜치에 커밋하고 Fork에 반영한다.
  자동 병합, 강제 Push, 기존 변경 삭제는 하지 않는다.
- 기존 GalTransl 구조·파일 플러그인·캐시 형식을 최대한 보존한다. 관련 없는 대규모
  리팩터링이나 전체 파일의 줄바꿈/서식 변경을 피한다.

## 환경별 검증 경계

- **Cloud(Codex/Claude):** 실제 Ollama, 사용자 PC, 실제 모델에 연결하지 않는다.
  성능 벤치마크 대신 임시 loopback 포트의 HTTP Mock 서버로 기능을 검증한다.
  Cloud의 `127.0.0.1`은 사용자 Windows PC가 아니다.
- **로컬 Windows Codex:** 실제 Ollama 연결·모델 품질·GPU/VRAM·성능 검증을
  수행할 수 있는 환경이다. 현재 작업이 실제로 이 환경인지 먼저 확인한다.
  모델 다운로드·설정 변경 등은 해당 세션의 요청 범위 안에서 수행한다.
- Cloud에서 작업할 때 사용자에게 로컬 명령 실행, 게임 파일 제공, 모델 파일
  업로드를 요구하지 않는다. 실제 모델 없이 가능한 구현과 테스트를 끝낸다.
- Mock 통과와 실제 모델 통과를 명확히 구분한다. Windows 실행 스크립트를
  Linux에서 검토한 사실을 Windows에서 실행한 것으로 기록하지 않는다.

## 데이터와 Git

- 실제 게임 스크립트·추출 원문, 모델/가중치 파일, 번역 캐시·출력물, API 키·토큰을
  새로 커밋하지 않는다. 작업 데이터는 무시되는 `projects/` 또는 저장소 밖에 둔다.
- 테스트는 직접 작성한 합성 대사·지문을 사용한다. 명확히 합성임을 표시한 작은
  테스트 fixture와 `examples/ollama_ko/gt_input/rainy_station.json`은 커밋 가능하다.
  이 예외를 실제 게임 텍스트나 모델 산출물에 적용하지 않는다.
- `.gitignore`는 보조 수단이다. `git add .` 전에 변경 목록을 검토하고 가능하면
  파일을 명시해 추가한다. 커밋 전 staged diff에 실행 데이터·비밀값이 없는지 확인한다.
- 원래 저장소에 추적 중인 파일은 ignore 규칙만으로 제거되지 않는다. 기존 파일을
  일괄 삭제하거나 Git 이력을 재작성하지 않는다.

## 구현과 테스트

- Ollama 기능 사용법은 [한국어 README](README_KO_OLLAMA.md)를 참고한다.
  Python 3.11을 기준으로 기존 `requirements.txt`를 사용하며 테스트에는 pytest가 필요하다.
- Linux Cloud에서는 기존 `.venv/bin/python`, Windows에서는 `.venv\Scripts\python.exe`를
  사용한다. 의존성이 없으면 저장소의 설치 절차/`setup_ollama_ko.cmd`를 따른다.
- 핵심 Mock 테스트:
  `python -m pytest -q tests/test_ollama_ko.py tests/test_ollama_ko_integration.py tests/test_ollama_ko_cli.py tests/test_ollama_ko_scene.py`
- Python 동작 변경 후 `python -m pytest -q -ra`를 실행한다. 프런트엔드 변경이 있으면
  `npm --prefix desktop test`, `npm --prefix desktop run build`,
  `npm --prefix desktop run i18n:check`도 실행한다.
- 수정한 문제를 재현하는 테스트를 먼저 작성하고 실패·수정·성공을 확인한다.
  문서만 바꾸는 작업은 링크·상태 일관성·Git 제외 규칙을 확인한다.
- 테스트를 생략/비활성화하거나 검증을 완화해 통과시키지 않는다. 실패와 건너뜀의
  이유를 기록한다. 실행하지 않은 명령이나 모델 테스트를 성공으로 표시하지 않는다.

## 작업 종료와 인수인계

매 작업 종료 시 [DEVELOPMENT_STATUS.md](docs/DEVELOPMENT_STATUS.md)를 갱신한다.
날짜, 환경, 브랜치/관련 커밋, 완료 사항, 실제 실행한 테스트와 결과, 미검증 사항,
남은 작업·차단 요인, PR 링크를 기록한다. 미완료 작업은 다음 에이전트가 재개할 수
있게 구체적으로 남긴다. 이번 작업이 문서 변경뿐이라면 그 사실과 검증 범위를 적는다.

상태 문서도 구현과 같은 브랜치에 커밋한다. 마지막 보고에는 실제로 반영된 커밋/PR과
남은 검증을 구분하고, 사용자 요청 없이 PR을 병합하지 않는다.
