"""流式输出解析器（增强版）

本实现使用 json.JSONDecoder.raw_decode 做增量解析：
- 处理前导噪声（比如 SSE 的 "data:" 前缀或其他文本）
- 在缓冲区中尝试提取第一个完整 JSON 对象并返回
- 若解析不完整则返回 None，等待更多片段
"""
from typing import Optional
import json
import re


class StreamJSONBuilder:
    """增量 JSON 构造器：累积文本片段，尝试解析并提取第一个完整的 JSON 对象。"""

    def __init__(self, max_buffer: int = 20000):
        self.buffer = ''
        self.max_buffer = max_buffer
        self._decoder = json.JSONDecoder()

    def _find_json_start(self) -> Optional[int]:
        m = re.search(r'[\{\[]', self.buffer)
        return m.start() if m else None

    def feed(self, chunk: str) -> Optional[dict]:
        """Feed 一个文本片段，若能解析出一个完整 JSON 则返回该对象，否则返回 None。

        说明：当 buffer 中包含多个 JSON 时，每次调用会返回第一个；上层可继续调用以提取后续对象。
        如果传入空字符串或 None，则会尝试从已有缓冲区中解析剩余对象（便于循环提取）。
        """
        # 清洗并追加新片段（若有）
        if chunk:
            # 处理 Gemini/一般 SSE 格式：按行拆分，去除每行开头的 data: 前缀，忽略 data: [DONE]
            lines = chunk.splitlines()
            for line in lines:
                line_clean = re.sub(r'^\s*data:\s*', '', line)
                if not line_clean:
                    continue
                if line_clean.strip() == '[DONE]':
                    continue
                # 追加到缓冲区（不额外插入换行），因为我们期待 JSON 可能直接拼接
                self.buffer += line_clean

        # 如果缓冲为空，则没有可解析的数据
        if not self.buffer:
            return None

        # 防止缓冲无限增长
        if len(self.buffer) > self.max_buffer:
            # 保守策略：保留最近的 max_buffer 字符
            self.buffer = self.buffer[-self.max_buffer:]

        # 找到第一个 JSON 开始位置
        start = self._find_json_start()
        if start is None:
            return None

        # 如果有前导噪声，丢弃
        if start > 0:
            self.buffer = self.buffer[start:]

        try:
            obj, end = self._decoder.raw_decode(self.buffer)
            # 切掉已消费的部分
            self.buffer = self.buffer[end:]
            return obj
        except json.JSONDecodeError:
            # 缓冲还不完整，等待更多片段
            return None

    def reset(self):
        self.buffer = ''
