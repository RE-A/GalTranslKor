import os
import logging
from time import localtime
import threading
from GalTransl.Utils import check_for_tool_updates

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

PROGRAM_SPLASH1 = r"""
   ____       _ _____                    _ 
  / ___| __ _| |_   _| __ __ _ _ __  ___| |
 | |  _ / _` | | | || '__/ _` | '_ \/ __| |
 | |_| | (_| | | | || | | (_| | | | \__ \ |
  \____|\__,_|_| |_||_|  \__,_|_| |_|___/_|                 

------Translate your favorite Galgame------
"""

PROGRAM_SPLASH2 = r"""
   ______      ________                      __
  / ____/___ _/ /_  __/________ _____  _____/ /
 / / __/ __ `/ / / / / ___/ __ `/ __ \/ ___/ / 
/ /_/ / /_/ / / / / / /  / /_/ / / / (__  ) /  
\____/\__,_/_/ /_/ /_/   \__,_/_/ /_/____/_/   
                                             
-------Translate your favorite Galgame-------
"""

PROGRAM_SPLASH3 = r'''

   ___              _     _____                                     _    
  / __|   __ _     | |   |_   _|    _ _   __ _    _ _      ___     | |   
 | (_ |  / _` |    | |     | |     | '_| / _` |  | ' \    (_-<     | |   
  \___|  \__,_|   _|_|_   _|_|_   _|_|_  \__,_|  |_||_|   /__/_   _|_|_  
_|"""""|_|"""""|_|"""""|_|"""""|_|"""""|_|"""""|_|"""""|_|"""""|_|"""""| 
"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-' 

--------------------Translate your favorite Galgame--------------------
'''

PROGRAM_SPLASH4 = r"""
     _____)           ______)                 
   /             /)  (, /                  /) 
  /   ___   _   //     /  __  _  __   _   //  
 /     / ) (_(_(/_  ) /  / (_(_(_/ (_/_)_(/_  
(____ /            (_/                        

-------Translate your favorite Galgame-------
"""
ALL_BANNERS = [PROGRAM_SPLASH1, PROGRAM_SPLASH2, PROGRAM_SPLASH3, PROGRAM_SPLASH4]
PROGRAM_SPLASH = ALL_BANNERS[localtime().tm_mday % 4]

GALTRANSL_VERSION = "8.4.3"
AUTHOR = "xd2333"
CONTRIBUTORS = "ryank231231, PiDanShouRouZhouXD, Noriverwater, Isotr0py, adsf0427, pipixia244, gulaodeng, sakura-umi, lifegpc, natsumerinchan, szyzbg"

