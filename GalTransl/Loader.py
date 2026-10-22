from GalTransl import LOGGER
from GalTransl.CSentense import *
from os import path
from json import loads
from typing import Union, Tuple, List

def load_transList(json_path_or_list: Union[str, list]) -> Tuple[CTransList, list]:
    """
    从json文件路径、json字符串、json list中载入待翻译列表
    json格式为[{"name":xx/"names":[],"message/pre_src":"xx"},...]
    """
    trans_list: CTransList = []

    if isinstance(json_path_or_list, str):
        if path.exists(json_path_or_list):
            # 如果是文件路径
            with open(json_path_or_list, "r", encoding="utf-8") as f:
                try:
                    json_list = loads(f.read())
                except Exception as e:
                    raise ValueError(f"JSON 파일을 해석할 수 없습니다 {json_path_or_list}: {str(e)}")
        else:
            # 如果是JSON字符串
            try:
                json_list = loads(json_path_or_list)
            except Exception as e:
                raise ValueError(f"JSON 문자열을 해석할 수 없습니다: {str(e)}")
    elif isinstance(json_path_or_list, list):
        json_list = json_path_or_list
    else:
        raise TypeError("입력은 문자열(파일 경로 또는 JSON 문자열)이나 목록이어야 합니다")

    if not isinstance(json_list, list):
        raise ValueError("해석한 JSON이 목록 형식이 아닙니다")

    file_has_name = any(isinstance(item, dict) and ("name" in item or "names" in item) for item in json_list)
    for i, item in enumerate(json_list):
        if not isinstance(item, dict):
            raise ValueError(f"JSON 목록의 {i+1}번째 항목이 dict 형식이 아닙니다")
        
        if "message" not in item:
            raise ValueError(f"JSON 형식이 잘못되었습니다. {i+1}번째 item에 message 필드가 없습니다: {item}")

        name = item.get("name", item.get("names", ""))
        pre_src = item["message"]
        index = item.get("index", i + 1)
        tmp_tran = CSentense(pre_src, name, index)
        tmp_tran.source_file_has_name = file_has_name
        if item.get("scene_break"):  # set by file plugins that know scene boundaries
            tmp_tran.scene_break = True
        
        # 链接上下文
        if trans_list:
            tmp_tran.prev_tran = trans_list[-1]
            trans_list[-1].next_tran = tmp_tran
        trans_list.append(tmp_tran)

    return trans_list, json_list
