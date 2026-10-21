# 플러그인 규격

## 플러그인 소개

플러그인 시스템은 텍스트 플러그인, 파일 플러그인, 문제 플러그인 세 종류를 지원합니다.
- 텍스트 플러그인은 텍스트를 원하는 대로 처리합니다. 예: 텍스트 정리, 텍스트 수정, 인물 이름 위치 수정 등.
- 파일 플러그인은 GalTransl이 더 많은 파일 형식을 지원하게 합니다. 예: 자막 파일, 텍스트 파일 등.
- 문제 플러그인은 번역문 후처리가 끝난 뒤 번역 문제를 검사하며, 반환한 문제는 시스템이 한데 모아 중복을 없앱니다.

플러그인을 기여하거나 직접 플러그인을 만들고 싶다면 이 문서를 계속 읽어 주세요.

## 1. 플러그인 이름 규칙

플러그인 이름은 기능을 정확히 드러내도록 분명하게 짓습니다. 다음 규칙을 따릅니다.

- 형식은 텍스트 플러그인 `Text_(엔진 이름/파일 종류)_(용도)`, 파일 플러그인 `File_(엔진 이름/파일 종류)_(확장자/noext)`로 통일합니다.
- 플러그인 파일 이름은 `text_`, `file_`, `problem_` 중 하나로 시작합니다.
- 엔진 이름/파일 종류 예: `krkr(엔진 이름)`, `subtitle(자막류 파일)`. 범용 텍스트 플러그인은 `common`을 씁니다.
- 마지막은 용도나 확장자입니다. 텍스트 플러그인 예: `clean(텍스트 정리)`, `fix(텍스트 수정)`. 파일 플러그인 예: `ast`, `srt`, `noext`.
- 최종 이름 예: `Text_krkr_rubyClean`, `Text_common_linebreakFix`, `File_subtitle_srt`

## 2. 플러그인 구조

플러그인에는 최소한 `플러그인이름.yaml`과 `플러그인이름.py`가 있어야 하며, 플러그인 이름 폴더 안에 둡니다. 폴더 예:

```
plugins
├── Text_krkr_rubyClean
│   ├── Text_krkr_rubyClean.yaml
│   └── Text_krkr_rubyClean.py
├── File_subtitle_srt
│   ├── File_subtitle_srt.yaml
│   └── File_subtitle_srt.py
```

.yaml 설정 파일 예:

```yaml
Core:
  Name: 예제 텍스트 플러그인
  Type: text
  Module: text_example_nouse

Documentation:
  Author: cx2333
  Version: 1.0
  Description: 예제 텍스트 플러그인입니다. 실제 프로젝트에서는 사용하지 마세요

Settings: # 플러그인 설정
  set_int: 123
  set_string: aaa
  set_bool: True
  设置样例4: False
```

Core와 Documentation은 필수이고 Settings는 없어도 됩니다.

- Core: 플러그인 기본 정보. 플러그인 이름, 종류(text/file/problem), 모듈 이름(파일 이름과 같게).
- Documentation: 플러그인 작성자, 버전, 설명.
- Settings: 플러그인 설정. 필요에 따라 자유롭게 정합니다.

## 3. 플러그인 작성 안내

플러그인은 `GTextPlugin`, `GFilePlugin`, `GProblemPlugin` 중 하나를 상속하며 클래스 이름은 자유입니다.

다음 메서드는 초기화용으로 세 종류 모두에 있습니다.

- `gtp_init(self, plugin_conf: dict, project_conf: dict)`: 플러그인을 불러올 때 호출됩니다. plugin_conf는 플러그인 yaml의 설정, project_conf는 프로젝트 yaml의 common 아래 설정입니다.
- `gtp_final(self)`: 모든 파일 번역이 끝난 뒤의 동작. 예: 안내 메시지 출력.

텍스트를 처리하는 GTextPlugin은 다음 메서드를 필요한 만큼 구현합니다.

