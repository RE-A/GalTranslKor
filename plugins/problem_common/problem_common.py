"""
分析问题
"""

from enum import Enum
from collections import Counter
from string import ascii_letters, digits, punctuation
from typing import List, Tuple
import re
import math

from GalTransl.CSentense import CSentense
from GalTransl.ConfigHelper import CProjectConfig
from GalTransl.GTPlugin import GProblemPlugin
from GalTransl.Dictionary import CGptDict


_DECIMAL_LITERAL_RE = re.compile(r"^[+-]?(\d+(\.\d+)?|\.\d+)([eE][+-]?\d+)?$")


def normalize_sentence_length_threshold(raw) -> int:
    if isinstance(raw, bool):
        return 17
    if isinstance(raw, str) and not _DECIMAL_LITERAL_RE.match(raw.strip()):
        return 17
    try:
        number = float(raw)
    except (TypeError, ValueError, OverflowError):
        return 17
    if not math.isfinite(number) or not number.is_integer() or number <= 0:
        return 17
    return int(number)


def extract_control_substrings(text: str) -> list[str]:
    """
    提取文本中所有以英文标点符号开头，且仅包含英文字母、数字和标点符号的子串。

    Args:
        text: 输入的文本字符串。

    Returns:
        一个包含所有匹配子串的列表。
    """
    # 定义允许的字符集：英文字母、数字和标点符号
    # string.punctuation 包含 !"#$%&'()*+,-./:;<=>?@[]^_`{|}~
    # string.ascii_letters 包含 a-z 和 A-Z
    # string.digits 包含 0-9
    allowed_chars = ascii_letters + digits + punctuation
    first_punctuation = r"""!#$%&()*+-./:;<=>?@[\]^_`{|}~"""
    # 构建正则表达式：
    # 1. [{re.escape(string.punctuation)}] - 匹配一个英文标点符号作为开头
    # 2. [{re.escape(allowed_chars)}]* - 匹配零个或多个由允许字符组成的后续部分
    # re.escape() 用于转义字符集中的特殊正则字符（如 `[` `]` `^` `-`）
    pattern = f"[{re.escape(first_punctuation)}][{re.escape(allowed_chars)}]*"
    
    # 使用 re.findall 查找所有匹配的子串
    return re.findall(pattern, text)


def get_most_common_char(input_text: str) -> Tuple[str, int]:
    """
    此函数接受一个字符串作为输入，并返回该字符串中最常见的字符及其出现次数。
    它会忽略黑名单中的字符，包括 "." 和 "，"。

    参数:
    - input_text: 一段文本字符串。

    返回值:
    - 包含最常见字符及其出现次数的元组。
    """
    black_list: List[str] = [".", "，"]
    counter: Counter = Counter(input_text)
    most_common = counter.most_common()
    most_char: str = ""
    most_char_count: int = 0
    for char in most_common:
        if char[0] not in black_list:
            most_char = char[0]
            most_char_count = char[1]
            break
    return most_char, most_char_count


def contains_japanese(text: str) -> str:
    """
    此函数接受一个字符串作为输入，检查其中是否包含日文字符。

    参数:
    - text: 要检查的字符串。

    返回值:
    - 如果字符串中包含日文字符，则返回 True，否则返回 False。
    """
    # 日文字符范围
    hiragana_range = (0x3040, 0x309F)
    katakana_range = (0x30A0, 0x30FF)
    katakana_range2 = (0xFF66, 0xFF9F)

    jp_chars = set()
    # 检查字符串中的每个字符
    for char in text:
        # 黑名单
        if char in ["ー", "・"]:
            continue
        # 获取字符的 Unicode 码点
        code_point = ord(char)
        # 检查字符是否在日文字符范围内
        if (
            hiragana_range[0] <= code_point <= hiragana_range[1]
            or katakana_range[0] <= code_point <= katakana_range[1]
            or katakana_range2[0] <= code_point <= katakana_range2[1]
        ):
            jp_chars.add(char)
    return "".join(jp_chars)


