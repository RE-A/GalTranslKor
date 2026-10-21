# 갈게임 스크립트 파일 플러그인

프로그램과 함께 배포되는 `res/msg_tool.exe`로 스크립트를 추출하고 되씁니다.

## 원문 다시 추출

스크립트 엔진이나 원문 인코딩을 바꾼 뒤에는 이 플러그인 설정의 **원문 인코딩** 아래에 있는 **원문 다시 추출**을 누르세요. 버튼을 누르면 현재 프로젝트 설정을 먼저 저장하고, 그 설정으로 이 플러그인이 처리하는 입력 파일을 한꺼번에 다시 추출한 뒤, 성공한 파일 수와 문장 수, 실패 이유를 그 자리에 보여 줍니다. 추출에 성공하면 추출 캐시를 갱신합니다. 파일 하나가 실패하면 그 파일의 마지막 성공 추출 캐시를 유지하고 다른 파일을 계속 처리합니다. "번역문 보기" 페이지로 갈 필요가 없으며, 나중에 그 페이지를 열면 내용을 다시 읽습니다.

추출 캐시는 번역 캐시와 별개입니다. 번역 캐시가 있는 파일은 계속 번역문을 보여 주며, 새로 고쳐도 번역 캐시를 지우거나 덮어쓰지 않습니다.

## 되쓰기 인코딩 검사

"원문 인코딩"(`source_encoding`)은 읽기를, "출력 인코딩"(`patched_encoding`)은 되쓰기를 정합니다. 출력 인코딩을 비우면 msg-tool의 엔진 기본값을 쓰며 원문 인코딩을 자동으로 따르지 않습니다. 예를 들어 CatSystem2의 CST는 기본으로 CP932 / Shift-JIS로 되쓰므로 일부 문자(한글 포함)는 그대로 쓸 수 없습니다.

플러그인은 msg-tool로 되쓰기 전에 인코딩 규칙이 확인된 CST와 KAG 텍스트를 검사합니다. 인코딩할 수 없는 문자를 찾으면 파일, 데이터 항목, 이름/본문, 문자 코드값을 알려 주고 원본 스크립트와 기존 출력을 유지합니다. Unicode BOM, 묶인 KAG, Windows 코드 페이지 인수, 도구의 치환표/이름표는 잘못 막지 않도록 도구에 맡깁니다. 다른 형식이나 사전 검사가 다루지 않는 인코딩 문제도 도구가 오류나 경고를 반환하면 처리 안내와 함께 원본 진단을 보여 줍니다. msg-tool의 `gb2312`는 실제로 GBK를 쓰므로 사전 검사도 GBK 기준입니다.

`Failed to encode Shift-JIS`나 인코딩 손실 안내가 나오면 게임 지원 여부에 따라 고르세요.

- 게임이 일본어 인코딩을 요구하면: 아래 **JIS 치환**을 켜고 UIF 설정이나 대응 치환 글꼴을 배포합니다. JIS 치환 사전은 중국어 간체자용이라 한글은 치환할 수 없습니다.
- 게임이 다른 인코딩을 지원하면: **출력 인코딩**을 `utf8`(또는 `gb2312`)로 바꿉니다. 원문 인코딩만 바꾸면 효과가 없습니다. `extra_args`에 `-p` / `-P`가 있으면 함께 고치거나 지우세요. 이 추가 인수가 출력 인코딩 설정보다 우선합니다.
- 안내된 문자를 고친 뒤 결과를 다시 만듭니다. 출력 설정만 바꿨다면 다시 번역할 필요가 없습니다.

## JIS 치환

플러그인 설정에서 **JIS 치환**(`jis_substitution: true`)을 켜면, 되쓸 때 본문과 이름에서 CP932로 인코딩할 수 없는 문자를 내장 사전에 따라 일본어 문자로 바꿉니다. 바로 인코딩할 수 있는 문자는 그대로 둡니다. 원문 유지 모드에서는 덧붙인 원문도 검사합니다. 번역 캐시와 전달된 데이터는 바뀌지 않습니다.

