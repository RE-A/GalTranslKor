"""Q6: 경고가 난 줄만 원문과 함께 다시 검토(Mock Ollama, 합성 문장). 품질 효과 판정이 아님."""
import asyncio
import json
from pathlib import Path

from GalTransl.Backend.OllamaQuality import warning_problems
from GalTransl.Loader import load_transList
from ollama_mock import mock_ollama
from test_ollama_ko import batch, config, engine


def request(payload):
    return json.loads(payload["messages"][-1]["content"])


def translate(texts):
    def action(payload):
        return {"translations": [{"id": line["id"], "text": texts[line["source"]]}
                                 for line in request(payload)["input"]]}
    return action


def review(changes):
    def action(payload):
        return {"reviews": [{"id": item["id"], **changes.get(item["source"], {"changed": False, "text": item["draft"]})}
                            for item in request(payload)["items"]]}
    return action


SRC = ["１０時に会おう。", "雨だ。", "{name}は３人で来た。", "風が吹いた。"]
DRAFT = {"１０時に会おう。": "열 시에 만나자.", "雨だ。": "비다.",
         "{name}は３人で来た。": "{name}은 셋이서 왔다.", "風が吹いた。": "바람이 불었다."}


def _run(tmp_path, actions, **options):
    source = load_transList([{"message": m} for m in SRC])[0]
    with mock_ollama(actions) as (url, calls):
        async def run():
            e = engine(config(tmp_path, url, followingContext=0, **options))
            try:
                await batch(e, source, tmp_path, size=4)
            finally:
                await e.shutdown()
            return e
        e = asyncio.run(run())
    return source, calls, e


def test_missing_numbers_are_a_warning():
    assert any("number" in w for w in warning_problems("１０時に会おう。", "열 시에 만나자."))
    assert not any("number" in w for w in warning_problems("１０時に会おう。", "10시에 만나자."))
    assert not any("number" in w for w in warning_problems("%02dです", "%02d입니다"))


def test_review_is_off_by_default(tmp_path):
    source, calls, _ = _run(tmp_path, [translate(DRAFT)])
    assert len(calls) == 1 and all(r.proofread_zh == "" for r in source)


def test_only_warned_lines_are_reviewed_and_valid_fix_is_kept(tmp_path):
    fix = {"１０時に会おう。": {"changed": True, "text": "10시에 만나자.", "reason": "숫자 복원"},
           # 제어 변수를 잃은 수정은 거절되고 초벌 번역이 남아야 함
           "{name}は３人で来た。": {"changed": True, "text": "그는 3명이서 왔다.", "reason": "숫자"}}
    source, calls, e = _run(tmp_path, [translate(DRAFT), review(fix)], reviewWarnings=True)
    assert len(calls) == 2
    system = calls[1][1]["messages"][0]["content"]
    items = request(calls[1][1])["items"]
    assert "검토" in system
    assert [i["source"] for i in items] == ["１０時に会おう。", "{name}は３人で来た。"]
    assert items[0]["draft"] == "열 시에 만나자." and items[0]["warnings"]
    first, _, third, _ = source
    assert first.pre_dst == "열 시에 만나자."  # 초벌은 보존
    assert first.proofread_zh == first.post_dst == "10시에 만나자."
    assert first.proofread_by.endswith(":review")
    assert third.proofread_zh == "" and third.post_dst == "{name}은 셋이서 왔다."
    log = [json.loads(l) for f in (tmp_path / "ollama_ko_logs").glob("review-*.jsonl")
           for l in f.read_text(encoding="utf-8").splitlines()]
    assert [(r["source"], r["accepted"]) for r in log] == [("１０時に会おう。", True), ("{name}は３人で来た。", False)]
    from GalTransl.OllamaKoTools import _read_cache
    cache = _read_cache(tmp_path, "scene.json")
    assert cache[1]["proofread_dst"] == "10시에 만나자." and cache[1]["pre_dst"] == "열 시에 만나자."
    assert e.stats["review_changed"] == 1 and e.stats["review_rejected"] == 1


def test_sampling_reviews_normal_lines_and_bad_reply_keeps_drafts(tmp_path):
    source, calls, e = _run(tmp_path, [translate(DRAFT), (200, "not json")],
                            reviewWarnings=False, reviewSampleEvery=2)
    assert [i["source"] for i in request(calls[1][1])["items"]] == ["雨だ。", "風が吹いた。"]
    assert all(r.proofread_zh == "" for r in source)  # 실패해도 번역은 그대로
    assert e.stats["review_failed"] == 1


def test_review_cap(tmp_path):
    source, calls, _ = _run(tmp_path, [translate(DRAFT), review({})],
                            reviewWarnings=True, reviewMaxLines=1)
    assert len(request(calls[1][1])["items"]) == 1
