"""Bounded Japanese-to-Korean translation through Ollama's HTTP APIs.

File loading, source preprocessing, cache persistence and output writing remain
owned by GalTransl. No model-specific tokenizer or Ollama SDK is required.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import math
from pathlib import Path
import time
from urllib.parse import urlsplit, urlunsplit

import httpx

from GalTransl import LOGGER
from GalTransl.Backend.BaseTranslate import BaseTranslate
from GalTransl.Backend.OllamaPrompts import (
    RESPONSE_SCHEMA, build_system_prompt, load_characters, load_korean_guideline,
    select_characters,
)
from GalTransl.Backend.OllamaQuality import FAILED_PREFIX, validate_translation
from GalTransl.Cache import save_transCache_to_json

LOG_FOLDER = "ollama_ko_logs"
# Upstream Chinese pre/post dictionaries rewrite Chinese text and must not touch Korean output.
CHINESE_DICTS = {"00通用字典_译前.txt", "00通用字典_译后.txt", "00通用字典_符号_译后.txt",
                 "01H字典_矫正_译前.txt", "GPT字典.txt"}


class _ContentFailure(Exception):
    """Retries exhausted on an unusable response; the batch may be retried smaller."""


def _number(cfg, name, default, minimum, maximum, *, integer=False):
    value = cfg.get(name, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Ollama.{name} must be numeric")
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"Ollama.{name} must be between {minimum} and {maximum}")
    if integer and int(value) != value:
        raise ValueError(f"Ollama.{name} must be an integer")
    return int(value) if integer else float(value)


def _endpoint(value, api):
    if not isinstance(value, str):
        raise ValueError("Ollama.endpoint must be a URL")
    parsed = urlsplit(value.strip())
    if (parsed.scheme not in ("http", "https") or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("Ollama.endpoint must be an HTTP(S) URL without credentials/query")
    path = parsed.path.rstrip("/")
    for suffix in ("/v1/chat/completions", "/api/chat", "/v1", "/api"):
        if path.endswith(suffix):
            path = path[:-len(suffix)]
            break
    path += "/api/chat" if api == "native" else "/v1/chat/completions"
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


class OllamaTranslate(BaseTranslate):
    def __init__(self, config):
        # Keep this backend independent of the Chinese default guideline and
        # OpenAI token pools. Reuse only lifecycle/progress/cancellation helpers.
        self.pj_config = config
        cfg = config.projectConfig.get("backendSpecific", {}).get("Ollama", {})
        if not isinstance(cfg, dict):
            raise ValueError("backendSpecific.Ollama must be an object")
        if config.getKey("language", "ja2ko") not in ("ko", "ja2ko"):
            raise ValueError("Ollama-ko requires common.language: ja2ko")
        if config.getKey("splitFile", "no") != "no":
            raise ValueError("Ollama-ko requires splitFile: no for sequential context")
        self.model = cfg.get("model", "")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("Set backendSpecific.Ollama.model to your installed model name")
        self.model = self.model.strip()
        self.api = cfg.get("api", "native")
        if self.api not in ("native", "openai"):
            raise ValueError("Ollama.api must be native or openai")
        self.url = _endpoint(cfg.get("endpoint", "http://127.0.0.1:11434"), self.api)
        self.api_key = cfg.get("apiKey", "ollama")
        if not isinstance(self.api_key, str) or not self.api_key.strip():
            raise ValueError("Ollama.apiKey must be a non-empty string")
        self.attempts = _number(cfg, "maxAttempts", 3, 1, 10, integer=True)
        self.retry_wait = _number(cfg, "retryWait", 1, 0, 30)
        self.timeout = _number(cfg, "apiTimeout", 180, 0.01, 3600)
        self.max_chars = _number(cfg, "maxPromptChars", 6000, 1000, 1000000, integer=True)
        self.num_ctx = _number(cfg, "numCtx", 8192, 512, 1048576, integer=True)
        self.num_predict = _number(cfg, "numPredict", 2048, 1, 131072, integer=True)
        self.temperature = _number(cfg, "temperature", 0.2, 0, 2)
        self.following_lines = _number(cfg, "followingContext", 4, 0, 64, integer=True)
        self.min_ratio = _number(cfg, "minLengthRatio", 0.2, 0, 1)
        common = {"contextLines": config.getKey("gpt.contextNum", 8)}
        self.context_lines = _number(common, "contextLines", 8, 0, 128, integer=True)
        self.think = cfg.get("think", False)
        if self.think is not None and not isinstance(self.think, bool):
            raise ValueError("Ollama.think must be true, false or null")
        self.on_failure = cfg.get("onFailure", "mark")
        if self.on_failure not in ("mark", "stop"):
            raise ValueError("Ollama.onFailure must be mark or stop")
        self.allow = cfg.get("allowJapanese", []) or []
        if not isinstance(self.allow, list) or not all(isinstance(w, str) for w in self.allow):
            raise ValueError("Ollama.allowJapanese must be a list of strings")
        project_dir = config.getProjectDir()
        character_file = cfg.get("characterFile", "characters.yaml")
        if not isinstance(character_file, str):
            raise ValueError("Ollama.characterFile must be a file name")
        self.characters = load_characters(Path(project_dir, character_file)) if character_file else []
        self.system_prompt = build_system_prompt(
            load_korean_guideline(config.getKey("gpt.translation_guideline"), project_dir),
            speech_to=any("speech_to" in c["profile"] for c in self.characters))
        self._warn_chinese_dictionaries(config)
        glossary = getattr(config, "gpt_dic", None)
        entries = [{"source": d.search_word, "target": d.replace_word, "note": d.note}
                   for d in getattr(glossary, "_dic_list", [])]
        identity = json.dumps({
            "contract": 2, "prompt": self.system_prompt, "model": self.model,
            "url": self.url, "temperature": self.temperature,
            "numCtx": self.num_ctx, "numPredict": self.num_predict,
            "think": self.think, "contextLines": self.context_lines,
            "followingContext": self.following_lines, "maxPromptChars": self.max_chars,
            "glossary": entries, "characters": [c["profile"] for c in self.characters],
            "minLengthRatio": self.min_ratio, "allowJapanese": self.allow,
        }, ensure_ascii=False, sort_keys=True)
        self.cache_identity = "Ollama-ko:" + self.model + ":" + hashlib.sha256(identity.encode()).hexdigest()[:20]
        self.log_dir = Path(project_dir, LOG_FOLDER)
        self.run_id = time.strftime("%Y%m%d-%H%M%S")
        self.started = time.monotonic()
        self.stats = {"requests": 0, "retries": 0, "batch_shrinks": 0, "lines_translated": 0,
                      "lines_failed": 0, "prompt_tokens": 0, "output_tokens": 0,
                      "model_seconds": 0.0, "errors": {}}
        # Local Ollama should not be routed through an unrelated system proxy.
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api == "openai" else None
        self.client = httpx.AsyncClient(timeout=self.timeout, trust_env=False, headers=headers)

    @staticmethod
    def _warn_chinese_dictionaries(config):
        section = config.projectConfig.get("dictionary", {}) or {}
        for key in ("preDict", "postDict", "gpt.dict"):
            for name in section.get(key, []) or []:
                if isinstance(name, str) and Path(name.replace("(project_dir)", "")).name in CHINESE_DICTS:
                    LOGGER.warning("Ollama-ko: dictionary.%s의 %s는 중국어용 기본 사전입니다. 한국어 번역에서는 제거하세요.", key, name)

    def _names_for(self, row, gpt_dic=None):
        speaker = row.get_speaker_name()
        if not speaker:
            return ()
        names = {speaker}
        for character in self.characters:
            if speaker in character["names"] and character["profile"]["ko"]:
                names.add(character["profile"]["ko"])
        if gpt_dic is not None and gpt_dic.get_dst(speaker):
            names.add(gpt_dic.get_dst(speaker))
        return tuple(names)

    def _check(self, row, text, gpt_dic=None):
        validate_translation(row.post_src, text, allow=self.allow,
                             speakers=self._names_for(row, gpt_dic), min_ratio=self.min_ratio)

    def validate_cache_hits(self, trans_list, hits, misses):
        """Invalidate foreign/stale/invalid translations before reporting hits."""
        accepted = set()
        gpt_dic = getattr(self.pj_config, "gpt_dic", None)
        for row in hits:
            if not row.post_src:
                accepted.add(id(row))
                continue
            try:
                if row.trans_by != self.cache_identity:
                    raise ValueError("model/prompt/settings changed")
                self._check(row, row.pre_dst, gpt_dic)
                if row.proofread_zh:
                    self._check(row, row.proofread_zh, gpt_dic)
            except ValueError:
                row.pre_dst = row.post_dst = row.proofread_zh = ""
                row.trans_by = row.proofread_by = ""
                row.cache_miss_reason = "ollama_validation_or_settings_changed"
            else:
                accepted.add(id(row))
        return ([r for r in trans_list if id(r) in accepted],
                [r for r in trans_list if id(r) not in accepted])

    def _messages(self, batch, context, following, glossary):
        texts = [r.post_src for r in batch] + [c["source"] for c in context + following]
        speakers = [r.get_speaker_name() for r in batch] + [c["speaker"] for c in context + following]
        body = {
            "characters": select_characters(self.characters, speakers, texts),
            "glossary": glossary, "context": context,
            "input": [{"id": i, "speaker": r.get_speaker_name(), "source": r.post_src}
                      for i, r in enumerate(batch, 1)],
            "following_context": following,
        }
        return [{"role": "system", "content": self.system_prompt},
                {"role": "user", "content": json.dumps(body, ensure_ascii=False)}]

    def _following(self, trans_list, start):
        if not self.following_lines:
            return []
        rows = []
        for row in trans_list[start:]:
            if row.post_src:
                rows.append({"speaker": row.get_speaker_name(), "source": row.post_src})
                if len(rows) == self.following_lines:
                    break
        return rows

    def _prepare(self, trans_list, position, candidates, gpt_dic):
        previous = trans_list[:position]
        context = [{"speaker": r.get_speaker_name(), "source": r.post_src,
                    "translation": r.proofread_zh or r.pre_dst}
                   for r in previous
                   if r.pre_dst and not r.trans_by.endswith(FAILED_PREFIX)
                   ][-self.context_lines:] if self.context_lines else []
        selected = []
        messages = None
        for row in candidates:
            batch = selected + [row]
            following = self._following(trans_list, position + len(batch))
            glossary = gpt_dic.gen_prompt(batch, type="gpt") if gpt_dic is not None else ""
            trial = self._messages(batch, context, following, glossary)
            if not selected:
                # Drop the oldest history first, then the farthest look-ahead.
                while sum(len(m["content"]) for m in trial) > self.max_chars and (context or following):
                    if context:
                        context.pop(0)
                    else:
                        following.pop()
                    trial = self._messages(batch, context, following, glossary)
            if sum(len(m["content"]) for m in trial) > self.max_chars:
                if not selected:
                    raise ValueError(f"Line {row.index} plus prompt/glossary exceeds maxPromptChars={self.max_chars}; increase the budget or split the source explicitly")
                break
            selected.append(row)
            messages = trial
        return selected, messages

    async def _post(self, payload):
        # Poll stop_event while the model is generating, not just between calls.
        task = asyncio.create_task(self.client.post(self.url, json=payload))
        try:
            while not task.done():
                self._check_stop_requested()
                await asyncio.wait({task}, timeout=0.1)
            self._check_stop_requested()
            return await task
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    def _record_usage(self, data):
        if self.api == "native":
            prompt, output = data.get("prompt_eval_count"), data.get("eval_count")
            duration = data.get("total_duration")
            if isinstance(duration, (int, float)):
                self.stats["model_seconds"] += duration / 1e9
        else:
            usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
            prompt, output = usage.get("prompt_tokens"), usage.get("completion_tokens")
        for key, value in (("prompt_tokens", prompt), ("output_tokens", output)):
            if isinstance(value, int) and not isinstance(value, bool):
                self.stats[key] += value
        if self.api == "native" and isinstance(prompt, int) and prompt >= self.num_ctx:
            raise ValueError(f"context window overflow: prompt used {prompt} of numCtx={self.num_ctx} tokens")

    async def _translate(self, batch, messages, gpt_dic=None):
        payload = {"model": self.model, "messages": messages, "stream": False}
        if self.api == "native":
            payload.update(format=RESPONSE_SCHEMA, options={
                "temperature": self.temperature, "num_ctx": self.num_ctx,
                "num_predict": self.num_predict,
            })
            if self.think is not None:
                payload["think"] = self.think
        else:
            payload.update(temperature=self.temperature, max_tokens=self.num_predict,
                           response_format={"type": "json_object"})
        for attempt in range(1, self.attempts + 1):
            self._check_stop_requested()
            content_error = False
            try:
                self.stats["requests"] += 1
                response = await self._post(payload)
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError("model response must be an object")
                self._record_usage(data)
                if self.api == "native":
                    if data.get("done") is not True or data.get("done_reason") == "length":
                        raise ValueError("incomplete model response")
                    content = data["message"]["content"]
                else:
                    choice = data["choices"][0]
                    if not isinstance(choice, dict):
                        raise ValueError("model choice must be an object")
                    if choice.get("finish_reason") != "stop":
                        raise ValueError("incomplete model response")
                    content = choice["message"]["content"]
                result = json.loads(content)["translations"]
                if not isinstance(result, list) or len(result) != len(batch):
                    raise ValueError("translation count mismatch")
                texts = []
                for index, (row, item) in enumerate(zip(batch, result), 1):
                    if not isinstance(item, dict) or type(item.get("id")) is not int or item["id"] != index:
                        raise ValueError("translation ID/order mismatch")
                    text = item.get("text")
                    self._check(row, text, gpt_dic)
                    texts.append(text)
                return texts
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status not in (408, 429) and status < 500:
                    raise RuntimeError(f"Ollama HTTP {status}; check endpoint/model/settings") from exc
                reason = f"HTTP {status}"
            except httpx.TransportError as exc:
                reason = type(exc).__name__ + ": " + str(exc)
            except (ValueError, KeyError, TypeError, IndexError) as exc:
                reason = type(exc).__name__ + ": " + str(exc)
                content_error = True
            errors = self.stats["errors"]
            key = reason.split(":")[0] if not content_error else reason.split(": ", 1)[-1][:80]
            errors[key] = errors.get(key, 0) + 1
            if attempt == self.attempts:
                message = f"Ollama translation failed after {attempt} attempts ({reason}); validated earlier batches remain cached"
                if content_error:
                    raise _ContentFailure(message)
                raise RuntimeError(message)
            self.stats["retries"] += 1
            LOGGER.warning("Ollama-ko retry %s/%s: %s", attempt, self.attempts, reason)
            await self._interruptible_sleep(min(30, self.retry_wait * 2 ** (attempt - 1)))
        raise AssertionError("unreachable")

    def _mark_failed(self, filename, row, reason):
        failed = FAILED_PREFIX + row.post_src
        row.pre_dst = row.post_dst = failed
        row.trans_by = self.cache_identity + FAILED_PREFIX
        row.problem = "翻译失败"  # upstream marker understood by retranslFail/problem filters
        self.stats["lines_failed"] += 1
        record = {"file": filename, "index": row.index, "speaker": row.get_speaker_name(),
                  "source": row.post_src, "reason": reason}
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            with open(self.log_dir / f"failures-{self.run_id}.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError as exc:
            LOGGER.error("Ollama-ko: failed to write failure log: %s", exc)
        LOGGER.error("Ollama-ko: %s line %s left untranslated: %s", filename, row.index, reason)

    async def batch_translate(self, filename, cache_file_path, trans_list,
                              num_pre_request, retry_failed=False, gpt_dic=None,
                              proofread=False, retran_key="", translist_hit=None,
                              translist_unhit=None):
        if proofread:
            raise ValueError("Ollama-ko supports translation, not the separate proofread pass")
        size = _number({"batchSize": num_pre_request}, "batchSize", 8, 1, 128, integer=True)
        limit = size
        pending = {id(r) for r in (translist_unhit if translist_unhit is not None else trans_list)}
        results = []
        position = 0
        while position < len(trans_list):
            self._check_stop_requested()
            if id(trans_list[position]) not in pending:
                position += 1
                continue
            # Stop at a cache hit so intervening cached dialogue becomes context.
            candidates = []
            for row in trans_list[position:position + limit]:
                if id(row) not in pending:
                    break
                candidates.append(row)
            selected, messages = self._prepare(trans_list, position, candidates, gpt_dic)
            try:
                texts = await self._translate(selected, messages, gpt_dic)
            except _ContentFailure as exc:
                if len(selected) > 1:
                    limit = max(1, len(selected) // 2)
                    self.stats["batch_shrinks"] += 1
                    LOGGER.warning("Ollama-ko: %s line %s, batch %s -> %s after repeated invalid responses",
                                   filename, selected[0].index, len(selected), limit)
                    continue
                if self.on_failure == "stop":
                    raise RuntimeError(str(exc)) from None
                self._check_stop_requested()
                self._mark_failed(filename, selected[0], str(exc))
                await save_transCache_to_json(selected, cache_file_path, project_dir=self.pj_config.getProjectDir())
                self.pj_config.bar(1)
                results.extend(selected)
                position += 1
                continue
            self._check_stop_requested()
            for row, text in zip(selected, texts):
                row.pre_dst = row.post_dst = text
                row.trans_by = self.cache_identity
            await save_transCache_to_json(selected, cache_file_path, project_dir=self.pj_config.getProjectDir())
            for row in selected:
                self._record_runtime_success(filename, row)
            self.stats["lines_translated"] += len(selected)
            self.pj_config.bar(len(selected))
            results.extend(selected)
            position += len(selected)
            limit = min(size, limit * 2)
        return results

    def _write_stats(self):
        stats = dict(self.stats, model=self.model, api=self.api, run_id=self.run_id,
                     wall_seconds=round(time.monotonic() - self.started, 3),
                     model_seconds=round(self.stats["model_seconds"], 3),
                     numCtx=self.num_ctx, contextLines=self.context_lines,
                     followingContext=self.following_lines)
        if stats["lines_translated"] and stats["wall_seconds"]:
            stats["lines_per_minute"] = round(stats["lines_translated"] * 60 / stats["wall_seconds"], 2)
        LOGGER.info("Ollama-ko 통계: 요청 %s, 재시도 %s, 번역 %s줄, 실패 %s줄, 입력 토큰 %s, 출력 토큰 %s",
                    stats["requests"], stats["retries"], stats["lines_translated"],
                    stats["lines_failed"], stats["prompt_tokens"], stats["output_tokens"])
        if not stats["requests"]:
            return
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            (self.log_dir / f"stats-{self.run_id}.json").write_text(
                json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            LOGGER.error("Ollama-ko: failed to write statistics: %s", exc)

    async def shutdown(self):
        try:
            self._write_stats()
        finally:
            await self.client.aclose()
