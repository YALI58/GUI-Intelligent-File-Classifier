#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests


class AICategorizationError(Exception):
    pass


class AICategorizationAuthError(AICategorizationError):
    pass


class AICategorizationNetworkError(AICategorizationError):
    pass


class AICategorizationRefusedError(AICategorizationError):
    pass


@dataclass
class AICategorizationResult:
    category: str
    confidence: float
    reason: str


def _safe_folder_name(name: str) -> str:
    name = (name or "").strip()
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", " ", name)
    name = name.strip(" .")
    return name[:80] if name else "未分类"


def _extract_keywords_from_name(path_str: str) -> List[str]:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff]+", " ", path_str.lower())
    parts = [p for p in cleaned.split() if len(p) > 1]
    stop = {"the", "and", "for", "with", "from", "this", "that", "file", "download", "temp"}
    parts = [p for p in parts if p not in stop]
    uniq = []
    seen = set()
    for p in parts:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
        if len(uniq) >= 12:
            break
    return uniq


def _desensitize_text(text: str) -> str:
    if not text:
        return text
    try:
        # email
        text = re.sub(r"([A-Za-z0-9._%+-]{1,64})@([A-Za-z0-9.-]+\.[A-Za-z]{2,})", "***@\\2", text)
        # phone (simple)
        text = re.sub(r"(?<!\d)(1\d{10})(?!\d)", "1**********", text)
        text = re.sub(r"(?<!\d)(\d{3})[- ]?(\d{4})[- ]?(\d{4})(?!\d)", "\\1****\\3", text)
        # CN ID card (simple)
        text = re.sub(r"(?<!\d)(\d{6})(\d{8})(\d{3})([0-9Xx])(?!\d)", "\\1********\\3*", text)
    except Exception:
        return text
    return text


