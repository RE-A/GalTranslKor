<div align=center><img width="150" height="150" src="./img/logo.png"/></div>

<h1><p align='center' >GalTransl</p></h1>

<div align=center><img src="https://img.shields.io/github/v/release/XD2333/GalTransl"/>   <img src="https://img.shields.io/github/license/XD2333/GalTransl"/>   <img src="https://img.shields.io/github/stars/XD2333/GalTransl"/></div>
<p align='center' >GPT/Claude/Deepseek/Sakura 등 대규모 언어 모델을 지원하는 갈게임 자동 번역 솔루션</p>

  한국어 · [English](README_EN.md)

> [!NOTE]
> 이 저장소는 [GalTransl](https://github.com/GalTransl/GalTransl)을 한국어 사용자용으로 고친 Fork입니다.
> 데스크톱 화면과 백엔드 메시지는 기본으로 한국어로 표시되며(설정에서 中文/English로 바꿀 수 있음),
> **로컬 Ollama 모델로 일본어 장면 TXT를 한국어로 번역하는 방법**은
> [한국어 · Ollama 번역 설정 및 Windows 실행](README_KO_OLLAMA.md)에 정리되어 있습니다.
> 아래 내용은 원본 README를 옮긴 것으로, 원본 기능 설명은 중국어 번역(汉化) 작업을 기준으로 합니다.
> 이 Fork에서는 중국어 전용 데이터(중국어 기본 사전, 중국어 번역 지침, 중국어 예제 프로젝트, 중국어 평가 데이터, 중국어 README)를 삭제했습니다.
> 중국어 원본이 필요하면 [원본 저장소](https://github.com/GalTransl/GalTransl)를 보세요.

  GalTransl은 몇 가지 기본 기능의 개선과 GPT 프롬프트 엔지니어링(Prompt Engineering)의 적극적인 활용을 결합한 갈게임 자동 번역 도구로, 게임에 넣는 번역 패치를 만드는 데 씁니다. 이제 **데스크톱 그래픽 인터페이스**를 제공해 명령줄 없이도 번역 전 과정을 진행할 수 있습니다.

> [!TIP]
> **갈게임을 번역하고 싶은데 대사를 추출하고 번역문을 게임에 다시 넣는 방법을 모르겠다면?**
>
> 함께 쓰는 **[GalTransl-GalGameReverse-Skill](https://github.com/GalTransl/GalTransl-GalGameReverse-Skill)** 을 써 보세요. 도구 모음과 게임 폴더를 로컬 파일을 다룰 수 있는 AI 도우미에게 맡기면 엔진을 식별하고 대사를 추출한 뒤, GalTransl의 번역 결과를 게임 패치로 다시 써 넣어 줍니다. 프로젝트에 입문 안내가 있으니 먼저 몇 문장으로 시험한 다음 게임 전체를 번역하세요. 지원 범위는 엔진과 게임 버전에 따라 다릅니다.

## 🤖 에이전트 모드 지원

> [!IMPORTANT]
> **이제 GalTransl은 에이전트 모드를 지원해 번역 과정 전체를 스스로 진행할 수 있습니다.**
>
> 데스크톱 앱에서 **에이전트 모드**로 들어가 자연어로 번역 요구사항을 말하면 에이전트가 알아서 번역 작업을 진행합니다.

![GalTransl 에이전트 모드: 번역 전 준비를 스스로 하고 시험 번역을 시작](./img/agent-mode.png)

번역 후 교정 서브에이전트는 기본으로 맡은 범위의 번역문을 바로 고칠 수 있습니다. 확신이 없거나 고친 뒤에도 확인이 필요한 문장에는 `proofread_comment`를 남겨 메인 에이전트가 다시 검토합니다. 메인 에이전트는 기본으로 수정 통계와 검토 대기 요약을 받으며, 전체 수정 기록과 검토 대기 목록은 페이지 단위로 조회할 수 있고 수정은 기록 단위로 되돌릴 수 있습니다. 이후 다른 편집이 있었던 문장은 덮어쓰지 않습니다. 교정을 마친 뒤에는 출력 파일을 다시 생성해야 합니다.


## 머리말
&ensp;&ensp;&ensp;&ensp;GalTransl의 핵심은 자동 번역 파이프라인으로, ChatGPT로 갈게임을 자동 번역할 때 알려진 대부분의 문제를 해결하고 전체 번역 품질을 높였습니다. 또한 다른 프로젝트와 조합해 패치 제작 전 과정을 연결하여 시작 장벽을 어느 정도 낮췄습니다. 관심 있는 분은 이 프로젝트로 일정 품질의 기계 번역 패치를 더 쉽게 만들 수 있고, (어쩌면) 이 틀을 바탕으로 더 높은 품질의 번역 패치를 효율적으로 만들어 볼 수 있습니다.

  * 특징:
  1. 🖥️ **데스크톱 그래픽 인터페이스** —— Tauri + React로 만든 최신 데스크톱 앱. 명령줄이 필요 없고 다크 모드, 사용자 지정 배경, 여러 프로젝트 관리 등을 지원합니다

<img width="2044" height="1397" alt="QQ20261003-110410" src="https://github.com/user-attachments/assets/25185c5b-7d5a-46d5-b4d1-0f3353ea67a0" />

  3. **GPT/Claude/Deepseek/Sakura** 등 대규모 언어 모델을 지원하며 프롬프트 엔지니어링으로 GPT의 번역 품질을 높였습니다
  4. **GPT 사전**을 지원해 GPT가 인물 설정을 이해하고 인명, 인칭 대명사, 낯선 단어를 정확하게 번역하게 합니다
  5. 번역 전·번역 후 사전과 조건 사전으로 유연한 자동 사전 시스템을 구성합니다
  6. 캐시를 실시간으로 저장하고 중단된 곳부터 자동으로 이어서 번역합니다
  7. 다른 프로젝트와 함께 여러 엔진의 스크립트를 한 번에 풀고 넣을 수 있으며, 시작을 돕는 전체 안내를 제공합니다
  8. srt, lrc, vtt 자막 파일, mtool json 파일, t++ excel 파일, epub 파일을 바로 번역할 수 있습니다
  9. 🤗 [Galtransl-7B-v3.5](https://huggingface.co/SakuraLLM/GalTransl-7B-v2)는 비주얼 노벨 번역에 맞춰 최적화한 로컬 모델로, VRAM 6GB 이상 그래픽카드에서 쓸 수 있습니다. sakuraumi와 xd2333이 함께 만들었습니다(중국어 출력용)
  10. 🤗 [GalTransl-14B-v3](https://huggingface.co/SakuraLLM/Sakura-GalTransl-14B-v3)는 GalTransl-v3 모델의 14B 버전입니다. 더 큰 기반 모델과 개선된 정렬 학습 덕분에 GalTransl-7B-v3보다 전반적인 품질이 좋습니다(중국어 출력용)

<b>❗❗ 이 도구로 번역한 결과를 전체 교정·윤문 없이 배포할 때는 눈에 잘 띄는 곳에 "xx 모델 AI 번역 패치"라고 표시해 주세요. "개인 번역" 패치라고 표시해서는 안 됩니다.</b>

## 최근 업데이트
* 2026.8: v8 업데이트. 에이전트 모드 추가, AI가 번역 과정을 스스로 진행
* 2026.4: v7 업데이트. **데스크톱 그래픽 인터페이스**(Tauri + React) 추가, 다크 모드, 사용자 지정 배경, 여러 프로젝트 관리, 번역 과정 시각화 등 지원
* 2025.5: v6 업데이트. 번역 템플릿 ForGal, GalTransl-14B-v3 모델 추가
* 2024.5: v5 업데이트. GalTransl-7B 모델 추가, 여러 파일 형식 지원
* 2024.2: v4 업데이트. 플러그인 시스템 지원
* 2023.12: v3 업데이트. 파일 단위 멀티스레드 지원 by @ryank231231
* 2023.7: v2 업데이트. 코드 전면 재구성 by @ryank231231
* 2023.6: v1 첫 버전 공개

## 목차
* [환경 준비](#환경-준비): 환경과 소프트웨어 설치
* [시작 안내](#시작-안내): 기계 번역 패치를 만드는 전 과정 소개. **이 도구 사용법만 보려면 2장의 2.2절로 바로 가세요**
* [설정 파일과 번역 엔진 설정](#설정-파일과-번역-엔진-설정): 번역 엔진 API의 호출과 설정 방법을 자세히 설명합니다.
* [GalTransl 핵심 기능 소개](#galtransl-핵심-기능-소개): GPT 사전, 캐시, 일반 사전, 문제 찾기 등의 기능을 소개합니다.
* 이후 안내는 [Wiki로 옮겼습니다](https://github.com/xd2333/GalTransl/wiki)(중국어)
* [개발과 빌드](#개발과-빌드): 개발 환경, 소스 실행, 플랫폼별 빌드와 자동 배포(클릭해서 펼치기)

## 환경 준비
  * **데스크톱판 (권장)**
  [Release](https://github.com/GalTransl/GalTransl/releases/)에서 플랫폼에 맞는 데스크톱 패키지를 내려받습니다. Windows는 `GalTransl_*_win.zip`을 받아 압축을 풀고 `GalTransl Desktop.exe`를 두 번 클릭하면 되며 **Python을 설치할 필요가 없습니다**. Linux x86_64는 휴대용 `.tar.gz`를 풀고 `./galtransl-desktop`을 실행합니다. 시스템에 WebKitGTK 4.1 등의 런타임 라이브러리가 필요합니다. macOS는 Intel과 Apple Silicon용 DMG 두 가지와 휴대용 `.tar.gz`를 제공합니다. 데스크톱 앱은 창마다 독립된 백엔드를 자동으로 시작하고 빈 포트를 할당하므로, 창 하나를 닫으면 그 창의 백엔드만 멈추고 다른 창은 계속 실행됩니다.
  * 이 Fork의 한국어 화면과 Ollama 번역 기능은 소스에서 실행합니다. [개발과 빌드](#개발과-빌드)와 [Ollama 안내](README_KO_OLLAMA.md)를 참고하세요.



## 유용한 도구
| 이름 | 설명 |
| --- | --- |
| GARbro | 엔진 도구: 최고의 언팩 도구. [내려받기](https://github.com/morkt/GARbro/releases/download/v1.5.44/GARbro-v1.5.44.2904.rar) |
| [KirikiriTools](https://github.com/arcusmaximus/KirikiriTools) | 엔진 도구: Krkr, krkrz 추출·삽입 도구 |
| [UniversalInjectorFramework](https://github.com/AtomCrafty/UniversalInjectorFramework) | 엔진 도구: sjis 터널, sjis 치환 방식 범용 삽입 프레임워크 |
| [VNTextProxy](https://github.com/arcusmaximus/VNTranslationTools) | 엔진 도구: sjis 터널 방식 범용 삽입 프레임워크 |
| GalTransl_DumpInjector | 스크립트 도구: [VNTextPatch](https://github.com/arcusmaximus/VNTranslationTools)의 그래픽 인터페이스, 종합 스크립트 텍스트 추출·삽입 도구 |
| [SExtractor](https://github.com/satan53x/SExtractor) | 스크립트 도구: 종합 스크립트 텍스트 추출·삽입 도구 |
| [msg-tool](https://github.com/lifegpc/msg-tool) | 스크립트 도구: 종합 스크립트 텍스트 추출·삽입 도구 |
| [DBTXT2Json_jp](https://github.com/XD2333/DBTXT2Json_jp) | 스크립트 도구: 두 줄 텍스트와 json_jp 상호 변환 스크립트 |
| [EmEditor](https://www.ghxi.com/emeditor.html) | 텍스트 도구: 강력한 텍스트 편집기. 주로 캐시 파일 수정에 씁니다. |
| [VSCode](https://code.visualstudio.com/) | 텍스트 도구: 강력한 텍스트 편집기. 주로 캐시 파일 수정에 씁니다. |
| [KeywordGacha](https://github.com/neavo/KeywordGacha) | 텍스트 도구: OpenAI 호환 API로 용어표를 자동 생성 |

## 시작 안내
갈게임 번역 패치를 만드는 대략적인 흐름은 다음과 같습니다.
1. 엔진 식별 -> 리소스 패키지를 풀어 스크립트 얻기 -> 2로
2. 스크립트를 일본어 텍스트로 풀기 -> 번역문으로 번역 -> 번역된 스크립트 만들기 -> 3으로
3. 리소스 패키지로 묶기 / 묶지 않고 읽히기 -> 4로
4. 엔진이 unicode를 지원하면 바로 플레이 -> 엔진이 shift jis라면 두 가지 방법으로 번역문 표시 시도

위 네 단계로 나눠 설명합니다. 처음 해 보는 분도 따라올 수 있도록 초보자 기준으로 썼습니다.

* 먼저 첫 파일 하나만 번역하거나 아무 문장이나 넣어 게임에 다시 넣고, 제대로 표시되는지 확인한 다음 전체를 번역하세요

(클릭해서 자세히 보기)
<details>

<summary>

### 1장 식별과 언팩

</summary>
엔진 식별은 사실 간단합니다. 보통 GARbro로 게임 폴더 안의 아무 리소스 패키지나 열면 왼쪽 아래 상태 표시줄에 엔진 이름이 나옵니다.

또는 [리소스 패키지 확장자 표](https://morkt.github.io/GARbro/supported.html)와 확장자를 비교해 보세요.

시나리오 스크립트는 보통 눈에 띄는 키워드가 있는 리소스 패키지나 그 안의 폴더에 있습니다. 예: scene, scenario, message, script 등. 스크립트는 대개 장이나 인물별로 나뉘어 있고, 본편과 H 장면(예: _h가 붙음)이 나뉜 경우도 있어서 리소스 패키지를 몇 개 뒤져 보면 찾을 수 있습니다.

또는 [Dir-A의 강좌](https://space.bilibili.com/8144708/)(중국어)를 참고하세요.

특히 새 krkrz 엔진은 GARbro로 리소스 패키지를 열 수 없으므로 [KrkrzExtract 프로젝트](https://github.com/xmoezzz/KrkrzExtract/releases/tag/1.0.0.0)를 써서 게임을 exe에 끌어 놓아 실행합니다. 그다음 전체 CG 세이브를 받아 모든 시나리오를 Ctrl로 한 번 넘기면 스크립트 파일을 얻을 수 있습니다.

</details>
<details>

<summary>

### 2장 추출과 번역

</summary>

* **【2.1. 스크립트 텍스트 추출】**
&ensp;&ensp;&ensp;&ensp;보통 이 프로젝트는 [VNTextPatch 도구](https://github.com/arcusmaximus/VNTranslationTools)와 함께 스크립트를 풉니다. VNTextPatch는 arcusmaximus가 만든, [여러 엔진](https://github.com/arcusmaximus/VNTranslationTools#vntextpatch) 스크립트의 추출과 삽입을 지원하는 범용 도구입니다.(모든 엔진에서 되는 것은 아니며, 실제로 추출에 실패하는 게임도 있습니다)

&ensp;&ensp;&ensp;&ensp;VNTextPatch는 cmd로 다루기 때문에 쉽게 쓸 수 있도록 그래픽 인터페이스를 만들었습니다. 프로젝트의 useful_tools/GalTransl_DumpInjector에서 GalTransl_DumpInjector.exe를 실행하세요.
&ensp;&ensp;&ensp;&ensp;이제 일본어 스크립트 폴더와 추출한 일본어 json을 저장할 폴더만 고르면 됩니다. 보통 일본어 스크립트는 script_jp 폴더에 두고, 추출한 스크립트를 저장할 gt_input 폴더를 새로 만듭니다.
![그림1](./img/img_dumper.png)
&ensp;&ensp;&ensp;&ensp;GalTransl은 처음부터 끝까지 name-message 형식의 JSON으로 입력, 처리, 출력합니다. [JSON이란](http://c.biancheng.net/json/what-is-json.html)(중국어)
추출한 json 파일은 emeditor로 열 수 있으며 보통 다음과 같습니다.
```json
[
  {
    "name": "咲來",
    "message": "「ってか、白鷺学園だったらあたしと一緒じゃん。\r\nセンパイだったんですねー」"
  }
]
```
&ensp;&ensp;&ensp;&ensp;{object(객체)} 하나가 한 문장이며 `message`는 내용입니다. object에 `name`이 있으면 대사라는 뜻입니다. 다만 모든 종류의 스크립트에서 name을 함께 추출할 수 있는 것은 아니며, **name을 올바르게 추출할 수 있으면 GalTransl의 번역 품질이 더 좋아집니다**.
&ensp;&ensp;&ensp;&ensp;PS. GalTransl은 정해진 형식의 json 입력만 지원하지만 VNTextPatch에 묶여 있는 것은 아닙니다. SExtractor 도구도 이제 GalTransl이 요구하는 name-message 형식 JSON을 내보낼 수 있습니다.
&ensp;&ensp;&ensp;&ensp;이 Fork는 장면별로 나뉜 일본어 TXT도 줄 구조를 보존하며 읽는 `file_vn_scene_txt` 플러그인을 제공합니다. [Ollama 안내](README_KO_OLLAMA.md)를 참고하세요.

* **【2.2. 데스크톱 앱으로 번역 (권장)】**
&ensp;&ensp;&ensp;&ensp;[Release](https://github.com/XD2333/GalTransl/releases/)에서 최신 버전을 내려받아 압축을 풀고 `GalTransl Desktop.exe`를 두 번 클릭해 실행합니다. 데스크톱 앱이 백엔드 서비스를 자동으로 시작하므로 따로 할 일은 없습니다.

&ensp;&ensp;&ensp;&ensp;실행 후 기본 흐름:
1. **새 프로젝트**: 홈에서 "새 프로젝트"를 누르고 프로젝트 저장 위치를 고른 뒤 번역할 파일을 가져옵니다
2. **번역 백엔드 설정**: 새 프로젝트 마법사에서 번역 백엔드(Deepseek, OpenAI 등)를 고르고 API Key와 Endpoint를 입력합니다. 왼쪽 "모델 설정" 페이지에서 여러 백엔드 설정을 미리 만들어 둘 수도 있습니다
3. **사전 설정**: 프로젝트의 "프로젝트 사전" 페이지에서 GPT 사전과 일반 사전을 설정합니다(최소한 인명 사전은 권장)
4. **번역 시작**: "번역 시작" 페이지에서 번역을 시작하고 진행률과 결과를 실시간으로 확인합니다
5. **번역문 보기**: 번역이 끝나면 "번역문 보기" 페이지에서 자동 오류 검사 결과를 보고 캐시를 고친 뒤 다시 생성합니다

&ensp;&ensp;&ensp;&ensp;데스크톱 앱은 여러 프로젝트를 동시에 열 수 있고 다크 모드, 사용자 지정 배경 등을 지원하며 "설정" 페이지에서 조정합니다. 화면 언어도 "설정"에서 한국어/中文/English 중에 고를 수 있습니다.

* **【2.2b. 명령줄로 번역 (고급 사용자)】**
&ensp;&ensp;&ensp;&ensp;명령줄 버전을 쓰려면 프로젝트 폴더를 만들고 `config.yaml`을 둡니다. 데스크톱 앱의 새 프로젝트 마법사가 만드는 설정(기본 템플릿 `GalTransl/DefaultProjectConfig.py`)을 쓰거나, Ollama 한국어 번역이라면 `run_ollama_ko.cmd projects\mygame --init`으로 만드세요. 그다음 일본어 파일을 `gt_input` 폴더에 넣고 `config.yaml`에서 번역 백엔드를 설정합니다.

```yaml
# 번역 백엔드 설정
backendSpecific:
  OpenAI-Compatible: # (ForGal/ForNovel/GenDic) OpenAI API 호환 인터페이스 공통
    tokens:
      - token: sk-example-key1
        endpoint: https://api.deepseek.com # 요청 주소. v1은 붙여도 되고 안 붙여도 됨
        modelName: deepseek-chat
      - token: sk-example-key2
        endpoint: https://openrouter.ai/api/v1/chat/completions # /chat/completions로 끝나면 v1을 자동으로 붙이지 않음
        modelName: deepseek/deepseek-chat-v3-0324:free
        stream: true # 토큰마다 스트리밍 요청 설정 가능
```

생각(thinking) 매개변수는 "모델 설정"에서 각각 설정하며, `OpenAI-Compatible` 항목이나 토큰마다 쓸 수도 있습니다: `enableThinking: true/false`(Qwen3, DashScope, SiliconFlow 등의 `enable_thinking`), `thinkingType: enabled/disabled`(DeepSeek 등의 `thinking.type`), `reasoningEffort: none/minimal/low/medium/high/xhigh/max`(OpenAI o 시리즈, GPT-5 및 호환 중계의 `reasoning_effort`). 세 항목은 서로 독립적이며 서비스 문서에 맞춰 고릅니다. 전역에서 설정하지 않으면 보내지 않고, 토큰에서 설정하지 않으면 전역을 따르며, 지원 단계는 서비스 문서를 기준으로 합니다.

* 유료 API 중계 서비스 예: [SiliconFlow](https://cloud.siliconflow.cn/i/SvDatvsk)(modelName: "deepseek-ai/DeepSeek-V3.1-Terminus"), [oaipro](https://api.oaipro.com/register?aff=ceAU) 등. 예시일 뿐이며 다른 중계 서비스도 찾아볼 수 있습니다. 이 프로젝트는 이들의 안정성과 사용 가능성을 보증하지 않습니다.

&ensp;&ensp;&ensp;&ensp;이때 받은 key를 넣으면서 endpoint 주소도 바꿔야 합니다. 보통 해당 서비스 안내에 나와 있습니다.
```yaml
      - token: sk-example-key1
        endpoint: https://api.siliconflow.cn # 요청 주소. v1은 붙여도 되고 안 붙여도 됨
```

&ensp;&ensp;&ensp;&ensp;프로젝트 설정을 마치고 필요한 의존성을 설치했는지 확인한 뒤(환경 준비 참고) `run_GalTransl_terminal.bat`를 두 번 클릭하고 프로젝트 경로를 입력하면 번역이 시작됩니다.
&ensp;&ensp;&ensp;&ensp;로컬 Ollama로 한국어 번역을 하려면 이 Fork의 `run_ollama_ko.cmd`와 [Ollama 안내](README_KO_OLLAMA.md)를 쓰세요.

&ensp;&ensp;&ensp;&ensp;**하지만 바로 번역을 시작하는 것은 권장하지 않습니다.** 최소한 [GPT 사전 사용법](#gpt-사전)을 먼저 익히거나 GenDic으로 인명 사전을 만들어, 번역할 갈게임의 인물 이름 사전을 정해 두어야 기본적인 번역 품질이 나옵니다.

&ensp;&ensp;&ensp;&ensp;번역이 끝나면 **캐시를 꼭 손보세요.** 대형 모델은 자주 실수합니다. GalTransl은 흔한 문제를 자동으로 찾아 캐시에 기록합니다. 캐시를 고친 뒤 프로그램을 다시 실행하면 캐시를 바탕으로 결과 json을 다시 만듭니다. [자동 오류 검사 절과 번역 캐시 절](#자동-오류-검사)을 참고하세요.

* **【2.3. 번역된 스크립트 만들기】**
&ensp;&ensp;&ensp;&ensp;GalTransl 추출·삽입 도구로 추출한 스크립트라면 만드는 방법도 같습니다. 일본어 스크립트 폴더, 번역 json 폴더, 번역 스크립트 저장 폴더를 고르고 '삽입'을 누르면 텍스트가 스크립트에 다시 들어갑니다. 다만 몇 가지 함정이 있으며 4장에서 다룹니다.

참고:
1. 일본어 스크립트 폴더를 script_jp라고 부르므로 번역 스크립트 저장 폴더는 보통 script_cn처럼 부릅니다
2. 보통 내보낼 때 쓴 도구로 다시 넣습니다. 번역을 시작하기 전에 가져오기와 내보내기가 모두 정상인지 먼저 확인하세요.


</details>

<details>

<summary>

### 3장 패킹 또는 패킹 없이 읽히기

 </summary>

&ensp;&ensp;&ensp;&ensp;번역 스크립트를 만들었으면 다음은 게임이 그것을 읽게 하는 일입니다. 요즘 주요 엔진은 대부분 패킹하지 않은 파일을 읽을 수 있습니다. Dir-A의 [강좌](https://space.bilibili.com/8144708/)(중국어)에서 작업할 엔진이 패킹 없이 읽기를 지원하는지 확인하세요.
&ensp;&ensp;&ensp;&ensp;특히 krkr/krkrz 엔진은 arcusmaximus의 [KirikiriTools 도구](https://github.com/arcusmaximus/KirikiriTools)에서 version.dll을 받아 게임 폴더에 넣고, 게임 폴더에 "unencrypted" 폴더를 만들어 스크립트를 바로 넣으면(하위 폴더 없이) krkr가 읽습니다.

</details>

<details>

<summary>

### 4장 엔진과 인코딩

</summary>

&ensp;&ensp;&ensp;&ensp;이 장을 읽기 전에 unicode, sjis(shift jis), gbk 인코딩의 기초를 알아 두세요. [Dir-A의 글](https://www.bilibili.com/read/cv12367744/)(중국어)을 참고하면 됩니다. 아래 내용은 원본 기준으로 중국어(GBK) 표시를 다룹니다. 한국어는 보통 unicode 엔진이 아니면 별도의 글꼴·인코딩 처리가 필요합니다.

작업 중인 엔진이 unicode 인코딩을 지원한다면(예: krkr, Artemis 엔진) 보통 바로 플레이할 수 있습니다. 하지만 엔진이 sjis 인코딩을 쓰면 그대로 열었을 때 글자가 깨지므로 두 가지 방법으로 번역문이 표시되게 해야 합니다.

방법 1: GBK 인코딩으로 스크립트를 넣고, 엔진 프로그램을 고쳐 GBK 인코딩을 지원하게 함
방법 2: 그대로 jis 인코딩으로 스크립트를 넣되, jis 터널 또는 jis 치환(권장) 방식으로 범용 삽입 dll과 함께 실행 중에 동적으로 바꿔 번역문을 표시함

GalTransl 추출·삽입 도구의 VNTextPatch 모드는 엔진 종류에 따라 기본으로 sjis 또는 unicode(utf8) 인코딩으로 스크립트를 넣습니다.

* **방법 1 사용**
(참고: 이 방식은 지금 버그가 있어 일부 엔진이 멈춥니다) 넣기 전에 "GBK 인코딩으로 삽입"을 선택합니다. 이 방식에서는 GBK가 지원하지 않는 문자(예: 음표 ♪)가 모두 빈칸으로 바뀝니다.
그다음 엔진을 고칠 ollydbg나 windbg 도구가 필요합니다. [여기서 내려받기](https://down.52pojie.cn/Tools/Debuggers/)
마지막으로 [Dir-A의 강좌](https://space.bilibili.com/8144708/)(중국어)에서 중단점을 걸고 수정하는 방법을 배웁니다. 리버싱 경험이 전혀 없다면 어려울 수 있지만 영상을 따라 여러 번 시도해 보세요.

* **방법 2 사용**
스크립트를 넣을 때 아무것도 선택하지 않습니다. "sjis_ext.bin 포함 문자: xxx"라는 안내가 나오면 프로그램이 sjis 인코딩으로 넣었고, 표시할 수 없는 문자를 script_cn 폴더의 sjis_ext.bin에 담아 sjis 터널 방식에서 쓰도록 했다는 뜻입니다.

**jis 터널**: 역시 arcusmaximus의 VNTranslationTools 프로젝트에 있는 [VNTextProxy 구성 요소](https://github.com/arcusmaximus/VNTranslationTools#vntextproxy)입니다. VNTextPatch는 텍스트를 스크립트에 넣을 때 sjis가 지원하지 않는 문자를 sjis에서 정의되지 않은 문자로 잠시 바꿔 두고, VNTextProxy가 DLL 하이재킹으로 게임을 HOOK해 그 문자를 만나면 원래대로 되돌립니다.

sjis 터널 방식을 쓸 때는 `script_cn`의 `sjis_ext.bin`을 게임 폴더로 옮기고, useful_tools\VNTextProxy의 dll을 하나씩 게임 폴더에 넣어(보통 version.dll부터 시도하거나 PEID/DIE 등으로 임포트 테이블 확인) 게임을 실행해 봅니다. 어느 dll이 게임을 제대로 hook해 표시되지 않던 텍스트가 나오는지 확인합니다(잘못되면 그 부분이 비어 있음). 안 되면 그 DLL을 지우고 다음 것을 시도합니다. [자세한 설정](https://github.com/XD2333/GalTransl/tree/main/useful_tools/VNTextProxy)

**jis 치환**: AtomCrafty의 [UniversalInjectorFramework(범용 삽입 프레임워크)](https://github.com/AtomCrafty/UniversalInjectorFramework#character-substitution) 프로젝트입니다. 역시 DLL 하이재킹으로 게임을 HOOK하며, 설정에 따라 어떤 문자를 다른 문자로 바꿀 수 있고 인코딩에 제한이 없습니다. 원본 작성자는 jis가 지원하지 않는 간체 한자와 jis가 지원하는 일본 한자의 대응을 규칙에 따라 정리한 [치환 사전](https://github.com/XD2333/GalTransl_DumpInjector/blob/main/hanzi2kanji_table.txt)을 만들어 자주 쓰는 간체자의 99.99%를 표시할 수 있게 했고(hanzi2kanji_table.txt), 치환 기능을 GalTransl 추출·삽입 도구에 넣었습니다(새 소식: [SExtractor](https://github.com/satan53x/SExtractor)도 치환을 지원하며 더 쓰기 편합니다). 치환한 뒤 UniversalInjectorFramework의 동적 Hook 치환으로 게임 안에서 그 일본 한자를 다시 간체자로 바꿔 정상 표시합니다.

sjis 치환 방식을 쓸 때는 먼저 GalTransl 추출·삽입 도구로 텍스트를 한 번 넣어 게임이 지원하지 않는 문자 목록을 얻습니다(넣은 뒤 "sjis_ext.bin 포함 문자: xxx" 안내가 나옴). 그다음 "sjis 치환 방식으로 삽입"을 선택하고 그 문자들을 오른쪽 입력란에 복사해 넣은 뒤 다시 삽입합니다. 삽입하면 sjis 치환 방식 설정이 만들어집니다.

useful_tools/UniversalInjectorFramework 폴더를 열면 여기에도 dll이 여러 개 있으니 하나씩 시도합니다. 보통 winmm.dll부터 시도하며, 폴더의 uif_config.json도 함께 게임 폴더에 복사한 뒤 이 json을 편집해 GalTransl 추출·삽입 도구가 준 설정대로 `source_characters`와 `target_characters`를 채웁니다.
그다음 게임을 실행했을 때 게임이 정상 동작하고 아래와 같은 콘솔이 뜨면
![img_terminal](./img/img_terminal.png)
대부분 성공입니다. 그렇지 않으면 그 DLL을 지우고 다음 것을 시도합니다.
참고: UniversalInjectorFramework도 sjis 터널 방식을 지원합니다. `tunnel_decoder`를 `True`로 하고 `mapping`에 sjis_ext.bin 포함 문자를 넣으면 됩니다.
참고: UniversalInjectorFramework의 콘솔 창은 숨길 수 있습니다. [자세한 설정 파일 안내](https://github.com/XD2333/GalTransl/tree/main/useful_tools/UniversalInjectorFramework)

</details>

## GalTransl 핵심 기능 소개
GPT 사전, 캐시, 일반 사전, 문제 찾기 등의 기능을 소개합니다.
(클릭해서 자세히 보기)
<details>

<summary>

### GPT 사전
&ensp;&ensp;&ensp;&ensp;GPT 사전 시스템은 GalTransl로 번역할 때 품질을 높이는 핵심 기능입니다. 설정을 보충해 주는 방식으로 번역 품질을 크게 높이며, GPT 번역이 기존 기계 번역과 다른 핵심입니다. gpt35, gpt4, newbing에 적용됩니다.
프로그램 폴더의 `Dict` 폴더에 "공통GPT사전.txt"가 있고, 프로젝트 폴더에 "项目GPT字典.txt(프로젝트 GPT 사전, 파일 이름은 프로그램이 쓰는 그대로)"를 새로 만들 수 있습니다. 보통 인명 정의는 프로젝트 사전에, 번역 품질을 전반적으로 높이는 어휘는 공통 사전에 씁니다.

</summary>

* 예를 들어 미리 각 인물 이름의 번역을 정하고 그 인물의 설정(성별, 대략적인 나이, 직업 등)을 적어 둘 수 있습니다. 이 설정을 GPT에 자동으로 전달하면 알맞은 인칭 대명사(그/그녀)와 호칭을 고르고, 이름이 가나일 때의 번역 표기를 고정할 수 있습니다.
* 또 GPT가 늘 틀리게 번역하는 단어를 보충할 수 있습니다. 약간의 설명을 덧붙이면 더 잘 이해합니다.

---

* 아래 예로 GPT 사전에 인물 설정을 넣는 법을 익혀 봅시다. 한 줄의 형식은 `일본어[Tab]번역[Tab]설명(생략 가능)`이며, 구분자는 반드시 **TAB**입니다.
```
フラン	프랑	name, lady, teacher
笠間	카사마	笠間 陽菜乃’s lastname, girl
陽菜乃	히나노	笠間 陽菜乃's firstname, girl
张三	장산	player's name, boy
$str20	$str20	player's codename, boy
```
이 항목들은 모두 인물을 정의합니다.
* 첫 줄은 GPT에게 "가나 フラン의 번역은 프랑이고, 사람 이름이며 여성이고 선생님이다"라고 알려 주는 것입니다. 그러면 GPT가 フラン先生을 번역할 때 프랑 의사가 아니라 프랑 선생님으로 번역합니다.
* 둘째, 셋째 줄은 같은 사람의 성과 이름입니다. 시험해 보니 성과 이름을 두 줄로 나눠 써야 GPT3.5가 알아봅니다.
* 넷째 줄은 주인공을 정하는 권장 방식입니다. **원어와 번역이 같아도 한 번 더 적어 주세요**.
* 다섯째 줄은 주인공이 스크립트에서 이름 대신 자리표시자로 쓰일 때의 권장 방식입니다.
* **설정은 너무 복잡하게 쓰지 마세요.** GPT가 이상한 상상을 많이 하게 됩니다.

---

* 아래 예로 GPT 사전에 낯선 단어를 넣는 법을 익혀 봅시다. 형식은 마찬가지로 `일본어[Tab]번역[Tab]설명(생략 가능)`이며 구분자는 **TAB**입니다.
```
大家さん  집주인
あたし	나/나야	use '나야' when being cute
```
* GPT가 잘 모르는 단어(예: "大家さん")이고 뜻이 비교적 하나로 정해져 있다면 이렇게 공통 GPT 사전에 넣으면 됩니다. 설명은 꼭 필요하지 않습니다.
* 둘째 줄은 번역에 여러 뜻 "나/나야"를 적고 설명에 "귀엽게 굴 때는 나야를 쓴다"고 적었습니다. GPT3.5는 그렇게 영리하지 않지만 GPT4는 대체로 잘 활용합니다.

프로그램 폴더의 `Dict` 폴더에 "공통GPT사전.txt"가 있고, 프로젝트 폴더에는 "项目GPT字典.txt"를 둡니다. 보통 인명 정의는 프로젝트 사전에, 번역 품질을 전반적으로 높이는 어휘는 공통 사전에 씁니다.
이번에 GPT에 보내는 이름과 문장에 그 단어가 있을 때만 그 단어의 설명이 이번 대화에 들어갑니다.
**그렇다고 아무 단어나 넣지는 마세요.** ~~다 넣으면 오히려 해가 됩니다~~. **인물 설정**과 **늘 틀리게 번역하는 단어**만 쓰는 것을 권장합니다.

실행 중에는 사전이 매 요청에 동적으로 표시됩니다.

![img_start](./img/img_start.png)

</details>

<details>

<summary>

### 일반 사전
GalTransl의 일반 사전은 "번역 전 사전"과 "번역 후 사전"으로 나뉩니다. 번역 전 사전은 번역 전에 일본어를 a에서 b로 바꾸고, 번역 후 사전은 번역된 문장을 a에서 b로 바꿉니다.

</summary>

번역 전 사전은 혀 짧은 발음 등을 바로잡거나, 같은 뜻을 가진 여러 단어를 먼저 하나로 맞춰 GPT 사전 입력을 줄이는 데 주로 씁니다.

번역 후 사전은 흔히 보는 사전으로, 번역 후 어떤 단어를 다른 단어로 바꿉니다. 여기에 "조건 사전"이라는 기능을 더했습니다. 조건 사전은 바꾸기 전에 판단 단계를 하나 추가해 잘못된 치환이나 과도한 치환을 막습니다.
한 줄 형식은 `pre_jp/post_jp[tab]판단어[tab]찾을 말[tab]바꿀 말`입니다.
* pre_jp/post_jp는 판단어를 찾을 위치이며, 정의는 "번역 캐시" 절에서 설명합니다
* 판단어: 찾을 위치(pre_jp/post_jp)에서 판단어를 찾았을 때만 뒤의 치환이 실행됩니다.
* 판단어 앞에 "!"를 붙이면 "없으면 바꾸기"가 되고, 그렇지 않으면 보통 "있으면 바꾸기"입니다.
* 판단어는 `[or]`나 `[and]`로 이을 수 있습니다. `[or]`로 여럿 이으면 "하나라도 맞으면 바꾸기", `[and]`로 이으면 "모두 맞아야 바꾸기"입니다.
* 찾을 말, 바꿀 말은 일반 사전과 같이 a를 b로 바꿉니다.

</details>

<details>

<summary>

### 번역 캐시
번역을 시작하면 transl_cache 폴더에서 번역 캐시를 볼 수 있습니다.
</summary>

번역 캐시는 json_jp와 하나씩 대응합니다. 번역하는 동안 결과는 먼저 캐시에 기록되고, 파일 하나가 다 번역되어야 json_cn(결과 폴더)에 나타납니다.

먼저 요점을 정리하면:
1. 어떤 문장을 다시 번역하고 싶으면 해당 번역 캐시 파일을 열어 그 문장의 pre_zh 줄을 통째로 지웁니다(**빈 줄을 남기지 마세요**)
2. 한 구간을 통째로 다시 번역하려면 해당 object 블록 여러 개를 지우고, 파일 하나를 다시 번역하려면 그 번역 캐시 파일을 지웁니다.
3. GalTransl이 번역하는 동안에는 번역 중인 파일의 캐시를 고치지 마세요. 고쳐도 다시 덮어쓰입니다.
4. json_cn 결과 파일 = 번역 캐시의 pre_zh/proofread_zh + 번역 후 사전 치환 + 대화 괄호 복원
5. 새 post_jp가 캐시의 post_jp와 다르면 다시 번역합니다. 보통 번역 전 사전을 새로 추가했을 때 생깁니다

다음은 번역 캐시의 전형적인 예입니다(현재 버전의 필드 이름은 pre_src/post_src/pre_dst/proofread_dst 등이며 아래는 원본 설명의 옛 이름입니다).
```json
    {
        "index": 4,
        "name": "",
        "pre_jp": "欠品していたコーヒー豆を受け取ったまでは良かったが、\r\n帰り道を歩いていると汗が吹き出してくる。",
        "post_jp": "欠品していたコーヒー豆を受け取ったまでは良かったが、\r\n帰り道を歩いていると汗が吹き出してくる。",
        "pre_zh": "领取了缺货的咖啡豆还好，\r\n但是走在回去的路上就汗流浃背了。",
        "proofread_zh": "领了缺货的咖啡豆倒是没问题，\r\n可是走在回去的路上，汗水就冒了出来。",
        "trans_by": "NewBing",
        "proofread_by": "NewBing",
    },
```
각 필드의 뜻:
* 기본 필드:
`index`  번호
`name`  인물 이름
`pre_jp`  원래 일본어
`post_jp`  처리한 일본어. 일반적으로 post_jp = pre_jp에서 대화 괄호 제거 + 번역 전 사전 치환. 코드를 다룰 줄 알면 여기에 직접 처리를 넣을 수도 있습니다
`pre_zh`  원래 번역문
`proofread_zh`  교정한 번역문
(post_zh는 없으며 결과 폴더에 있습니다.)
`trans_by`  번역 엔진/번역자
`proofread_by`  교정 엔진/교정자
`problem`  문제 기록. 아래 자동 오류 검사 참고.
`post_zh_preview`  json_cn 미리보기용이며 **여기를 고쳐도 json_cn에는 반영되지 않습니다**. `pre_jp`/`proofread_zh`를 고치세요

* Emeditor로 캐시를 고치는 방법: 파일 하나를 골라 오른쪽 클릭 - Emeditor로 연 다음 transl_cache의 모든 파일을 선택해 끌어 놓습니다.
이때 탭이 자리를 많이 차지하면 탭을 오른쪽 클릭 - 탭 사용자 지정에서 "탭이 맞지 않을 때"를 "없음"으로 바꾸면 탭이 한 줄로 표시됩니다(Emeditor 전문가판 필요).
그다음 Ctrl+F로 관심 있는 키워드(예: problem, proofread_comment)를 검색하고 "그룹의 모든 문서 검색"을 선택하면 모든 파일에서 빠르게 찾을 수 있고, 추출을 누르면 모든 문제를 한눈에 볼 수 있습니다.

* **VSCode**도 캐시를 고치기에 아주 좋습니다. VSCode로 캐시 폴더를 열고 problem 등을 전체 검색하면 모든 문제를 빠르게 찾을 수 있습니다.

* 고칠 내용을 정했으면 해당 문장의 `pre_zh` 또는 `proofread_zh`를 바로 고친 뒤 **GalTransl을 한 번 더 실행**하면 곧 새 json_cn이 만들어집니다.

</details>

<details>

<summary>

### 자동 오류 검사

GalTransl은 번역 결과를 오랫동안 관찰해 만든 규칙으로 문제를 자동으로 찾는 시스템을 갖추고 있습니다.
</summary>
문제 찾기 기능은 각 프로젝트의 `config.yaml`에서 켜며 기본 설정은 다음과 같습니다. 문제 이름은 실제 설정값이므로 중국어 그대로 둡니다.

```yaml
# 자동 문제 분석 설정. - 앞에 #을 붙이면 끌 수 있음
problemAnalyze:
  problemList: # 찾을 문제 목록
    - 词频过高 # 단어 반복이 20회 초과
    - 标点错漏 # 문장부호를 더하거나 빠뜨림
    - 残留日文 # 일본어 히라가나·가타카나 잔류
    - 丢失换行 # 줄바꿈이 부족함. 보통 문제없음
    - 多加换行 # 원문보다 줄바꿈이 많음. 화면을 넘칠 수 있음
    - 比日文长 # 일본어보다 1.3배 이상 김
    - 字典使用 # GPT 사전대로 번역하지 않음
    - 语言不通 # 대상 언어로 번역되지 않은 것으로 의심. 중국어 번역 시 GBK 외 문자가 있는지 검사
    #- 引入英文 # 원래 영어가 없는데 번역문에 영어가 들어감
    #- 比日文长严格 # 엄격 검사. 일본어보다 길면 안 됨
```

현재 위 문제들을 찾을 수 있습니다. #으로 주석 처리된 항목은 주석을 풀어 켜고, 반대로 #을 붙여 해당 문제 검사를 끌 수 있습니다.
이 문제 검사는 중국어 출력을 기준으로 만들어졌습니다. 이 Fork의 `Ollama-ko` 엔진은 한국어 전용 검사와 품질 리포트를 따로 사용합니다.

찾은 문제는 번역 캐시에 저장됩니다(번역 캐시 절 참고). Emeditor로 problem 키워드를 한꺼번에 추출하면 현재 모든 문제를 볼 수 있으며, 캐시의 pre_jp를 고쳐 문제를 바로잡습니다.

(새 기능) 이제 config.yaml에 retranslKey를 설정해 특정 문제를 한꺼번에 다시 번역할 수 있습니다. 예: retranslKey: "残留日文"

</details>

## 설정 파일과 번역 엔진 설정

ForGal-json, ForGal-markdown, ForNovel은 기본으로 다중 턴 대화 번역을 사용합니다. 같은 파일 조각 안의 연속된 배치가 대화를 공유하며, 첫 턴에 전체 규칙과 번역 지침을 보내고 이후 턴에는 새 텍스트와 이번 턴의 용어표를 보냅니다. 스트리밍과 비스트리밍 응답의 생각 내용은 기록 메시지와 함께 다시 전달됩니다. Sakura/GalTransl 로컬 모델은 기존 흐름을 유지합니다.

데스크톱 앱의 "번역 설정"에서 다중 턴 번역을 켜고 끌 수 있고 "고급 설정"에서 세션 제한을 조정합니다. 프로젝트 설정의 `common`에서도 설정할 수 있습니다.

```yaml
gpt.multiTurn: true
gpt.multiTurn.maxTurns: 8
gpt.multiTurn.maxChars: 24000
gpt.contextNum: 8
```

턴 수나 문자 예산(생각 내용 포함)이 한도에 이르면 새 세션을 열고 최근 `gpt.contextNum`개의 번역문을 보충합니다. 문자 예산은 기록을 제한하는 데 쓰이며 한 배치의 입력을 자르지 않습니다. 모델 컨텍스트가 작으면 요청당 문장 수도 줄이세요. 캐시 적중으로 건너뛴 구간은 해당 위치에서 문맥을 다시 만듭니다. `gpt.multiTurn: false`로 하면 단일 턴 요청으로 돌아가고, `gpt.contextNum: 0`은 앞 문맥 보충만 끄며 다중 턴 대화는 끄지 않습니다. API는 턴마다 전체 대화 기록을 받으므로 비용은 API의 컨텍스트 캐시 정책에 따라 달라집니다.

데스크톱 앱은 그래픽 인터페이스(왼쪽 "모델 설정" 페이지)로 번역 백엔드 설정을 관리하므로 YAML을 직접 편집할 필요가 없습니다. 프로젝트 설정은 "설정 편집" 페이지에서 바꿉니다.

명령줄 버전의 자세한 설정 항목은 `config.yaml` 설정 파일의 주석을 읽으면 됩니다(주석은 원본 기준 중국어). 로컬 Ollama 한국어 번역 설정은 [README_KO_OLLAMA.md](README_KO_OLLAMA.md)에 있습니다.


## 개발과 빌드

<details>
<summary>개발 환경 설정 (개발자/고급 사용자)</summary>

* **명령줄판 (개발자/고급 사용자)**
  명령줄 버전을 쓰거나 개발에 참여하려면:

  1. [이 프로젝트를 내려받거나](https://github.com/XD2333/GalTransl/releases/) 저장소를 clone해 원하는 위치에 풉니다
  2. Python 3.11.9를 설치합니다. [내려받기](https://www.python.org/downloads/release/python-3119/)
  **설치할 때 아래쪽 add Python to path를 선택하세요**
  3. Python 의존성 설치: `安装、更新依赖.bat`(의존성 설치·업데이트)를 두 번 클릭하거나 `pip install -r requirements.txt`를 직접 실행합니다

### 데스크톱 앱 개발 모드

아래 단계는 Windows 기준입니다. 소스에서 데스크톱 앱을 실행하려면 먼저 이 저장소 소스를 clone하거나 내려받고, 저장소 루트(`run_desktop_dev.bat`이 있는 폴더)에서 터미널을 엽니다.

**처음 환경 준비**

1. [Python 3.11.9](https://www.python.org/downloads/release/python-3119/)와 [Node.js LTS](https://nodejs.org/)를 설치하고 `python`, `node`, `npm`이 PATH에 있는지 확인합니다.
2. 기본 데스크톱 창을 띄우려면 [Rust](https://www.rust-lang.org/tools/install)를 설치하고 기본 Windows MSVC 툴체인을 씁니다. Rust를 설치할 때 VC 툴체인과 SDK 설치 안내가 나오면 함께 설치합니다.
3. 설치를 마치면 터미널을 다시 열고 저장소 루트에서 아래 명령을 실행해 프로젝트 전용 Python 환경을 만들고 의존성을 설치합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm.cmd --prefix desktop ci
```

**평소 실행**

저장소 루트의 `run_desktop_dev.bat`를 두 번 클릭하거나 터미널에서 실행합니다.

```powershell
.\run_desktop_dev.bat
```

실행 스크립트는 저장소의 `.venv`를 자동으로 활성화하고, 기본 위치 `%USERPROFILE%\.cargo\bin`에 설치된 Cargo를 인식합니다. 스크립트는 Python 백엔드와 프런트엔드 개발 콘솔을 각각 엽니다.

- 백엔드 주소는 [http://127.0.0.1:12333](http://127.0.0.1:12333), 프런트엔드 개발 주소는 [http://127.0.0.1:1420/](http://127.0.0.1:1420/)입니다.
- Cargo가 있으면 Tauri 데스크톱 창을 빌드해 엽니다. 처음 실행할 때는 Rust 의존성을 내려받아 빌드하므로 콘솔이 끝날 때까지 기다리세요.
- Cargo가 없으면 브라우저 개발 모드로 실행합니다. 프런트엔드 주소를 직접 열면 됩니다. 이 모드는 Rust, C++ 빌드 도구, WebView2가 필요 없습니다.
- 프런트엔드 코드를 고치면 바로 반영되고, Rust 코드를 고치면 자동으로 다시 빌드합니다. Python 백엔드 코드를 고친 뒤에는 백엔드를 다시 시작해야 합니다.
- 화면 언어는 기본 한국어이며 "설정 → 화면 → 인터페이스 언어"에서 바꿉니다. 백엔드 메시지 언어는 환경 변수 `GT_LANG`(`ko`/`zh-cn`/`en`)으로 바꿉니다.

**주의 사항**

- `.venv`와 의존성은 처음 한 번만 만들고 설치하면 됩니다. 소스를 업데이트한 뒤 의존성이 바뀌었다면 위의 Python 의존성 설치 명령과 `npm.cmd --prefix desktop ci`를 다시 실행합니다.
- `ModuleNotFoundError`가 나면 의존성을 저장소의 `.venv`에 설치했는지 확인하세요. 실행 스크립트는 Python 의존성을 자동으로 설치하지 않습니다.
- 실행하기 전에 `12333`과 `1420` 포트를 다른 인스턴스가 쓰고 있지 않은지 확인하세요. 끝낼 때는 백엔드와 프런트엔드 개발 콘솔에서 각각 `Ctrl+C`로 서비스를 멈춘 뒤 콘솔을 닫습니다. 데스크톱 창만 닫으면 따로 실행 중인 Python 백엔드는 멈추지 않습니다.
- 백엔드는 포트를 혼자 사용합니다. 중복 실행하면 새 백엔드가 포트 사용 중이라고 알리고 종료하며 기존 백엔드는 계속 실행됩니다. 이 수정을 적용한 뒤에는 예전에 실행한 백엔드를 모두 멈추고 실행 스크립트를 다시 실행하세요.

### Linux x86_64 개발과 빌드

현재 Linux 지원 범위는 x86_64이며 ARM은 포함하지 않습니다.

Ubuntu 22.04+/Debian 12+에서는 다음 의존성을 설치합니다.

```bash
sudo apt-get update
sudo apt-get install -y build-essential curl file libssl-dev patchelf rpm \
  libwebkit2gtk-4.1-dev libayatana-appindicator3-dev librsvg2-dev
```

Fedora에서는:

```bash
sudo dnf install webkit2gtk4.1-devel openssl-devel curl wget file \
  libappindicator-gtk3-devel librsvg2-devel rpm-build dpkg
```

처음 준비와 평소 실행:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm --prefix desktop ci
./run_desktop_dev.sh
```

스크립트는 Python 백엔드를 먼저 시작한 뒤 Tauri 데스크톱 앱을 시작합니다. Cargo가 없으면 브라우저 개발 모드로 대신 실행합니다.

Linux 배포 패키지 빌드:

```bash
python build_linux_x64.py --no-bundles
```

Linux CI와 정식 배포는 휴대용 패키지만 만듭니다. 로컬에서 설치 패키지를 시험하려면 `--formats deb,appimage`로 Tauri 설치 패키지 형식을 고릅니다.

출력은 `release/`에 있습니다.

- `GalTransl_*_linux_x86_64.tar.gz`
- `GalTransl_*_linux_x86_64.tar.gz`

정식 배포 패키지는 Ubuntu 22.04 또는 같은 glibc 기준의 환경에서 빌드해야 합니다. 앱 설정은 `$XDG_CONFIG_HOME/GalTransl`에, 사용자 공통 사전은 `$XDG_DATA_HOME/GalTransl/Dict`에 저장합니다. 공통 번역 지침과 에이전트 세션은 각각 `$XDG_DATA_HOME/GalTransl/translation_guidelines`와 `$XDG_DATA_HOME/GalTransl/agent_sessions`에 저장합니다. XDG 환경 변수가 없으면 `~/.config`와 `~/.local/share`를 씁니다. 설치 폴더의 사전과 지침은 처음 복사할 원본으로만 쓰입니다. Windows는 계속 프로그램 폴더의 설정과 사전을 사용합니다.

Linux 지원은 모든 외부 도구가 이식되었다는 뜻이 아닙니다. 예를 들어 msg-tool 플러그인에 포함된 `res/msg_tool.exe`는 Windows 프로그램이므로 관련 스크립트 형식의 추출/되쓰기는 Linux에서 바로 쓸 수 없습니다.


### macOS 개발과 빌드

현재 macOS 빌드는 Intel(x86_64)과 Apple Silicon(arm64)을 지원합니다. Xcode Command Line Tools, Python 3.11, Node.js, Rust와 프로젝트 의존성이 필요합니다.

```bash
npm --prefix desktop ci
python build_macos.py
```

빌드 결과는 `release/`에 있으며 해당 아키텍처의 `.dmg`와 휴대용 `.tar.gz`가 포함됩니다. 서명하지 않은 빌드는 macOS Gatekeeper에 막힐 수 있습니다. 정식 배포할 때는 Apple Developer 서명과 공증을 설정해야 합니다.

</details>

<details>
<summary>자동 빌드와 배포 (관리자)</summary>

### 자동 빌드와 배포

[Build and draft release](https://github.com/GalTransl/GalTransl/actions/workflows/build-release.yml)는 Windows x64, Ubuntu 22.04 x86_64, macOS Intel/Apple Silicon 기본 runner에서 데스크톱 패키지를 빌드합니다.

배포 검수는 압축을 푼 백엔드를 별도 폴더에서 시작하고, 임시 설정과 사용자 데이터 폴더를 써서 TXT, JSON, EPUB 파일을 실제로 해석합니다. macOS는 DMG를 마운트해 그 안의 `.app`을 복사하고 버전, 프런트엔드·백엔드 아키텍처, 리소스를 확인한 뒤 앱 패키지 안의 백엔드를 시작해 같은 검사를 합니다.

| 실행 방식 | 결과 |
| --- | --- |
| `main` 업데이트, PR 제출 | 테스트, Windows·Linux·macOS 빌드, 이번 Actions artifacts 업로드 |
| Actions → Build and draft release → Run workflow | 수동 시험 패키징. artifacts만 만들며 Release를 만들거나 바꾸지 않음 |
| 버전 tag 푸시(`8.2.0` 또는 `v8.2.0`) | Windows, Linux, macOS 모두 테스트·빌드·패키지 후 검사를 통과하면 초안 Release를 만들고 첨부 파일 업로드 |

**시험 빌드 내려받기**: 워크플로 실행 상세에서 **Artifacts**를 필요한 만큼 내려받습니다(모두 14일 보관). Linux와 macOS 휴대용 패키지는 `GalTransl_<버전>_linux_x86_64.tar.gz`, `GalTransl_<버전>_macos_x86_64.tar.gz`, `GalTransl_<버전>_macos_arm64.tar.gz`라는 이름으로 제공되며 한 번만 풀면 실행 권한이 유지된 채 쓸 수 있습니다. Windows의 `GalTransl-windows-x64`와 macOS 아키텍처별 `dmg` artifact는 여전히 Actions가 바깥 ZIP으로 감싸 제공합니다.

**새 버전 배포 (관리자)**:

1. `GalTransl/__init__.py`의 `GALTRANSL_VERSION`을 올리고, 이 워크플로가 포함된 코드를 커밋해 푸시합니다.
2. 소스 버전과 같은 새 tag를 푸시합니다. 아래는 아직 배포하지 않은 `8.2.0`을 예로 든 것이며 실제로는 이번 버전으로 바꿉니다.
   ```bash
   git tag 8.2.0
   git push origin 8.2.0
   ```
3. 워크플로가 성공할 때까지 기다린 뒤 **Releases**에서 자동 생성된 초안을 확인하고, 배포 설명을 보충한 다음 **Publish release**를 직접 누릅니다. 업로드 중에 초안을 먼저 배포하지 마세요.

tag는 `X.Y.Z`와 `vX.Y.Z`를 지원하며 소스 버전과 같아야 합니다. 기존 tag(예: `8.1.0`)를 옮기거나 다시 쓰지 마세요. 정식 첨부 파일은 Windows `.zip`, Linux `.tar.gz`, macOS Intel/Apple Silicon의 `.dmg`와 `.tar.gz`, `SHA256SUMS.txt`입니다. 첨부 파일을 모두 내려받은 뒤 `sha256sum -c SHA256SUMS.txt`로 확인할 수 있으며, Windows에서는 PowerShell `Get-FileHash <파일> -Algorithm SHA256`으로 목록과 대조합니다.

이 과정은 GitHub 내장 `GITHUB_TOKEN`만 쓰며 별도의 PAT나 번역 API 키가 필요 없습니다. 배포 job만 `contents: write`를 요청합니다. 조직 정책이 쓰기를 막으면 관리자가 이 저장소의 Release 쓰기 권한을 허용해야 합니다. 실패하면 다시 실행할 수 있습니다. 기존 초안은 자동 빌드 첨부 파일을 갱신하되 직접 고친 제목과 설명은 유지하며, 이미 정식 배포된 Release는 덮어쓰기를 거부합니다. tag를 골라 수동 실행해도 artifacts만 만듭니다.

빌드 후에는 최종 휴대용 패키지를 풀어 소스 폴더 밖에서 백엔드를 시작하고 버전과 플러그인 목록을 확인합니다. 이 검사가 데스크톱 GUI 전체, 각 설치 프로그램, 모든 플러그인의 기능 테스트를 대신하지는 않습니다.

</details>