- `before_src_processed(self, tran: CSentense) -> CSentense`: 원문 처리 전에 호출됩니다. 수정한 `CSentense`를 반환합니다.
- `after_src_processed(self, tran: CSentense) -> CSentense`: 원문 처리 후에 호출됩니다. 수정한 `CSentense`를 반환합니다.
- `before_dst_processed(self, tran: CSentense) -> CSentense`: 번역문 처리 전에 호출됩니다. 수정한 `CSentense`를 반환합니다.
- `after_dst_processed(self, tran: CSentense) -> CSentense`: 번역문 처리 후에 호출됩니다. 수정한 `CSentense`를 반환합니다.

* 여기서 "처리"란 GalTransl이 항상 하는 일, 즉 일본어 대사 괄호 제거와 사전 치환, 번역 후 대사 괄호 복원과 번역 후 사전 치환을 말합니다.
* 그래서 엔진 텍스트에 대사 괄호 좌우로 불필요한 문자가 있으면 `before_src_processed`에서 숨겨 두면(tran의 left_symbol, right_symbol 속성으로 옮김) 대사 괄호를 복원할 때 자동으로 돌아옵니다.
* 엔진 텍스트가 대사 괄호 왼쪽에 인물 이름을 적는다면 `before_src_processed`에서 이름을 tran의 speaker 속성으로 옮기고, `after_dst_processed`에서 이름을 대사 괄호 왼쪽으로 되돌립니다(프로그램이 먼저 대사 괄호를 복원해야 하므로 after).

파일을 처리하는 GFilePlugin은 다음 메서드를 **반드시** 구현합니다.
- `load_file(self, file_path: str) -> list`: 파일을 불러와 message와 name(생략 가능)이 있는 dict list를 반환합니다.
- `save_file(self, file_path: str, transl_json: list)`: 파일을 저장합니다. transl_json은 load_file이 준 json에서 message와 name을 번역한 결과입니다.

* load_file에서는 다음 방법으로 message와 무관한 내용을 결과까지 가져갈 수 있습니다.
1. 각 dict에 다른 정보를 바로 넣으면 save_file이 그대로 돌려받으므로 원래 파일로 복원해 저장합니다(예: file_subtitle_srt, file_vn_scene_txt 플러그인)
## 4. 문제 플러그인

플러그인 폴더와 파일 이름은 `problem_` 접두사를 권장하며, YAML의 `Core.Type`은 `problem`입니다.
프로젝트에서 `plugin.problemPlugins`를 설정하면 여러 플러그인이 목록 순서대로 실행됩니다.
프로젝트 전용 플러그인은 프로젝트의 `plugins` 폴더에 두고 이름 앞에 `(project_dir)`를 붙입니다. 프로젝트 설정 덮어쓰기는 여전히 모듈 이름을 씁니다.
`problemPlugins`를 설정하지 않은 옛 프로젝트는 기본으로 `problem_common`을 사용하며, `[]`로 명시하면 끌 수 있습니다.
`problem_common`은 기존 `problemAnalyze.problemList`, `arinashiDict` 설정을 유지합니다.
긴 문장 기준값은 플러그인 설정 `plugin.problem_common.avgSentenceLengthThreshold`이며 기본값은 17입니다.
플러그인 YAML의 `Settings`는 기본값을, `SettingsSchema`는 라벨, 설명, 숫자 범위 등을 선언합니다.
데스크톱 앱은 설정 항목을 자동으로 표시하고, 에이전트는 `get_plugin_settings`로 찾아 바꿀 수 있습니다.
`SettingsSchema`의 선택 항목 `legacy_path`로 옛 설정 경로를 선언할 수 있습니다. 플러그인 덮어쓰기 값이 없으면
실행 시점, 데스크톱 앱, 에이전트 모두 이 옛 값을 읽으며, 새 플러그인 설정이 옛 값보다 우선합니다.
일반 플러그인은 이 방식으로 `problemAnalyze.avgSentenceLengthThreshold`와 호환됩니다.
문제 종류, 설명, 기본 사용 여부는 플러그인이 정하며, 백엔드와 프런트엔드는 `get_problem_types()`로 읽습니다.
이 메서드는 `gtp_init` 전에도 호출될 수 있으므로 초기화 상태에 의존하면 안 됩니다.
플러그인 안에 열거형을 정의하고 `problem_types = 열거형클래스`로 지정할 수 있으며, 열거형 멤버는 `description`과 `default_enabled`를 제공합니다.
문자열 목록(기본 사용 안 함)이나 `name`, `description`, `default_enabled`가 있는 dict 목록도 지원합니다.
`get_problem_types()`를 덮어써 `[{"name": "译文过长", "description": "설명", "default_enabled": false}]`를 반환해도 됩니다.
`problemAnalyze.problemList`가 없거나 `null`이면 플러그인 기본값을 쓰고, 명시한 목록은 기본값을 덮어쓰며, `[]`는 모든 선택 항목을 끕니다.
같은 이름의 종류는 화면에서 합쳐 표시되며, 기본 사용 여부는 모든 선언의 합집합입니다. 옛 `GPT35` 설정도 계속 읽을 수 있습니다.
데스크톱 앱의 "플러그인 기본값으로 되돌리기"는 목록을 `null`로 하고 옛 `GPT35` 목록을 지웁니다. 출처 플러그인을 끈 종류는 계속 표시되지만 선택할 수 없습니다.
플러그인의 `check`는 `project_config.getProblemAnalyzeConfig("problemList")`로 자신의 검사 항목이 켜져 있는지 판단해야 합니다.

