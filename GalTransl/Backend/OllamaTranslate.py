"""Bounded Japanese-to-Korean translation through Ollama's HTTP APIs.

File loading, source preprocessing, cache persistence and output writing remain
owned by GalTransl. No model-specific tokenizer or Ollama SDK is required.
"""
from __future__ import annotations

import asyncio
from collections import Counter
import hashlib
import json
import math
import re
from urllib.parse import urlsplit, urlunsplit

import httpx

from GalTransl import LOGGER
from GalTransl.Backend.BaseTranslate import BaseTranslate
from GalTransl.Backend.OllamaPrompts import KOREAN_SYSTEM_PROMPT, RESPONSE_SCHEMA
from GalTransl.Cache import save_transCache_to_json


_MARKERS = re.compile(
    r"\{[^{}\r\n]+\}|%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[sdfiuoxX]|"
    r"\[[^\[\]\r\n]+\]|</?[^<>\r\n]+>|\\(?:[A-Za-z]+(?:\[[^\]\r\n]*\])?|.)"
)
_KANA = re.compile(r"[\u3041-\u3096\u30a1-\u30fa\uff66-\uff9d]")
_HANGUL = re.compile(r"[\uac00-\ud7a3\u3131-\u318e]")
_JAPANESE = re.compile(r"[\u3041-\u30fa\u4e00-\u9fff]")


