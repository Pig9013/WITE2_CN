#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal OpenAI-compatible / Ollama client (stdlib only)."""
from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

log = logging.getLogger("llm")


@dataclass
class LLMConfig:
    provider: str = "openai"          # openai | ollama
    base_url: str = "http://127.0.0.1:1234/v1"
    model: str = "qwen2.5-14b-instruct"
    api_key: str = "lm-studio"
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 2048
    timeout: int = 180
    retries: int = 3
    num_ctx: int = 8192

    @classmethod
    def from_dict(cls, d: dict) -> "LLMConfig":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


class LLMError(RuntimeError):
    pass


class ChatClient:
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg

    def _post(self, path: str, payload: dict) -> dict:
        url = self.cfg.base_url.rstrip("/") + path
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.cfg.api_key:
            req.add_header("Authorization", f"Bearer {self.cfg.api_key}")
        last_err: Optional[Exception] = None
        for attempt in range(1, self.cfg.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.cfg.timeout) as r:
                    return json.loads(r.read().decode("utf-8", "replace"))
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")[:500]
                last_err = LLMError(f"HTTP {e.code}: {body}")
                if e.code < 500 and e.code != 429:
                    break
            except Exception as e:
                last_err = e
            wait = min(20, 2 ** attempt)
            log.warning("LLM request failed (%s/%s): %s; retry in %ss", attempt, self.cfg.retries, last_err, wait)
            time.sleep(wait)
        raise LLMError(f"LLM request failed: {last_err}")

    def health(self) -> dict:
        url = self.cfg.base_url.rstrip("/")
        if self.cfg.provider == "openai":
            url += "/models"
        else:
            url = url.replace("/v1", "") + "/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8", "replace"))

    def chat(self, messages: list[dict], temperature: Optional[float] = None,
             max_tokens: Optional[int] = None) -> str:
        cfg = self.cfg
        if cfg.provider == "openai":
            payload = {
                "model": cfg.model,
                "messages": messages,
                "temperature": cfg.temperature if temperature is None else temperature,
                "top_p": cfg.top_p,
                "max_tokens": cfg.max_tokens if max_tokens is None else max_tokens,
                "stream": False,
            }
            data = self._post("/chat/completions", payload)
            try:
                return data["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError) as e:
                raise LLMError(f"bad OpenAI response: {data}") from e
        else:
            payload = {
                "model": cfg.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": cfg.temperature if temperature is None else temperature,
                    "top_p": cfg.top_p,
                    "num_ctx": cfg.num_ctx,
                    "num_predict": cfg.max_tokens if max_tokens is None else max_tokens,
                },
            }
            data = self._post("/api/chat", payload)
            try:
                return data["message"]["content"].strip()
            except (KeyError, TypeError) as e:
                raise LLMError(f"bad Ollama response: {data}") from e

    def chat_json(self, messages: list[dict], **kwargs) -> Any:
        text = self.chat(messages, **kwargs).strip()
        fence = chr(96) * 3
        if text.startswith(fence):
            text = re.sub(r"^" + fence + r"[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*" + fence + r"$", "", text)
        for start in (text.find("["), text.find("{")):
            if start >= 0:
                try:
                    return json.loads(text[start:])
                except json.JSONDecodeError:
                    pass
        raise LLMError(f"response is not JSON: {text[:300]}")


def make_client(cfg: LLMConfig) -> ChatClient:
    return ChatClient(cfg)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
    ap.add_argument("--model", default="qwen2.5-14b-instruct")
    ap.add_argument("--provider", default="openai")
    ap.add_argument("--prompt", default="用中文回答：装甲掷弹兵是什么？")
    args = ap.parse_args()
    c = ChatClient(LLMConfig(provider=args.provider, base_url=args.base_url, model=args.model))
    print(c.health())
    print(c.chat([{"role": "user", "content": args.prompt}]))
