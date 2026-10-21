# GalTransl Desktop

이 폴더에는 GalTransl의 Tauri 데스크톱 셸과 React 프런트엔드가 있습니다. 화면 언어는 기본 한국어이며
설정에서 中文/English로 바꿀 수 있습니다([언어 리소스 안내](src/i18n/README.md)).

## 개발

1. 프런트엔드 의존성 설치:
   `npm ci`
2. 저장소 루트에서 Python 백엔드 시작:
   `python run_backend.py --host 127.0.0.1 --port 12333`
3. 프런트엔드 개발 서버 시작:
   `npm run dev`
4. Rust가 설치되어 있으면 데스크톱 셸 실행:
   `npm run tauri:dev`

Linux x86_64에서는 `../run_desktop_dev.sh`가 2-4단계를 수행하고, 데스크톱 프로세스가 끝나면
백엔드를 멈춥니다. 프런트엔드는 브라우저와 호환되며 HTTP로 Python 백엔드와 통신합니다.

- 프런트엔드는 일부러 브라우저 호환으로 만들었으며 HTTP로 Python 백엔드와 통신합니다.
- 패키지된 데스크톱 프로세스는 각자 `--port 0`으로 백엔드를 시작합니다. 운영체제가 바인딩할 때 포트를 고르며, 백엔드는 비공개 `--ready-file`로 실제 주소를 알리고, Tauri가 API 요청 전에 그 주소를 프런트엔드에 넘깁니다.
- 패키지된 창을 닫으면 그 창이 시작한 백엔드 프로세스 트리만 멈춥니다. 동시에 연 창은 백엔드가 따로 있습니다. 시작 실패와 시간 초과 때도 자기 자식 프로세스를 정리합니다.
- 개발 모드는 계속 `127.0.0.1:12333`의 외부 백엔드를 쓰며, 개발 창을 닫아도 그 백엔드는 계속 실행됩니다. `VITE_BACKEND_URL`로 명시적으로 덮어쓸 수 있습니다.
- 시작 핸드셰이크가 바뀌었으므로 이 변경을 패키징할 때는 데스크톱 실행 파일과 Python 백엔드를 모두 다시 빌드하세요. 할당된 포트는 메모리에만 두며 프런트엔드 환경설정에 저장하지 않습니다.

## Linux 빌드

배포판에 맞는 Tauri Linux 필수 패키지를 설치한 뒤 실행합니다.

```bash
python ../build_linux_x64.py
```

이 스크립트는 PyInstaller 백엔드를 빌드해 Tauri sidecar로 넣고, `plugins`, `Dict`, `translation_guidelines`,
`res`를 함께 묶어 `.deb`, `.rpm`, `.AppImage`, 휴대용 `.tar.gz`를 만듭니다. x86_64만 지원하며
ARM 대상은 의도적으로 범위에서 제외했습니다.

## 연결 테스트

- 프런트엔드 주소 선택, HTTP/SSE 경로, 재연결: `npm run test:backend-connection`.
- 기본 프로세스 수명 주기(`src-tauri`에서): `cargo test --offline backend::tests -- --include-ignored`. 이 테스트는 저장소의 `.venv`로 실제 Python 백엔드를 시작합니다. 백엔드 의존성이 설치된 다른 Python 환경을 쓰려면 `GALTRANSL_TEST_PYTHON`을 설정하세요. Windows에서는 테스트 환경이 자기 자식 프로세스 트리를 멈출 수 있어야 합니다.
