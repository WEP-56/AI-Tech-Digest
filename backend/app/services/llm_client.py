"""LLM 适配器：统一封装 OpenAI Completion / Responses / Anthropic Messages 接口"""
import json
import time
import httpx
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMResult:
    """LLM调用统一结果"""
    text: str = ""
    raw_response: dict = field(default_factory=dict)
    model: str = ""
    provider_type: str = ""
    usage: dict = field(default_factory=dict)
    success: bool = False
    error: str = ""
    latency_ms: int = 0


class BaseLLMClient:
    """LLM客户端基类"""

    def __init__(self, config: dict):
        self.config = config
        self.base_url = config.get("base_url", "").rstrip("/")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model_name", "")
        self.temperature = config.get("temperature", 0.3)
        self.max_tokens = config.get("max_output_tokens", 4000)
        self.timeout = config.get("timeout_seconds", 60)
        self.retry_count = config.get("retry_count", 2)

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        raise NotImplementedError

    def _call_with_retry(self, fn) -> LLMResult:
        last_error = ""
        for attempt in range(self.retry_count + 1):
            start = time.time()
            try:
                result = fn()
                result.latency_ms = int((time.time() - start) * 1000)
                if result.success:
                    return result
                last_error = result.error
            except Exception as e:
                last_error = str(e)
                result = LLMResult(success=False, error=last_error, latency_ms=int((time.time() - start) * 1000))
            if attempt < self.retry_count:
                time.sleep(1)
        return LLMResult(success=False, error=last_error or "未知错误")


class OpenAICompletionClient(BaseLLMClient):
    """OpenAI-compatible Chat Completions 接口 (/v1/chat/completions)"""

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        def _call() -> LLMResult:
            url = f"{self.base_url}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload, headers=headers)

            if resp.status_code != 200:
                return LLMResult(
                    success=False,
                    error=f"HTTP {resp.status_code}: {resp.text[:500]}",
                    raw_response={"status_code": resp.status_code, "body": resp.text[:500]},
                )
            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            return LLMResult(
                text=text,
                raw_response=data,
                model=self.model,
                provider_type="openai_completion",
                usage=usage,
                success=True,
            )

        return self._call_with_retry(_call)


class OpenAIResponsesClient(BaseLLMClient):
    """OpenAI-compatible Responses 接口 (/v1/responses)"""

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        def _call() -> LLMResult:
            url = f"{self.base_url}/v1/responses"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "input": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
            }
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload, headers=headers)

            if resp.status_code != 200:
                return LLMResult(
                    success=False,
                    error=f"HTTP {resp.status_code}: {resp.text[:500]}",
                    raw_response={"status_code": resp.status_code, "body": resp.text[:500]},
                )
            data = resp.json()
            # 优先使用 output_text
            text = data.get("output_text", "")
            if not text:
                output = data.get("output", [])
                if output and isinstance(output, list):
                    for item in output:
                        if item.get("type") == "message":
                            content = item.get("content", [])
                            if content and isinstance(content, list):
                                text = content[0].get("text", "")
                                break
            usage = data.get("usage", {})
            return LLMResult(
                text=text,
                raw_response=data,
                model=self.model,
                provider_type="openai_responses",
                usage=usage,
                success=True,
            )

        return self._call_with_retry(_call)


class AnthropicMessagesClient(BaseLLMClient):
    """Anthropic Messages 接口 (/v1/messages)"""

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        def _call() -> LLMResult:
            url = f"{self.base_url}/v1/messages"
            version = self.config.get("anthropic_version", "2023-06-01")
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": version,
                "content-type": "application/json",
            }
            payload = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_prompt},
                ],
            }
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload, headers=headers)

            if resp.status_code != 200:
                return LLMResult(
                    success=False,
                    error=f"HTTP {resp.status_code}: {resp.text[:500]}",
                    raw_response={"status_code": resp.status_code, "body": resp.text[:500]},
                )
            data = resp.json()
            content = data.get("content", [])
            text = ""
            if content and isinstance(content, list):
                text_parts = [
                    item.get("text", "")
                    for item in content
                    if isinstance(item, dict) and item.get("type") == "text" and item.get("text")
                ]
                if text_parts:
                    text = "\n".join(text_parts)
                else:
                    text = content[0].get("text", "") if isinstance(content[0], dict) else ""
            if not text.strip():
                return LLMResult(
                    success=False,
                    error="LLM response did not contain text content",
                    raw_response=data,
                )
            usage = data.get("usage", {})
            return LLMResult(
                text=text,
                raw_response=data,
                model=self.model,
                provider_type="anthropic_messages",
                usage=usage,
                success=True,
            )

        return self._call_with_retry(_call)


def create_llm_client(config: dict) -> BaseLLMClient:
    """根据provider_type创建对应的LLM客户端"""
    provider = config.get("provider_type", "")
    clients = {
        "openai_completion": OpenAICompletionClient,
        "openai_responses": OpenAIResponsesClient,
        "anthropic_messages": AnthropicMessagesClient,
    }
    client_cls = clients.get(provider)
    if not client_cls:
        raise ValueError(f"不支持的接口类型: {provider}")
    return client_cls(config)