CONFIG_FILENAME = "config.yaml"
INPUT_FOLDERNAME = "gt_input"
OUTPUT_FOLDERNAME = "gt_output"
CACHE_FOLDERNAME = "transl_cache"
# 全局翻译规范目录名（程序根目录下）：各项目的 common.gpt.translation_guideline 从这里选一份
GUIDELINES_FOLDERNAME = "translation_guidelines"
# 项目没配置全局规范时兜底读的那一份（见 Backend/BaseTranslate.py）：
# 界面上不允许删它，否则那些项目的翻译会直接报"读不到规范"。
DEFAULT_GUIDELINE_NAME = "Basic.md"
TRANSLATOR_SUPPORTED = {
    "auto-translate": {
        "zh-cn": "基于文本自动选择合适的模板并在翻译报错时轮动切换。",
        "en": "Automatically selects the appropriate template based on the text and rotates templates when translation fails.",
        "ko": "텍스트에 맞는 템플릿을 자동으로 고르고, 번역 오류가 나면 템플릿을 바꿔 가며 시도합니다.",
    },
    "Ollama-ko": {
        "zh-cn": "通过 Ollama 将日语对白和叙述翻译为韩语，保留批次上下文。",
        "en": "Japanese-to-Korean translation with Ollama and sequential batch context.",
        "ko": "로컬 Ollama로 일본어 대사·지문을 한국어로 번역하며 배치 문맥을 유지합니다.",
    },
    "ForGal-json": {
        "zh-cn": "(openai接口)翻译Gal时使用，json格式输入，兼容性好。",
        "en": "Customized template for Gal translation, json input. ",
        "ko": "(OpenAI API) 갈게임 번역용 템플릿. json 형식 입력으로 호환성이 좋습니다.",
    },
    "ForGal-tool": {
        "zh-cn": "(openai接口)通过译文补丁工具分组翻译Gal，需支持函数工具调用，批次间不保留多轮对话。",
        "en": "Gal translation in groups using a translation patch tool; requires function calling support. Each batch is independent.",
        "ko": "번역 패치 도구로 갈게임을 묶음 단위로 번역합니다. function calling 지원이 필요하며 배치마다 독립적입니다.",
    },
    "ForNovel-tool": {
        "zh-cn": "(openai接口)通过译文补丁工具翻译小说，输入不带name字段，批次间不保留多轮对话。",
        "en": "Novel translation using a patch tool, without name fields. Each batch is independent.",
        "ko": "패치 도구로 소설을 번역하며 이름 필드는 없습니다. 배치마다 독립적입니다.",
    },
    "ForNovel": {
        "zh-cn": "(openai接口)翻译轻小说等其他文本时使用，区别是输入不带name字段。",
        "en": " Customized template for Novel translation. ",
        "ko": "소설 번역용 템플릿.",
    },
    "ForGal-markdown": {
        "zh-cn": "(openai接口)翻译Gal时使用，Markdown表格输入和输出，句内换行使用<br>。",
        "en": " Gal translation using Markdown tables for input and output, with <br> line breaks. ",
        "ko": "Markdown 표로 입출력하는 갈게임 번역 템플릿. 줄바꿈은 <br>입니다.",
    },
    "galtransl-v3": {
        "zh-cn": "(sakura接口)为翻译Gal基于Sakura进一步优化的本地模型",
        "en": "Further optimized local small model based on Sakura for Gal translation",
        "ko": "Sakura 기반으로 갈게임 번역에 더 최적화한 로컬 소형 모델(중국어 출력)",
    },
    "sakura-v1.0": {
        "zh-cn": "(sakura接口)为翻译轻小说/Gal开展大规模训练的本地模型，具有多个型号和大小",
        "en": "(For v1.0 prompt) Locally trained model for light novel/Gal translation, available in multiple sizes",
        "ko": "(v1.0 프롬프트용) 라이트노벨/갈게임 번역용으로 학습한 로컬 모델. 여러 크기가 있습니다(중국어 출력)",
    },
    "GenDic": {
        "zh-cn": "(openai接口)自动化构建GPT字典，需要接大模型如Deepseek-V3",
        "en": "Automatically build GPT dictionary, requires a large model, recommended GPT4/Claude-3/Deepseek-V3",
        "ko": "GPT 사전을 자동으로 만듭니다. 큰 모델이 필요하며 GPT4/Claude-3/Deepseek-V3를 권장합니다",
    },
    "rebuildr": {
        "zh-cn": "重建结果 用译前译后字典通过缓存刷写结果json -- 跳过翻译和写缓存",
        "en": "Rebuild results - Use pre/post translation dictionary to rewrite result json via cache - Skip translation and cache writing",
        "ko": "결과 다시 만들기 - 번역 전/후 사전으로 캐시에서 결과 json을 다시 씀 - 번역과 캐시 쓰기는 건너뜀",
    },
    "rebuilda": {
        "zh-cn": "重建缓存和结果 用译前译后字典刷写缓存+结果json -- 跳过翻译",
        "en": "Rebuild cache and results - Use pre/post translation dictionary to rewrite cache+result json - Skip translation",
        "ko": "캐시와 결과 다시 만들기 - 번역 전/후 사전으로 캐시와 결과 json을 다시 씀 - 번역은 건너뜀",
    },
    "dump-name": {
        "zh-cn": "导出name字段，生成name替换表，用于翻译name字段",
        "en": "Export name field to generate name replacement table for name field translation",
        "ko": "name 필드를 내보내 name 필드 번역용 이름 치환표를 만듭니다",
    },
    "show-plugs": {
        "zh-cn": "显示全部插件列表",
        "en": "Show all plugin list",
        "ko": "모든 플러그인 목록 보기",
    },
}
TRANSLATOR_DEFAULT_ENGINE = {
    "auto-translate": "gpt-5",
    "ForGal-tool": "gpt-5",
    "ForGal-markdown": "deepseek-chat",
    "ForNovel-tool": "gpt-5",
    "ForNovel": "deepseek-chat",
    "ForGal-json": "gpt-4.1",
    "sakura-v1.0": "sakura-7b-qwen2.5-v1.0",
    "galtransl-v3": "Sakura-GalTransl-7B-v3",
    "GenDic": "deepseek-chat",
}
NEED_OpenAITokenPool=["auto-translate", "ForGal-json", "ForGal-tool", "ForGal-markdown", "ForNovel", "ForNovel-tool", "GenDic"]
LANG_SUPPORTED = {
    "zh-cn": "Simplified_Chinese",
    "zh-tw": "Traditional_Chinese",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian",
    "fr": "French",
}
LANG_SUPPORTED_W = {
    "zh-cn": "简体中文",
    "zh-tw": "繁體中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
    "ru": "русский",
    "fr": "Français",
}
DEBUG_LEVEL = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}

new_version = []
update_thread = threading.Thread(target=check_for_tool_updates, args=(new_version,))
update_thread.start()

