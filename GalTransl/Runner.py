import os, time, sys, datetime, threading
from os.path import exists as isPathExists
from os import makedirs as mkdir
import logging, colorlog
from GalTransl import LOGGER, TRANSLATOR_SUPPORTED, new_version, GALTRANSL_VERSION,NEED_OpenAITokenPool
from GalTransl.GTPlugin import GTextPlugin, GFilePlugin, GProblemPlugin
from GalTransl.Problem import load_problem_plugins, finalize_problem_plugins
from GalTransl.COpenAI import COpenAITokenPool, init_sakura_endpoint_queue
from GalTransl.yapsy.PluginManager import PluginManager
from GalTransl.ConfigHelper import CProjectConfig, CProxyPool
from GalTransl.Frontend.LLMTranslate import doLLMTranslate
from GalTransl.i18n import get_text,GT_LANG
from GalTransl.RuntimePaths import get_plugins_dir
from GalTransl.FilePluginDetect import is_auto as is_auto_file_plugin, detect_file_plugins
from GalTransl.Utils import get_file_list
from GalTransl.CSplitter import (
    DictionaryCountSplitter,
    EqualPartsSplitter,
    DictionaryCombiner,
)


class _JobThreadFilter(logging.Filter):
    """Only accept log records emitted from this job's own thread.

    Without this filter, every handler added by concurrent jobs would fire for
    every log record, causing N× duplication when N jobs run in parallel.
    """

    def __init__(self):
        super().__init__()
        self._thread_ident = threading.current_thread().ident

    def filter(self, record: logging.LogRecord) -> bool:
        return record.thread == self._thread_ident


class _ExceptionOnlyConsoleFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return bool(record.exc_info)