- 켜면 항상 CP932로 출력하며 `patched_encoding`을 무시합니다. `source_encoding`은 계속 원본 스크립트의 읽기 인코딩을 정합니다. `extra_args`의 출력 인코딩 인수는 지우세요.
- 되쓰기에 성공할 때마다 프로젝트 출력 루트에 `uif_config.json`을 만들거나 갱신합니다(보통 `gt_output/uif_config.json`, 옛 프로젝트는 `json_cn/uif_config.json`일 수 있음). 하위 폴더의 스크립트도 이 설정을 함께 쓰며, 번역이 모두 끝날 때까지 기다릴 필요가 없습니다.
- UIF의 `character_substitution.source_characters`는 치환된 일본어 문자, `target_characters`는 그에 대응하는 원래 문자입니다. 매핑은 현재 플러그인 인스턴스가 성공적으로 쓴 모든 스크립트를 합친 것이며, 같은 파일을 다시 저장하면 그 파일의 매핑을 갱신합니다. 이어서 실행할 때는 다시 되쓰지 않은 스크립트와 호환되도록 이전 설정의 매핑을 유지합니다. 옛 매핑을 지우려면 출력 폴더의 설정을 지운 뒤 출력을 전부 다시 만드세요.
- 기존 설정의 글꼴, 삽입 등 다른 설정은 유지합니다. 스크립트를 게임에 복사한 뒤 [UniversalInjectorFramework](https://github.com/AtomCrafty/UniversalInjectorFramework)와 이 설정을 함께 쓰거나, 사전에 대응하는 치환 글꼴을 써야 원래 문자가 표시됩니다.
- **JIS 매핑 불가 문자 처리**(`jis_unmapped`)의 기본값은 `error`이며, 사전에 없는 문자가 있으면 그 파일의 쓰기를 멈춥니다. `space`로 하면 SExtractor처럼 전각 공백으로 바꾸고, 설정의 `character_substitution.remain`에 그 문자를 기록하며 경고를 출력합니다.
- 텍스트 자체에 치환 사전의 대상 문자가 있으면 `character_substitution.repeat`에 기록하고 화면 확인을 안내합니다. 대역 텍스트나 치환 글꼴을 쓸 때 특히 확인하세요.

JIS 치환을 끄면 원래 되쓰기 흐름으로 돌아가며 UIF 설정을 만들거나 갱신하지 않습니다.

## 에이전트로 설정 조정

에이전트는 `get_plugin_settings(plugin_name="file_msgtool_script")`로 기본값, 프로젝트 적용값, 선택지 설명, 전체 설정 경로를 볼 수 있습니다. 프로젝트 YAML에 아직 없는 항목도 `update_project_config`로 플러그인이 선언한 설정을 추가할 수 있습니다. 예: `plugin.file_msgtool_script.jis_substitution: true`. 모르는 키, 잘못된 종류, 올바르지 않은 선택지는 거부되며, 쓰기는 현재 에이전트 권한 모드와 승인 미리보기를 따릅니다.

되쓰기 인코딩에 실패하면 `wait`와 `get_runtime`이 전체 오류와 구조화된 해결 안내를 돌려줍니다. 먼저 설정을 조회한 뒤 게임 호환성에 따라 JIS 치환을 고르거나 `plugin.file_msgtool_script.patched_encoding`을 조정합니다. 되쓰기 설정만 바꿨다면 `start_translation(translator="rebuildr")`로 캐시에서 다시 만들고 작업 성공을 기다립니다. JIS를 쓸 때는 UIF/대응 글꼴도 배포해야 합니다.

## 사전 출처

`subs_cn_jp.json`(2,999개 매핑)과 `uif_config.json` 템플릿은 [SExtractor](https://github.com/satan53x/SExtractor) 버전 `8d8d976fd04ae54e7c677705af937273d04a376a`의 `src/subs_cn_jp.json`, `src/uif_config.json`에서 복사했습니다. 치환 규칙은 `src/helper_text.py`의 `generateSubsJis` / `generateSubsConfig`를 참고했으며, SExtractor에 따르면 사전은 원래 GalTransl_DumpInjector에서 왔습니다. SExtractor와 이 프로젝트는 모두 GPL-3.0 라이선스를 쓰며 자세한 내용은 저장소 루트의 `LICENSE`를 보세요.

사전과 템플릿은 플러그인과 함께 묶여 있어 실행할 때 SExtractor를 설치할 필요가 없습니다.
