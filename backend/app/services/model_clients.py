from typing import Any, Dict, Optional
import os
import time


class ModelClientBase:
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        raise NotImplementedError()

    async def async_generate(self, prompt: str, max_tokens: int = 512) -> str:
        """异步生成：默认实现会调用同步生成（保持兼容）。实现方可覆盖以使用异步 HTTP 客户端。"""
        return self.generate(prompt, max_tokens=max_tokens)


class DummyModelClientLocal(ModelClientBase):
    """本地模拟客户端（与 CFPAgent 的 DummyModelClient 类似），用于测试。"""

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        import json
        return json.dumps({
            "overview": "（模拟）基于检索与输入的摘要",
            "recommendations": ["优先还款", "检查利率并优化贷款结构"],
            "risks": ["高利率风险"],
            "confidence": 0.75
        })


class GeminiClientSkeleton(ModelClientBase):
    """Gemini 客户端骨架：仅包含调用接口的占位方法，实际应填入 SDK/HTTP调用细节并处理密钥。"""

    def __init__(self, api_key: str = ''):
        self.api_key = api_key

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        # TODO: 实现对接 Gemini 的 HTTP 或 SDK 调用并返回 text
        raise NotImplementedError('Please implement Gemini API call here')


class GeminiClientHTTP(ModelClientBase):
    """更健壮的 Gemini HTTP 客户端模板：

    特性：
      - 支持 sync 调用（使用 httpx/requests 中任意可用者）
      - 基本重试与指数退避
      - 可选流式接口占位（需要根据实际 API 调整）
      - 从环境变量读取配置：GEMINI_API_KEY / GEMINI_BASE_URL / GEMINI_TIMEOUT
    注意：在 CI/生产中请通过 repository secrets 注入 GEMINI_API_KEY，并启用 GEMINI_ENABLED=true
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = 'https://api.gemini.example/v1', timeout: int = 30):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.base_url = base_url or os.getenv('GEMINI_BASE_URL', base_url)
        self.timeout = int(os.getenv('GEMINI_TIMEOUT', str(timeout)))

    def _select_http_client(self):
        # prefer httpx if available for nicer API and optional async
        try:
            import httpx
            return 'httpx', httpx
        except Exception:
            try:
                import requests
                return 'requests', requests
            except Exception:
                raise RuntimeError('Either httpx or requests is required for GeminiClientHTTP; pip install httpx or requests')

    def _parse_response(self, data: Any) -> str:
        # Try common response shapes
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            # Gemini-like may put content under ['candidates'][0]['content'] or ['output'] or ['text']
            if 'text' in data and isinstance(data['text'], str):
                return data['text']
            if 'output' in data and isinstance(data['output'], str):
                return data['output']
            if 'candidates' in data and isinstance(data['candidates'], list) and len(data['candidates']) > 0:
                first = data['candidates'][0]
                if isinstance(first, dict) and 'content' in first:
                    return first['content']
            if 'choices' in data and isinstance(data['choices'], list) and len(data['choices']) > 0:
                first = data['choices'][0]
                if isinstance(first, dict):
                    if 'text' in first:
                        return first['text']
                    if 'message' in first and isinstance(first['message'], dict):
                        return first['message'].get('content') or str(first['message'])
        # fallback
        return str(data)

    def generate(self, prompt: str, max_tokens: int = 512, stream: bool = False) -> str:
        """同步生成接口。stream=True 为占位支持（目前返回完整文本）。"""
        if not self.api_key:
            raise RuntimeError('GEMINI API key not configured')

        client_name, client = self._select_http_client()

        url = f"{self.base_url.rstrip('/')}/generate"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"prompt": prompt, "max_tokens": max_tokens}

        max_attempts = 3
        backoff_base = 0.5
        last_exc = None
        for attempt in range(1, max_attempts + 1):
            try:
                if client_name == 'httpx':
                    resp = client.post(url, json=payload, headers=headers, timeout=self.timeout)
                    resp.raise_for_status()
                    data = resp.json()
                else:
                    resp = client.post(url, json=payload, headers=headers, timeout=self.timeout)
                    resp.raise_for_status()
                    try:
                        data = resp.json()
                    except Exception:
                        data = resp.text

                # If stream requested: placeholder behavior (real streaming requires SSE/HTTP/WS support)
                if stream:
                    # For now return full parsed string; keep API shape stable for callers
                    return self._parse_response(data)

                return self._parse_response(data)
            except Exception as e:
                last_exc = e
                sleep_for = backoff_base * (2 ** (attempt - 1))
                time.sleep(sleep_for)
        # If no exception captured, raise a generic error
        if last_exc is None:
            raise RuntimeError('GeminiClientHTTP failed without exception')
        raise last_exc


class GeminiClientAsync(GeminiClientHTTP):
    """使用 httpx.AsyncClient 的异步实现（如果 httpx 可用）。"""

    async def async_generate(self, prompt: str, max_tokens: int = 512, stream: bool = False) -> str:
        if not self.api_key:
            raise RuntimeError('GEMINI API key not configured')

        try:
            import httpx
        except Exception:
            raise RuntimeError('httpx is required for async operations; pip install httpx')

        url = f"{self.base_url.rstrip('/')}/generate"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"prompt": prompt, "max_tokens": max_tokens}

        max_attempts = 3
        backoff_base = 0.5
        last_exc = None
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                    resp.raise_for_status()
                    try:
                        data = resp.json()
                    except Exception:
                        data = resp.text

                    return self._parse_response(data)
                except Exception as e:
                    last_exc = e
                    sleep_for = backoff_base * (2 ** (attempt - 1))
                    await __import__('asyncio').sleep(sleep_for)

        if last_exc is None:
            raise RuntimeError('GeminiClientAsync failed without exception')
        raise last_exc

    async def async_stream_generate(self, prompt: str, max_tokens: int = 512):
        """异步流式生成：返回一个 async generator，逐段 yield text chunk。

        注意：实际流格式依赖供应商 API（SSE / chunked JSON / line-delimited）；此实现使用 httpx.AsyncClient.stream
        并逐行 yield 文本片段，供上层增量组装器处理。
        """
        try:
            import httpx
        except Exception:
            raise RuntimeError('httpx is required for async streaming; pip install httpx')

        if not self.api_key:
            raise RuntimeError('GEMINI API key not configured')

        url = f"{self.base_url.rstrip('/')}/generate"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"prompt": prompt, "max_tokens": max_tokens, "stream": True}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream('POST', url, json=payload, headers=headers) as resp:
                    resp.raise_for_status()
                    # iterate lines to better handle SSE / line-delimited formats
                    async for raw_line in resp.aiter_lines():
                        if not raw_line:
                            continue
                        line = raw_line.strip()
                        # SSE style: lines like 'data: {...}'
                        if line.startswith('data:'):
                            line = line[len('data:'):].strip()
                            if line == '[DONE]':
                                break
                            yield line
                        else:
                            # sometimes providers emit plain JSON fragments or text
                            if line == '[DONE]':
                                break
                            yield line
            except Exception as e:
                # propagate so caller can decide fallback
                raise


def create_gemini_client_from_env() -> Optional[GeminiClientHTTP]:
    enabled = os.getenv('GEMINI_ENABLED', 'false').lower() in ('1', 'true', 'yes')
    if not enabled:
        return None
    key = os.getenv('GEMINI_API_KEY')
    base = os.getenv('GEMINI_BASE_URL', 'https://api.gemini.example/v1')
    if key:
        # prefer async client if httpx available
        try:
            import httpx
            return GeminiClientAsync(api_key=key, base_url=base)
        except Exception:
            return GeminiClientHTTP(api_key=key, base_url=base)
    return None