def contains_korean(text: str) -> bool:
    """
    此函数接受一个字符串作为输入，检查其中是否包含韩文字符。

    参数:
    - text: 要检查的字符串。

    返回值:
    - 如果字符串中包含韩文字符，则返回 True，否则返回 False。
    """
    # 韩文字符范围
    hangul_jamo_range = (0x1100, 0x11FF)  # 韩文声母和韵母
    hangul_compatibility_jamo_range = (0x3130, 0x318F)  # 韩文兼容声母和韵母
    hangul_syllables_range = (0xAC00, 0xD7AF)  # 韩文音节

    # 检查字符串中的每个字符
    for char in text:
        # 获取字符的 Unicode 码点
        code_point = ord(char)
        # 检查字符是否在韩文字符范围内
        if (
            hangul_jamo_range[0] <= code_point <= hangul_jamo_range[1]
            or hangul_compatibility_jamo_range[0]
            <= code_point
            <= hangul_compatibility_jamo_range[1]
            or hangul_syllables_range[0] <= code_point <= hangul_syllables_range[1]
        ):
            return True
    return False


def is_all_gbk(s):
    if s == "":
        return ""
    
    non_gbk_chars = set()
    for char in s:
        try:
            char.encode('gbk')
        except UnicodeEncodeError:
            non_gbk_chars.add(char)
    
    return str("".join(non_gbk_chars))


def contains_english(text: str) -> str:
    """
    此函数接受一个字符串作为输入，检查其中是否包含英文字符。

    参数:
    - text: 要检查的字符串。

    返回值:
    - 如果字符串中包含英文字符，则返回 True，否则返回 False。
    """
    # 英文字符范围
    english_range = (0x0041, 0x005A)
    english_range2 = (0x0061, 0x007A)
    english_range3 = (0xFF21, 0xFF3A)
    english_range4 = (0xFF41, 0xFF5A)

    eng_chars = ""
    # 检查字符串中的每个字符
    for char in text:
        # 获取字符的 Unicode 码点
        code_point = ord(char)
        # 检查字符是否在英文字符范围内
        if (
            english_range[0] <= code_point <= english_range[1]
            or english_range2[0] <= code_point <= english_range2[1]
            or english_range3[0] <= code_point <= english_range3[1]
            or english_range4[0] <= code_point <= english_range4[1]
        ):
            eng_chars += char
    return eng_chars


class CProblemType(Enum):
    """Common checks and their display metadata, owned by this plugin."""

    def __new__(cls, value, description, default_enabled):
        member = object.__new__(cls)
        member._value_ = value
        member.description = description
        member.default_enabled = default_enabled
        return member

    词频过高 = 1, "번역문에서 한 글자가 20번 넘게 반복됨(원문보다 훨씬 많음).", True
    标点错漏 = 2, "괄호, 따옴표, 쌍점 등 문장부호가 원문과 다름.", True
    本无括号 = 标点错漏
    本无引号 = 标点错漏
    残留日文 = 3, "번역문에 일본어 히라가나·가타카나가 남음. 원문과 최종 번역문이 완전히 같으면 原文输出(원문 출력)으로 기록.", True
    丢失换行 = 4, "번역문에 원문의 문장 내 줄바꿈이 없음.", False
    多加换行 = 5, "번역문 줄바꿈이 원문보다 많아 화면을 넘칠 수 있음.", True
    比日文长 = 6, "번역문 길이가 원문의 1.3배를 넘음(한국어는 띄어쓰기를 빼고 1.5배 기준).", True
    字典使用 = 7, "GPT 사전대로 번역하지 않음.", True
    引入英文 = 8, "원문에 없는 영어 단어가 번역문에 들어감.", False
    比日文长严格 = 9, "번역문 길이가 원문보다 김(엄격한 기준).", False
    语言不通 = 10, "대상 언어가 중국어면 GBK 밖의 문자가 많을 때, 한국어면 중국어 출력이 의심될 때.", True
    缺控制符 = 11, "번역문에 원문의 제어 문자(\\n, 변수 표기 등)가 없음.", True
    独白男他 = 12, "독백(name 없음) 번역문에 '他'가 나옴(중국어 출력 전용).", True
    单句过长 = 13, "번역문 문장이 너무 김. 평균 구간 길이가 기준값(avgSentenceLengthThreshold)을 넘음.", False
    数字不符 = 14, "원문의 아라비아 숫자가 번역문에 없음(한국어 대상 전용, 제어 문자 안의 숫자는 제외).", True

# Variables and control codes keep their digits verbatim; they are checked by 缺控制符.
_CONTROL_CODE_RE = re.compile(r"%[-+ #0-9.]*[a-zA-Z]|\[[^\]]*\]|\{[^}]*\}|<[^>]*>|\\[a-zA-Z]+\d*")
_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")
_FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９．，", "0123456789.,")