class FileCategorizationAIClient:
    def __init__(
        self,
        api_key: str,
        provider: str = "openai",
        endpoint: str = "https://api.openai.com/v1/chat/completions",
        model: str = "gpt-4o-mini",
        proxy: str = "",
        timeout_seconds: int = 30,
    ):
        self.api_key = api_key
        self.provider = provider
        self.endpoint = endpoint
        self.model = model
        self.proxy = proxy
        self.timeout_seconds = timeout_seconds

    def _proxies(self) -> Optional[Dict[str, str]]:
        if not self.proxy:
            return None
        return {
            "http": self.proxy,
            "https": self.proxy,
        }

    def validate_key(self) -> Tuple[bool, str]:
        try:
            _ = self.categorize_metadata(
                metadata={
                    "task": "file_categorization",
                    "filename": "example_report_2026_Q1.pdf",
                    "extension": ".pdf",
                    "keywords": ["report", "q1", "2026"],
                },
                allowed_categories=[],
            )
            return True, "有效"
        except AICategorizationAuthError:
            return False, "无效"
        except AICategorizationNetworkError:
            return False, "网络异常"
        except AICategorizationRefusedError:
            return False, "权限受限"
        except AICategorizationError:
            return False, "配置错误"
        except Exception:
            return False, "连接失败"

    def _normalize_endpoint(self) -> str:
        provider = (self.provider or "").strip().lower()
        endpoint = (self.endpoint or "").strip()
        if not endpoint:
            return endpoint

        if provider in {"openai", "openai_compatible"}:
            if endpoint.rstrip("/").endswith("/v1"):
                return endpoint.rstrip("/") + "/chat/completions"
            return endpoint

        if provider == "deepseek":
            base = endpoint.rstrip("/")
            if base.endswith("/v1"):
                return base + "/chat/completions"
            if base.endswith("api.deepseek.com"):
                return base + "/v1/chat/completions"
            return endpoint

        return endpoint

    def categorize_metadata(self, metadata: Dict[str, Any], allowed_categories: List[str]) -> AICategorizationResult:
        task = metadata.get("task")
        if task != "file_categorization":
            raise AICategorizationRefusedError("当前功能仅限于文件分类场景")

        if self.provider.lower() not in {"openai", "openai_compatible", "deepseek"}:
            raise AICategorizationError("不支持的AI服务商")

        system_prompt = (
            "你是智能文件分类助手。你只允许执行文件分类任务，不允许对话、写作、编辑、翻译、总结、代码生成等任何其他任务。"
            "你的输出必须是JSON：{\"category\": string, \"confidence\": number, \"reason\": string}。"
            "category 必须是一个适合作为文件夹名的短字符串。"
        )

        content_snippet = metadata.get("content_snippet")
        user_payload = {
            "function": "file_categorization_only",
            "task": "file_categorization",
            "file_metadata": {
                "filename": metadata.get("filename", ""),
                "extension": metadata.get("extension", ""),
                "keywords": metadata.get("keywords", []),
                "content_snippet": content_snippet,
                "modified_time": metadata.get("modified_time"),
                "created_time": metadata.get("created_time"),
                "size": metadata.get("size"),
            },
            "allowed_categories": allowed_categories[:50] if allowed_categories else [],
            "requirements": {
                "content_snippet_limited": bool(content_snippet),
                "no_full_file_content": True,
                "no_api_key_echo": True,
                "classification_only": True,
            },
        }

        req = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "temperature": 0.2,
        }

        provider = (self.provider or "").strip().lower()
        if provider in {"openai", "openai_compatible"}:
            req["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                self._normalize_endpoint(),
                headers=headers,
                json=req,
                timeout=self.timeout_seconds,
                proxies=self._proxies(),
            )
        except requests.RequestException as e:
            raise AICategorizationNetworkError("分类API调用异常") from e

        if resp.status_code in (401, 403):
            raise AICategorizationAuthError("分类服务鉴权失败")

        if resp.status_code == 404:
            raise AICategorizationError("分类服务地址无效")

        if resp.status_code in (400, 422):
            raise AICategorizationError("分类服务请求参数错误")

        if resp.status_code >= 400:
            raise AICategorizationError("文件分类分析未完成")

        try:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        except Exception as e:
            raise AICategorizationError("文件分类分析未完成") from e

        category = _safe_folder_name(str(parsed.get("category", "")))
        try:
            confidence = float(parsed.get("confidence", 0.0))
        except Exception:
            confidence = 0.0
        reason = str(parsed.get("reason", ""))

        if not category:
            category = "未分类"

        confidence = max(0.0, min(1.0, confidence))
        return AICategorizationResult(category=category, confidence=confidence, reason=reason[:200])


def build_file_metadata(
    file_path_str: str,
    filename_only: bool = True,
    stat: Optional[Any] = None,
    content_assist_enabled: bool = False,
    max_content_chars: int = 2000,
    allowed_text_exts: Optional[List[str]] = None,
    desensitize_enabled: bool = True,
) -> Dict[str, Any]:
    import os
    from pathlib import Path

    file_path = Path(file_path_str)
    keywords = _extract_keywords_from_name(file_path.stem)

    meta: Dict[str, Any] = {
        "task": "file_categorization",
        "filename": file_path.name,
        "extension": file_path.suffix.lower(),
        "keywords": keywords,
    }

    if content_assist_enabled:
        try:
            ext = file_path.suffix.lower()
            exts = allowed_text_exts or []
            exts_norm = [str(x).strip().lower() for x in exts if str(x).strip()]
            if ext in set(exts_norm):
                limit = int(max(0, max_content_chars))
                limit = min(limit, 12000)
                if limit > 0 and file_path.exists() and file_path.is_file():
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        snippet = f.read(limit)
                    if desensitize_enabled:
                        snippet = _desensitize_text(snippet)
                    meta['content_snippet'] = snippet
        except Exception:
            pass

    if not filename_only:
        try:
            s = stat or file_path.stat()
            meta["size"] = getattr(s, "st_size", None)
            meta["modified_time"] = getattr(s, "st_mtime", None)
            meta["created_time"] = getattr(s, "st_ctime", None)
        except Exception:
            pass

    return meta


class AICallUsageTracker:
    def __init__(self):
        self.used_calls = 0
        self.last_call_ts = 0.0

    def mark_call(self):
        self.used_calls += 1
        self.last_call_ts = time.time()