class _ServerStatusFilter(logging.Filter):
    """For server-started jobs: only let through key status messages.

    Allows WARNING+ and INFO messages that look like translation milestones
    (file start, file complete, project summary, etc.).
    Blocks per-line translation output and other noisy INFO messages.
    """
    # Prefixes of INFO messages that are useful for observing backend state
    _ALLOWED_INFO_PREFIXES = (
        ">>> 开始翻译",
        "+++ 结果保存",
        "总耗时",
        "翻译开始时间",
        "开始时间已到",
        "当前使用",
        # Korean messages of this fork
        ">>> 번역 시작",
        "+++ 결과 저장",
        "총 소요 시간",
        "번역 시작 시각",
        "시작 시각 도달",
        "현재 Sakura worker",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.WARNING:
            return True
        if record.levelno < logging.INFO:
            return False
        msg = record.getMessage()
        return any(msg.startswith(p) for p in self._ALLOWED_INFO_PREFIXES)


def _raise_if_stop_requested(stop_event):
    if stop_event is not None and stop_event.is_set():
        from GalTransl.Service import JobCancelledError

        raise JobCancelledError()


CONSOLE_FORMAT = colorlog.ColoredFormatter(
    "[%(asctime)s]%(log_color)s[%(levelname)s]%(reset)s%(message)s",
    datefmt="%m-%d %H:%M:%S",
    log_colors={
        "DEBUG": "white",
        "INFO": "white",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)
File_FORMAT = logging.Formatter(
    "[%(asctime)s][%(levelname)s] %(message)s", datefmt="%m-%d %H:%M:%S"
)


def chinese_only_model_warning(translator: str, language) -> str | None:
    """Sakura/GalTransl 모델은 중국어로만 출력한다. 한국어 대상이면 경고 문구를 돌려준다."""
    target = str(language or "").split("2")[-1].strip().lower()
    if target in ("ko", "korean") and ("sakura" in translator or "galtransl" in translator):
        return (
            f"번역기 {translator}는 중국어 전용 모델이라 한국어 대상(language: {language})에서도 "
            "중국어로 번역합니다. 한국어 번역은 ForGal-json 등 OpenAI 호환(Ollama) 번역기를 쓰세요."
        )
    return None


async def run_galtransl(cfg: CProjectConfig, translator: str, stop_event=None):
    PROJECT_DIR = cfg.getProjectDir()
    cfg.select_translator = translator
    cfg.stop_event = stop_event

    def get_pluginInfo_path(name):
        if "(project_dir)" in name:
            name = name.replace("(project_dir)", "")
            return os.path.join(PROJECT_DIR, "plugins", name, f"{name}.yaml")
        else:
            return str(get_plugins_dir() / name / f"{name}.yaml")

    def print_plugin_list(plugin_manager: PluginManager):
        LOGGER.info("플러그인 목록:")
        for candidate in plugin_manager.getPluginCandidates():
            plug_path = os.path.dirname(candidate[1])
            plug_name = os.path.basename(plug_path)
            if "text_example_nouse" in plug_name:
                continue
            plug_info = candidate[2]
            plug_type = plug_info.yaml_dict["Core"].get("Type", "unknown").lower()
            if PROJECT_DIR in plug_path:
                plug_type = "Project-local " + plug_type
            if "Settings" in plug_info.yaml_dict:
                plug_settings = plug_info.yaml_dict["Settings"]
            else:
                plug_settings = {}

            LOGGER.info(f"  > {plug_name} ({plug_type} Plugin)")
            LOGGER.info(
                f"    이름: {plug_info.name} v{plug_info.version} by {plug_info.author}"
            )
            LOGGER.info(f"    설명: {plug_info.description}")
            LOGGER.info(f"    경로: {plug_path}")
            if plug_settings:
                LOGGER.info(f"    설정: ")
                for key, value in plug_settings.items():
                    LOGGER.info(f"     - {key}: {value}")
            LOGGER.info("---------------------------------")
        LOGGER.info("* 플러그인 설정을 바꾸려면 플러그인 경로의 .yaml 파일을 편집하세요.")

    start_time = time.time()
    _raise_if_stop_requested(stop_event)

    if translator not in TRANSLATOR_SUPPORTED.keys():
        raise Exception(f"지원하지 않는 번역기: {translator}")
    if warning := chinese_only_model_warning(translator, cfg.getKey("language")):
        LOGGER.warning(warning)

    # 日志初始化 — 添加当前 job 的 handler（不再全局 clear，避免并发 job 互相干扰）
    _job_handlers: list[logging.Handler] = []
    _thread_filter = _JobThreadFilter()  # 只处理本线程日志，防止并发 job 日志重复
    is_server = getattr(cfg, "non_interactive", False)
    if is_server:
        # Server job: 轻量控制台输出（仅关键状态），不使用 alive_bar
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(CONSOLE_FORMAT)
        handler.addFilter(_thread_filter)
        handler.addFilter(_ServerStatusFilter())
    else:
        # CLI job: 完整终端输出 + alive_bar
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(CONSOLE_FORMAT)
        handler.addFilter(_thread_filter)
        if not getattr(cfg, "print_translation_log_in_terminal", True):
            handler.addFilter(_ExceptionOnlyConsoleFilter())
    LOGGER.addHandler(handler)
    _job_handlers.append(handler)
    if cfg.getCommonConfigSection().get("saveLog", False):
        log_path = os.path.join(PROJECT_DIR, "GalTransl.log")
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(File_FORMAT)
        file_handler.addFilter(_thread_filter)
        LOGGER.addHandler(file_handler)
        _job_handlers.append(file_handler)

    try:
        start_time_text = cfg.getCommonConfigSection().get("start_time", "")
        if start_time_text:
            LOGGER.info(f"번역 시작 시각: {start_time_text}")
            start_transl_time = datetime.datetime.strptime(start_time_text, "%H:%M")
            while True:
                _raise_if_stop_requested(stop_event)
                now = datetime.datetime.now()
                if (
                    now.hour == start_transl_time.hour
                    and now.minute == start_transl_time.minute
                ):
                    LOGGER.info("시작 시각 도달, 번역을 시작합니다...")
                    break
                time.sleep(1)

        # 目录初始化
        for dir_path in [
            cfg.getInputPath(),
            cfg.getOutputPath(),
            cfg.getCachePath(),
        ]:
            _raise_if_stop_requested(stop_event)
            if not isPathExists(dir_path):
                LOGGER.info("%s 폴더가 없어 새로 만듭니다...", dir_path)
                mkdir(dir_path)
        # 插件初始化
        plugin_manager = PluginManager(
            {"GTextPlugin": GTextPlugin, "GFilePlugin": GFilePlugin, "GProblemPlugin": GProblemPlugin},
            [str(get_plugins_dir()), os.path.join(PROJECT_DIR, "plugins")],
        )
        plugin_manager.locatePlugins()
        # 打印插件列表
        if translator == "show-plugs":
            print_plugin_list(plugin_manager)
            return None
        new_candidates = []
        for tname in cfg.getTextPluginList():
            info_path = get_pluginInfo_path(tname)
            candidate = plugin_manager.getPluginCandidateByInfoPath(info_path)
            if candidate:
                new_candidates.append(candidate)
            else:
                LOGGER.warning(f"텍스트 플러그인을 찾지 못함: {tname}, 건너뜀")
        fname = cfg.getFilePlugin()
        if is_auto_file_plugin(fname):
            # 自动识别：按输入目录里实际出现的文件类型加载所需的全部文件插件
            detected = detect_file_plugins(get_file_list(cfg.getInputPath()), cfg.getProjectDir())
            fnames = sorted({n for n in detected.values() if n})
            unknown = [os.path.basename(p) for p, n in detected.items() if not n]
            if unknown:
                LOGGER.warning(f"파일 플러그인 자동 인식: 다음 파일은 형식을 알 수 없어 건너뜀: {unknown[:20]}")
            LOGGER.info(f"파일 플러그인 자동 인식: {fnames or '없음'}")
        else:
            fnames = [fname] if fname else []
        for fname in fnames:
            info_path = get_pluginInfo_path(fname)
            candidate = plugin_manager.getPluginCandidateByInfoPath(info_path)
            assert candidate, f"파일 플러그인을 찾지 못함: {fname}, 설정을 확인하세요"
            new_candidates.append(candidate)

        plugin_manager.setPluginCandidates(new_candidates)
        plugin_manager.loadPlugins()
        text_plugins = plugin_manager.getPluginsOfCategory("GTextPlugin")
        file_plugins = plugin_manager.getPluginsOfCategory("GFilePlugin")
        for plugin in file_plugins + text_plugins:
            _raise_if_stop_requested(stop_event)
            plugin_conf = plugin.yaml_dict
            plugin_module = plugin_conf["Core"]["Module"]
            project_conf = cfg.getCommonConfigSection()
            project_plugin_conf = cfg.getPluginConfigSection()
            if plugin_module in project_plugin_conf:
                plugin_conf["Settings"].update(project_plugin_conf[plugin_module])
            project_conf["project_dir"] = cfg.getProjectDir()
            try:
                LOGGER.info(get_text("loading_plugin", GT_LANG, plugin.name))
                plugin.plugin_object.gtp_init(plugin_conf, project_conf)
            except Exception as e:
                LOGGER.error(get_text("plugin_load_failed", GT_LANG, plugin.name, e))
                if plugin in text_plugins:
                    text_plugins.remove(plugin)
                elif plugin in file_plugins:
                    file_plugins.remove(plugin)

        # proxyPool初始化
        proxyPool = CProxyPool(cfg) if cfg.getKey("internals.enableProxy") else None
        if proxyPool and translator not in [
            "rebuildr",
            "rebuilda",
            "dump-name",
            "show-plugs",
        ]:
            _raise_if_stop_requested(stop_event)
            await proxyPool.checkAvailablity()
            if not proxyPool.proxies:
                raise Exception("사용할 수 있는 프록시가 없습니다. 프록시 설정을 확인하세요")
        if not proxyPool:
            #LOGGER.warning("不使用代理")
            pass

        # OpenAITokenPool初始化
        if any(x in translator for x in NEED_OpenAITokenPool):
            OpenAITokenPool = COpenAITokenPool(cfg, translator)
        else:
            OpenAITokenPool = None

        # 初始化sakura端点队列
        if "sakura" in translator or "galtransl" in translator:
            _raise_if_stop_requested(stop_event)
            sakura_endpoint_queue = await init_sakura_endpoint_queue(cfg)
            cfg.endpointQueue = sakura_endpoint_queue

        # 检查更新
        if new_version and new_version[0] != GALTRANSL_VERSION:
            LOGGER.info(
                f"\033[32m새 버전 발견: {new_version[0]}\033[0m  현재 버전: {GALTRANSL_VERSION}"
            )
            LOGGER.info(
                f"\033[32m업데이트 주소: https://github.com/xd2333/GalTransl/releases\033[0m"
            )

        if project_conf.get("splitFile", "no") in ["Num","Equal"]:
            val = project_conf.get("splitFile", "no")
            splitFileNum = int(project_conf.get("splitFileNum", -1))
            cross_num = int(project_conf.get("splitFileCrossNum", 0))
            if "dump-name" in translator:  # 提取人名表时不交叉
                cross_num = 0
            if splitFileNum == -1:
                splitFileNum = int(project_conf.get("workersPerProject", -1))

            if val == "Num":
                assert splitFileNum > 10, "DictionaryCountSplitter의 분할 수는 10보다 커야 합니다"
                input_splitter = DictionaryCountSplitter(splitFileNum, cross_num)
            elif val == "Equal":
                input_splitter = EqualPartsSplitter(splitFileNum, cross_num)
            else:
                raise Exception(f"지원하지 않는 분할 방식: {val}")
            # 默认的输出合并器
            output_combiner = DictionaryCombiner()
        else:
            input_splitter = EqualPartsSplitter(1)
            output_combiner = DictionaryCombiner()

        cfg.tPlugins = text_plugins
        cfg.fPlugins = file_plugins
        load_problem_plugins(cfg)
        cfg.fPluginAuto = is_auto_file_plugin(cfg.getFilePlugin())
        cfg.tokenPool = OpenAITokenPool
        cfg.proxyPool = proxyPool
        cfg.input_splitter = input_splitter

        _raise_if_stop_requested(stop_event)
        await doLLMTranslate(cfg)

        for plugin in file_plugins + text_plugins:
            _raise_if_stop_requested(stop_event)
            plugin.plugin_object.gtp_final()

        end_time = time.time()
        LOGGER.info(f"총 소요 시간: {end_time-start_time:.3f}s")
    finally:
        finalize_problem_plugins(cfg)
        # 移除当前 job 添加的 handler，不影响其他并发 job
        for h in _job_handlers:
            LOGGER.removeHandler(h)
