import os
# Language support for GalTransl
# This file contains all the text strings used in the UI and backend

# Available languages
AVAILABLE_LANGUAGES = ["ko", "zh-cn", "en"]

# Default language (this fork defaults to Korean; set GT_LANG=zh-cn or en to switch)
DEFAULT_LANGUAGE = "ko"

GT_LANG=os.environ.get("GT_LANG", DEFAULT_LANGUAGE)

# UI text strings
UI_TEXT = {
    # Common
    "language_name": {
        "zh-cn": "简体中文",
        "en": "English",
        "ko": "한국어"
    },
    
    # Input prompts
    "input_project_path": {
        "zh-cn": "请输入/拖入项目文件夹，或项目文件夹内的yaml配置文件[default]：",
        "en": "Please input/drag project folder, or yaml config file in project folder[default]: ",
        "ko": "프로젝트 폴더 또는 프로젝트 폴더 안의 yaml 설정 파일 경로를 입력하거나 끌어 놓으세요[기본값]: "
    },
    "input_path_empty": {
        "zh-cn": "输入路径不能为空且必须是字符串类型\n",
        "en": "Input path cannot be empty and must be a string\n",
        "ko": "입력 경로는 비어 있을 수 없으며 문자열이어야 합니다\n"
    },
    "project_folder_not_exist": {
        "zh-cn": "项目文件夹 {0} 不存在，请检查后重新输入\n",
        "en": "Project folder {0} does not exist, please check and input again\n",
        "ko": "프로젝트 폴더 {0}이(가) 없습니다. 확인 후 다시 입력하세요\n"
    },
    "config_file_not_exist": {
        "zh-cn": "配置文件 {0} 不存在，请检查后重新输入\n",
        "en": "Config file {0} does not exist, please check and input again\n",
        "ko": "설정 파일 {0}이(가) 없습니다. 확인 후 다시 입력하세요\n"
    },
    "config_file_not_valid": {
        "zh-cn": "配置文件路径 {0} 不是一个有效的文件，请检查后重新输入\n",
        "en": "Config file path {0} is not a valid file, please check and input again\n",
        "ko": "설정 파일 경로 {0}은(는) 올바른 파일이 아닙니다. 확인 후 다시 입력하세요\n"
    },
    "continue_with_project": {
        "zh-cn": "(留空继续『{0}』项目)",
        "en": "(leave empty to continue with \"{0}\" project)",
        "ko": "(비워 두면 \"{0}\" 프로젝트로 계속)"
    },
    "select_translator": {
        "zh-cn": "请为『{0}』项目选择翻译模板：",
        "en": "Please select translation template for \"{0}\" project:",
        "ko": "\"{0}\" 프로젝트의 번역 템플릿을 선택하세요:"
    },
    
    # Error messages
    "error_validating_path": {
        "zh-cn": "验证项目路径时发生错误: {0}\n",
        "en": "Error validating project path: {0}\n",
        "ko": "프로젝트 경로 확인 중 오류: {0}\n"
    },
    "error_creating_shortcut": {
        "zh-cn": "创建快捷方式时发生错误: {0}\n",
        "en": "Error creating shortcut: {0}\n",
        "ko": "바로 가기 생성 중 오류: {0}\n"
    },
    "error_project_path_empty": {
        "zh-cn": "项目路径不能为空且必须是字符串类型",
        "en": "Project path cannot be empty and must be a string",
        "ko": "프로젝트 경로는 비어 있을 수 없으며 문자열이어야 합니다"
    },
    "error_config_file_empty": {
        "zh-cn": "配置文件名不能为空且必须是字符串类型",
        "en": "Config file name cannot be empty and must be a string",
        "ko": "설정 파일 이름은 비어 있을 수 없으며 문자열이어야 합니다"
    },
    "error_translator_empty": {
        "zh-cn": "翻译器名称不能为空且必须是字符串类型",
        "en": "Translator name cannot be empty and must be a string",
        "ko": "번역기 이름은 비어 있을 수 없으며 문자열이어야 합니다"
    },
    "error_loading_config": {
        "zh-cn": "加载配置文件失败: {0}",
        "en": "Failed to load config file: {0}",
        "ko": "설정 파일을 불러오지 못했습니다: {0}"
    },
    "error_creating_event_loop": {
        "zh-cn": "创建新的事件循环...",
        "en": "Creating new event loop...",
        "ko": "새 이벤트 루프를 만드는 중..."
    },
    "error_unexpected": {
        "zh-cn": "程序遇到未预期的错误: {0}",
        "en": "Program encountered an unexpected error: {0}",
        "ko": "프로그램에서 예기치 않은 오류가 발생했습니다: {0}"
    },
    "error_closing_event_loop": {
        "zh-cn": "关闭事件循环时发生错误: {0}",
        "en": "Error closing event loop: {0}",
        "ko": "이벤트 루프를 닫는 중 오류: {0}"
    },
    
    # Status messages
    "translation_completed": {
        "zh-cn": "任务完成，准备重新开始...",
        "en": "task completed, preparing to restart...",
        "ko": "작업을 마쳤습니다. 다시 시작할 준비 중..."
    },
    "waiting_for_requests": {
        "zh-cn": "正在等待现有请求返回...",
        "en": "Waiting for existing requests to return...",
        "ko": "진행 중인 요청이 돌아오기를 기다리는 중..."
    },
    "goodbye": {
        "zh-cn": "Goodbye.",
        "en": "Goodbye.",
        "ko": "종료합니다."
    },
    "program_error": {
        "zh-cn": "程序遇到问题，即将退出（诊断信息：{0}）",
        "en": "Program encountered a problem and will exit (diagnostic info: {0})",
        "ko": "프로그램에 문제가 생겨 종료합니다 (진단 정보: {0})"
    },
    "invalid_source_language": {
        "zh-cn": "错误的源语言代码：{0}",
        "en": "Invalid source language code: {0}",
        "ko": "잘못된 원문 언어 코드: {0}"
    },
    "invalid_target_language": {
        "zh-cn": "错误的目标语言代码：{0}",
        "en": "Invalid target language code: {0}",
        "ko": "잘못된 대상 언어 코드: {0}"
    },
    "request_error_quota": {
        "zh-cn": "[请求错误]余额不足：{0}",
        "en": "[Request Error] Insufficient quota: {0}",
        "ko": "[요청 오류] 사용량 부족: {0}"
    },
    "request_error_switch_token": {
        "zh-cn": "[请求错误]切换到token {0}",
        "en": "[Request Error] Switching to token {0}",
        "ko": "[요청 오류] 토큰 {0}(으)로 전환"
    },
    "request_error_too_many": {
        "zh-cn": "[请求错误]请求受限，{0}秒后继续尝试",
        "en": "[Request Error] Request limited, trying again in {0} seconds",
        "ko": "[요청 오류] 요청 제한, {0}초 뒤 다시 시도"
    },
    "request_error_reset": {
        "zh-cn": "[请求错误]报错重置会话",
        "en": "[Request Error] Error resetting session",
        "ko": "[요청 오류] 세션 초기화 중 오류"
    },
    "request_error_retry": {
        "zh-cn": "[请求错误]报错:{0}, 2秒后重试",
        "en": "[Request Error] Error: {0}, retrying in 2 seconds",
        "ko": "[요청 오류] 오류: {0}, 2초 뒤 다시 시도"
    },
    "parse_error": {
        "zh-cn": "[解析错误]解析结果出错：{0}",
        "en": "[Parse Error] Error parsing result: {0}",
        "ko": "[해석 오류] 결과 해석 중 오류: {0}"
    },
    "parse_error_skip": {
        "zh-cn": "[解析错误]解析出错但跳过本轮翻译",
        "en": "[Parse Error] Error parsing but skipping this translation round",
        "ko": "[해석 오류] 해석 오류가 있지만 이번 번역 회차는 건너뜁니다"
    },
    "repeated_error": {
        "zh-cn": "单句反复出错，已中止。错误为：{0}",
        "en": "Repeated errors on a single sentence, aborted. Error: {0}",
        "ko": "한 문장에서 오류가 반복되어 중단했습니다. 오류: {0}"
    },
    "translation_input": {
        "zh-cn": "->翻译输入：{0}\n{1}\n",
        "en": "->Translation input: {0}\n{1}\n",
        "ko": "->번역 입력: {0}\n{1}\n"
    },
    "proofread_input": {
        "zh-cn": "->校对输入：{0}\n{1}\n",
        "en": "->Proofreading input: {0}\n{1}\n",
        "ko": "->교정 입력: {0}\n{1}\n"
    },
    "output": {
        "zh-cn": "->输出：",
        "en": "->Output:",
        "ko": "->출력:"
    },
    "output_with_content": {
        "zh-cn": "->输出：\n{0}",
        "en": "->Output:\n{0}",
        "ko": "->출력:\n{0}"
    },
    "non_json_output": {
        "zh-cn": "-> 非json：\n{0}\n",
        "en": "-> Non-JSON:\n{0}\n",
        "ko": "-> JSON 아님:\n{0}\n"
    },
    "cache_read_error": {
        "zh-cn": "读取缓存{0}时出现错误，请检查错误信息",
        "en": "Error reading cache {0}, please check error message",
        "ko": "캐시 {0}을(를) 읽는 중 오류가 발생했습니다. 오류 메시지를 확인하세요"
    },
    "retry_failed": {
        "zh-cn": "重试失败的: {0}",
        "en": "Retrying failed: {0}",
        "ko": "실패 항목 다시 시도: {0}"
    },
    "loading_plugin": {
        "zh-cn": "加载插件\"{0}\"...",
        "en": "Loading plugin \"{0}\"...",
        "ko": "플러그인 \"{0}\" 불러오는 중..."
    },
    "plugin_load_failed": {
        "zh-cn": "插件\"{0}\"加载失败: {1}",
        "en": "Plugin \"{0}\" loading failed: {1}",
        "ko": "플러그인 \"{0}\"을(를) 불러오지 못했습니다: {1}"
    },
    "file_processing_error": {
        "zh-cn": "处理文件 {0} 时发生错误: {1}",
        "en": "Error processing file {0}: {1}",
        "ko": "파일 {0} 처리 중 오류: {1}"
    },
    "task_execution_failed": {
        "zh-cn": "任务执行失败: {0}",
        "en": "Task execution failed: {0}",
        "ko": "작업 실행 실패: {0}"
    },
    "plugin_execution_failed": {
        "zh-cn": "插件 {0} 执行失败: {1}",
        "en": "Plugin {0} execution failed: {1}",
        "ko": "플러그인 {0} 실행 실패: {1}"
    },
    "file_translation_completed": {
        "zh-cn": "文件 {0}{1} 翻译完成，用时 {2:.3f}s",
        "en": "File {0}{1} translation completed, time used {2:.3f}s",
        "ko": "파일 {0}{1} 번역 완료, 소요 시간 {2:.3f}초"
    },
    "file_chunks_completed": {
        "zh-cn": "文件 {0} 的所有chunk都翻译完成",
        "en": "All chunks of file {0} have been translated",
        "ko": "파일 {0}의 모든 조각을 번역했습니다"
    },
    "file_load_failed": {
        "zh-cn": "文件 {0} 无法加载",
        "en": "File {0} cannot be loaded",
        "ko": "파일 {0}을(를) 불러올 수 없습니다"
    },
    "cache_incomplete": {
        "zh-cn": "{0} 缓存不完整，无法重构",
        "en": "{0} cache incomplete, cannot rebuild",
        "ko": "{0} 캐시가 불완전해 다시 만들 수 없습니다"
    },
    # 重建失败时把"哪几句、为什么"说清楚（见 Backend/RebuildTranslate）
    "cache_incomplete_detail": {
        "zh-cn": "共 {0} 句，{1} 句没命中缓存（重建不翻译，只能用现有缓存重刷译文与结果）：",
        "en": "{0} sentences in total, {1} not found in cache (rebuild does not translate; it can only re-apply dictionaries using the existing cache):",
        "ko": "총 {0}문장 중 {1}문장이 캐시에 없습니다(rebuild는 번역하지 않고 기존 캐시에 사전만 다시 적용합니다):"
    },
    "cache_incomplete_reason_line": {
        "zh-cn": "- {0} 句：{1}",
        "en": "- {0} sentence(s): {1}",
        "ko": "- {0}문장: {1}"
    },
    "cache_incomplete_examples": {
        "zh-cn": "例：{0}",
        "en": "e.g. {0}",
        "ko": "예: {0}"
    },
    "cache_incomplete_miss_key_not_found": {
        "zh-cn": "缓存里没有这一条（说话人 + 原文 + 上下句拼出的键对不上：原文被改过，或缓存是按分块写的）",
        "en": "not present in cache (the speaker+source+neighbour key does not match: source edited, or cache written per chunk)",
        "ko": "캐시에 없음(화자+원문+앞뒤 문장 키가 일치하지 않음: 원문이 수정되었거나 캐시가 조각별로 기록됨)"
    },
    "cache_incomplete_miss_post_src_changed": {
        "zh-cn": "原文经译前字典替换后与缓存里记录的不一致（译前字典改过 → 这条缓存已过期）",
        "en": "source after pre-dictionary differs from the cached one (pre-dictionary changed → stale cache)",
        "ko": "번역 전 사전 적용 후 원문이 캐시와 다름(번역 전 사전 변경 → 오래된 캐시)"
    },
    "cache_incomplete_miss_pre_dst_empty": {
        "zh-cn": "缓存里这条的译文是空的（上次没翻成功，或没写进缓存）",
        "en": "cached translation is empty (last run failed or never wrote it)",
        "ko": "캐시의 번역문이 비어 있음(지난 실행이 실패했거나 기록되지 않음)"
    },
    "cache_incomplete_miss_translate_failed": {
        "zh-cn": "缓存里这条是翻译失败（(Failed)），且配置开着「重试失败句」",
        "en": "cached entry is a failed translation and retranslFail is enabled",
        "ko": "캐시 항목이 번역 실패이고 retranslFail이 켜져 있음"
    },
    "cache_incomplete_miss_retran_key": {
        "zh-cn": "原文命中重译关键字（配置 retranslKey）",
        "en": "source matches retranslKey",
        "ko": "원문이 retranslKey와 일치"
    },
    "cache_incomplete_miss_retran_problem": {
        "zh-cn": "问题描述命中重译关键字（配置 retranslKey）",
        "en": "problem text matches retranslKey",
        "ko": "문제 텍스트가 retranslKey와 일치"
    },
    "cache_incomplete_miss_proofread_missing": {
        "zh-cn": "还没有校对稿（本次按校对模式查缓存）",
        "en": "no proofread result yet (cache queried in proofread mode)",
        "ko": "아직 교정 결과가 없음(교정 모드로 캐시 조회)"
    },
    "cache_incomplete_miss_unknown": {
        "zh-cn": "未命中缓存（原因码：{0}）",
        "en": "not found in cache (reason code: {0})",
        "ko": "캐시에서 찾지 못함(사유 코드: {0})"
    },
    "cache_incomplete_hint": {
        "zh-cn": "处理：给这些句子补上译文（patch_transl_cache）后重跑重建；或删掉它们重翻（delete_transl_cache → start_translation）。",
        "en": "How to fix: write translations for these entries (patch_transl_cache) and rebuild again, or delete them and retranslate (delete_transl_cache → start_translation).",
        "ko": "해결 방법: 이 항목의 번역을 써 넣고(patch_transl_cache) 다시 rebuild하거나, 삭제하고 다시 번역하세요(delete_transl_cache → start_translation)."
    }
}

# Function to get text in the current language
def get_text(key, lang=GT_LANG, *args):
    """
    Get text in the specified language
    
    Args:
        key: The key for the text
        lang: The language code (default: DEFAULT_LANGUAGE)
        *args: Arguments to format into the text
        
    Returns:
        The text in the specified language, or the key if not found
    """
    if lang not in AVAILABLE_LANGUAGES:
        lang = DEFAULT_LANGUAGE  # Default to default language if language not supported
    
    if key not in UI_TEXT:
        return key
    
    if lang not in UI_TEXT[key]:
        # Fallback to default language if the key exists but not in the requested language
        lang = next(code for code in (DEFAULT_LANGUAGE, "en", "zh-cn") if code in UI_TEXT[key])
    
    text = UI_TEXT[key][lang]
    
    if args:
        try:
            return text.format(*args)
        except:
            return text
    
    return text