def _numbers(text: str) -> Counter:
    text = _CONTROL_CODE_RE.sub(" ", text.translate(_FULLWIDTH_DIGITS))
    return Counter(n.replace(",", "") for n in _NUMBER_RE.findall(text))


MONOLOGUE_MALE_HE_EXCLUDES = (
    "其他",
    "他们",
    "他人",
    "他乡",
    "他国",
    "他日",
    "他山",
)

def _check_problems(
    tran: CSentense,
    projectConfig: CProjectConfig,
    gpt_dict: CGptDict = None,
    sentence_length_threshold: int = 17,
) -> list[str]:
    """Return the legacy check results for a sentence."""
    arinashi_dict = projectConfig.getProblemAnalyzeArinashiDict()
    find_type = projectConfig.getProblemAnalyzeConfig("problemList")
    # Other plugins may add names to the same project problem list.
    find_type = {
        CProblemType.__members__[name]
        for item in find_type
        if (name := getattr(item, "name", item)) in CProblemType.__members__
    }

    if getattr(tran, "skip_check", False):
        return []

    pre_src = tran.pre_src
    post_src = tran.post_src
    pre_dst = tran.pre_dst
    post_dst = tran.post_dst
    if pre_dst == "":
        return []
    n_symbol = ""
    if "\\r\\n" in pre_src:
        n_symbol = "\\r\\n"
    elif "\r\n" in pre_src:
        n_symbol = "\r\n"
    elif "\\n" in pre_src:
        n_symbol = "\\n"
    elif "\n" in pre_src:
        n_symbol = "\n"
    if projectConfig.getlbSymbol() != "auto" and projectConfig.getlbSymbol() != "":
        n_symbol = projectConfig.getlbSymbol()

    # Korean target: Hangul is expected, half-width punctuation is normal and
    # spacing makes Korean longer than Japanese, so those checks are adapted.
    korean = str(getattr(projectConfig, "target_lang", "")).lower() in ("ko", "korean")
    half_width = {"（": "(", "：": ":", "；": ";"} if korean else {}

    problem_list = []
    if CProblemType.词频过高 in find_type:
        most_word, word_count = get_most_common_char(pre_dst)
        most_word_src, word_count_src = get_most_common_char(pre_src)
        if word_count > 20 and word_count > word_count_src * 2:
            problem_list.append(f"词频过高：'{most_word}'{str(word_count)}次")
    if CProblemType.标点错漏 in find_type:
        char_to_error = {
            ("（", ")"): "括号",
            "：": "冒号",
            "*": "*符号",
            "；": "；符号",
            "[": "[符号",
            "<": "<符号",
            ("『", "「", "“"): "引号",
        }

        for chars, error in char_to_error.items():
            if korean:
                chars = tuple(chars) if isinstance(chars, tuple) else (chars,)
                chars = chars + tuple(half_width[c] for c in chars if c in half_width)
            if isinstance(chars, tuple):
                if not any(char in pre_src for char in chars):
                    if any(char in post_dst for char in chars):
                        problem_list.append(f"本无{error}")
                elif any(char in pre_src for char in chars):
                    if not any(char in post_dst for char in chars):
                        problem_list.append(f"本有{error}")
            else:
                if chars not in pre_src:
                    if chars in post_dst:
                        problem_list.append(f"本无{error}")
                elif chars in pre_src:
                    if chars not in post_dst:
                        problem_list.append(f"本有{error}")

        if not korean and contains_korean(pre_dst) and not contains_korean(pre_src):
            problem_list.append("本无韩文")
    if CProblemType.残留日文 in find_type:
        pre_dst_jp_chars = contains_japanese(pre_dst)
        post_dst_jp_chars = contains_japanese(post_dst)
        if pre_dst_jp_chars != "" and post_dst_jp_chars != "":
            if pre_src == post_dst:
                problem_list.append("原文输出")
            else:
                problem_list.append(f"残留日文：{post_dst_jp_chars}")
    if CProblemType.丢失换行 in find_type and n_symbol != "":
        if pre_src.count(n_symbol) > post_dst.count(n_symbol):
            problem_list.append("丢失换行")
    if CProblemType.单句过长 in find_type and n_symbol != "":
        n_number = post_dst.count(n_symbol)
        # 去除换行符本身的字符长度，只计算纯文本
        clean_len = len(post_dst) - n_number * len(n_symbol)
        avg_sentence_length = clean_len / (n_number + 1)
        if avg_sentence_length > sentence_length_threshold:
            problem_list.append("单句过长")
    if CProblemType.多加换行 in find_type and n_symbol != "":
        if pre_src.count(n_symbol) < post_dst.count(n_symbol):
            problem_list.append("多加换行")
    if CProblemType.比日文长 in find_type or CProblemType.比日文长严格 in find_type:
        len_beta = 1.3
        min_diff=8
        if CProblemType.比日文长严格 in find_type:
            len_beta = 1.0
            min_diff=0
        dst_len = len(post_dst)
        if korean:
            dst_len = len("".join(post_dst.split()))
            if CProblemType.比日文长 in find_type and CProblemType.比日文长严格 not in find_type:
                len_beta = 1.5
        if dst_len > len(pre_src) * len_beta and dst_len - len(pre_src) >= min_diff:
            problem_list.append(
                f"比日文长：{round(dst_len/max(len(pre_src),0.1),1)}倍({dst_len-len(pre_src)}字符)"

            )
    if CProblemType.字典使用 in find_type and gpt_dict is not None:
        if val := gpt_dict.check_dic_use(pre_dst, tran, ignore_spaces=korean):
            problem_list.append(val)
    if korean and CProblemType.数字不符 in find_type:
        missing = _numbers(post_src) - _numbers(post_dst)
        if missing:
            problem_list.append(f"数字不符：{' '.join(missing.elements())}")
    if CProblemType.引入英文 in find_type:
        if not contains_english(post_src) and contains_english(pre_dst):
            eng_chars = contains_english(post_dst)
            if len(eng_chars)>4:
                problem_list.append(f"引入英文：{eng_chars}")
    if CProblemType.语言不通 in find_type:
        if korean:
            new_han = [c for c in post_dst if "\u4e00" <= c <= "\u9fff" and c not in pre_src]
            hangul = [c for c in post_dst if "\uac00" <= c <= "\ud7a3"]
            if new_han and len(new_han) > len(hangul):
                problem_list.append(f"语言不通-疑似中文：{''.join(dict.fromkeys(new_han))[:20]}")
        elif "zh" in projectConfig.target_lang:
            if not is_all_gbk(pre_dst):
                non_gbk_whites=["♪","♥"]
                non_gbk_chars = is_all_gbk(post_dst)
                for non_gbk_white in non_gbk_whites:
                    non_gbk_chars = non_gbk_chars.replace(non_gbk_white,"")
                if non_gbk_chars !="":
                    problem_list.append(f"语言不通-非GBK：{non_gbk_chars}")
    if CProblemType.缺控制符 in find_type:
        control_list_src = extract_control_substrings(pre_src)
        # 用「子串包含」而不是「token 精确相等」判断是否保留：extract_control_substrings
        # 是按 ASCII 连续段切词的，源文 `[石浦城跡/いしうらじょうあと]`（括号内是日文，
        # 非 ASCII）切出 ['[', '/', ']']，译文 `[石浦城迹/shipuchengji]`（括号内是罗马字，
        # `]` 又在允许字符集里）会把它们并成一个 token `/shipuchengji]`——精确比较就会
        # 误报「缺控制符：/ ]」。真正的控制符（如 `<color=red>`）丢没丢，子串包含同样判得出来。
        lost_list = [
            control_src for control_src in control_list_src
            if control_src not in pre_dst and control_src not in post_dst
        ]
        if lost_list:
            problem_list.append(f"缺控制符：{' '.join(lost_list)}")
    if CProblemType.独白男他 in find_type:
        if tran.speaker == "" and "他" in post_dst:
            if not any(exclude in post_dst for exclude in MONOLOGUE_MALE_HE_EXCLUDES):
                problem_list.append("独白男他")

    if arinashi_dict != {}:
        for key, value in arinashi_dict.items():
            if key not in pre_src and value in post_dst:
                problem_list.append(f"本无 {key} 译有 {value}")
            if key in pre_src and value not in post_dst:
                problem_list.append(f"本有 {key} 译无 {value}")

    if "(Failed)" in post_dst:
        problem_list.append("翻译失败")

    return problem_list


class CommonProblemPlugin(GProblemPlugin):
    problem_types = CProblemType
    sentence_length_threshold: int = 17

    def gtp_init(self, plugin_conf, project_conf):
        self.sentence_length_threshold = normalize_sentence_length_threshold(
            plugin_conf.get("Settings", {}).get("avgSentenceLengthThreshold", 17)
        )

    def check(self, tran, project_config, gpt_dict=None) -> list[str]:
        return _check_problems(tran, project_config, gpt_dict, self.sentence_length_threshold)