def validate_translation(source: str, text: str) -> None:
    """Structural checks, not a claim of semantic translation quality."""
    if not isinstance(text, str) or (source.strip() and not text.strip()):
        raise ValueError("empty/non-string translation")
    if Counter(_MARKERS.findall(source)) != Counter(_MARKERS.findall(text)):
        raise ValueError("placeholder/control marker mismatch")
    if re.findall(r"\r\n|\r|\n", source) != re.findall(r"\r\n|\r|\n", text):
        raise ValueError("line break mismatch")
    plain_source = _MARKERS.sub("", source)
    plain_text = _MARKERS.sub("", text)
    if _KANA.search(plain_text):
        raise ValueError("Japanese kana remains")
    if _JAPANESE.search(plain_source) and not _HANGUL.search(plain_text):
        raise ValueError("Korean translation required")
    if text.strip().startswith("```") or "<think>" in text:
        raise ValueError("model commentary is not a translation")


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
        self.attempts = _number(cfg, "maxAttempts", 3, 1, 10, integer=True)
        self.retry_wait = _number(cfg, "retryWait", 1, 0, 30)
        self.timeout = _number(cfg, "apiTimeout", 180, 0.01, 3600)
        self.max_chars = _number(cfg, "maxPromptChars", 6000, 1000, 1000000, integer=True)
        self.num_ctx = _number(cfg, "numCtx", 8192, 512, 1048576, integer=True)
        self.num_predict = _number(cfg, "numPredict", 2048, 1, 131072, integer=True)
        self.temperature = _number(cfg, "temperature", 0.2, 0, 2)
        common = {"contextLines": config.getKey("gpt.contextNum", 8)}
        self.context_lines = _number(common, "contextLines", 8, 0, 128, integer=True)
        self.think = cfg.get("think", False)
        if self.think is not None and not isinstance(self.think, bool):
            raise ValueError("Ollama.think must be true, false or null")
        glossary = getattr(config, "gpt_dic", None)
        entries = [{"source": d.search_word, "target": d.replace_word, "note": d.note}
                   for d in getattr(glossary, "_dic_list", [])]
        identity = json.dumps({
            "contract": 1, "prompt": KOREAN_SYSTEM_PROMPT, "model": self.model,
            "url": self.url, "temperature": self.temperature,
            "numCtx": self.num_ctx, "numPredict": self.num_predict,
            "think": self.think, "contextLines": self.context_lines,
            "maxPromptChars": self.max_chars, "glossary": entries,
        }, ensure_ascii=False, sort_keys=True)
        self.cache_identity = "Ollama-ko:" + self.model + ":" + hashlib.sha256(identity.encode()).hexdigest()[:20]
        # Local Ollama should not be routed through an unrelated system proxy.
        self.client = httpx.AsyncClient(timeout=self.timeout, trust_env=False)

    def validate_cache_hits(self, trans_list, hits, misses):
        """Invalidate foreign/stale/invalid translations before reporting hits."""
        accepted = set()
        for row in hits:
            if not row.post_src:
                accepted.add(id(row))
                continue
            try:
                if row.trans_by != self.cache_identity:
                    raise ValueError("model/prompt/settings changed")
                validate_translation(row.post_src, row.pre_dst)
                if row.proofread_zh:
                    validate_translation(row.post_src, row.proofread_zh)
            except ValueError:
                row.pre_dst = row.post_dst = row.proofread_zh = ""
                row.trans_by = row.proofread_by = ""
                row.cache_miss_reason = "ollama_validation_or_settings_changed"
            else:
                accepted.add(id(row))
        return ([r for r in trans_list if id(r) in accepted],
                [r for r in trans_list if id(r) not in accepted])

    def _messages(self, batch, context, glossary):
        body = {
            "context": context, "glossary": glossary,
            "input": [{"id": i, "speaker": r.get_speaker_name(), "source": r.post_src}
                      for i, r in enumerate(batch, 1)],
        }
        return [{"role": "system", "content": KOREAN_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(body, ensure_ascii=False)}]

    def _prepare(self, candidates, previous, glossary):
        context = [{"speaker": r.get_speaker_name(), "source": r.post_src,
                    "translation": r.proofread_zh or r.pre_dst}
                   for r in previous if r.pre_dst][-self.context_lines:] if self.context_lines else []
        selected = []
        messages = None
        for row in candidates:
            trial = self._messages(selected + [row], context, glossary)
            if not selected:
                while sum(len(m["content"]) for m in trial) > self.max_chars and context:
                    context.pop(0)
                    trial = self._messages([row], context, glossary)
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

    async def _translate(self, batch, messages):
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
            try:
                response = await self._post(payload)
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError("model response must be an object")
                if self.api == "native":
                    if data.get("done") is not True or data.get("done_reason") == "length":
                        raise ValueError("incomplete model response")
                    content = data["message"]["content"]
                else:
                    choice = data["choices"][0]
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
                    validate_translation(row.post_src, text)
                    texts.append(text)
                return texts
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status not in (408, 429) and status < 500:
                    raise RuntimeError(f"Ollama HTTP {status}; check endpoint/model/settings") from exc
                reason = f"HTTP {status}"
            except (httpx.TransportError, ValueError, KeyError, TypeError, IndexError) as exc:
                reason = type(exc).__name__ + ": " + str(exc)
            if attempt == self.attempts:
                raise RuntimeError(f"Ollama translation failed after {attempt} attempts ({reason}); validated earlier batches remain cached")
            LOGGER.warning("Ollama-ko retry %s/%s: %s", attempt, self.attempts, reason)
            await self._interruptible_sleep(min(30, self.retry_wait * 2 ** (attempt - 1)))
        raise AssertionError("unreachable")

    async def batch_translate(self, filename, cache_file_path, trans_list,
                              num_pre_request, retry_failed=False, gpt_dic=None,
                              proofread=False, retran_key="", translist_hit=None,
                              translist_unhit=None):
        if proofread:
            raise ValueError("Ollama-ko supports translation, not the separate proofread pass")
        size = _number({"batchSize": num_pre_request}, "batchSize", 8, 1, 128, integer=True)
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
            for row in trans_list[position:position + size]:
                if id(row) not in pending:
                    break
                candidates.append(row)
            glossary = gpt_dic.gen_prompt(candidates, type="gpt") if gpt_dic is not None else ""
            selected, messages = self._prepare(candidates, trans_list[:position], glossary)
            texts = await self._translate(selected, messages)
            self._check_stop_requested()
            for row, text in zip(selected, texts):
                row.pre_dst = row.post_dst = text
                row.trans_by = self.cache_identity
            await save_transCache_to_json(selected, cache_file_path, project_dir=self.pj_config.getProjectDir())
            for row in selected:
                self._record_runtime_success(filename, row)
            self.pj_config.bar(len(selected))
            results.extend(selected)
            position += len(selected)
        return results

    async def shutdown(self):
        await self.client.aclose()