```python
from GalTransl.GTPlugin import GProblemPlugin

class ExampleProblemPlugin(GProblemPlugin):
    def get_problem_types(self):
        return [{"name": "译文过长", "description": "번역문이 길이 상한을 넘음", "default_enabled": True}]

    def gtp_init(self, plugin_conf, project_conf):
        self.limit = plugin_conf.get("Settings", {}).get("limit", 100)

    def check(self, tran, project_config, gpt_dict=None):
        if "译文过长" not in project_config.getProblemAnalyzeConfig("problemList"):
            return []
        return ["译文过长"] if len(tran.post_dst) > self.limit else []
```

`check`는 반드시 `list[str]`를 반환하며 문장이나 `tran.problem`을 고칠 필요는 없습니다.
검사할 때 원문, 번역문, 앞뒤 문장, 프로젝트 설정, GPT 사전을 읽을 수 있습니다.
시스템은 빈 번역문과 `skip_check` 항목을 건너뛰고, 기존 문제를 유지하며, 플러그인 하나의 예외가 다른 플러그인에 번지지 않게 합니다.
일반 번역, 캐시 적중 후 재생성, 캐시 편집 후 재생성은 같은 문제 플러그인을 씁니다.
`gtp_final`은 작업이 끝날 때 호출됩니다. 문제 플러그인 인스턴스는 병렬 조각이 함께 쓰므로 `check` 안에서 인스턴스 상태를 바꾸지 마세요.

## 5. 주의 사항

- 원래 `GalTransl.Utils`의 `get_most_common_char`, `contains_japanese`, `contains_english`, `contains_korean`, `is_all_gbk`, `extract_control_substrings`는 `problem_common` 플러그인으로 옮겨졌습니다. 옛 경로를 쓰는 사용자 플러그인은 옮기거나, 필요한 판단 로직을 플러그인 안에 직접 두어야 합니다.
- 모든 플러그인 메서드에는 알맞은 오류 처리가 있어야 합니다.
- 플러그인끼리 서로 영향을 주지 않도록 전역 변수를 피하세요.
- 외부 자원 의존을 최소화하고 Python 표준 라이브러리와 GalTransl이 제공하는 인터페이스만 쓰세요.
- Complex is better than complicated. 기존 플러그인에 합칠 수 있으면 합치는 것을 우선하고, Author에 이름을 추가하세요.

이상이 플러그인의 기본 규격입니다. 도움이 되기를 바랍니다.
