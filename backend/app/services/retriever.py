from typing import List


class BaseRetriever:
    """检索器抽象基类。实际实现应连接向量数据库并返回文本 chunk 列表。"""

    def get(self, query: str, top_k: int = 5) -> List[str]:
        raise NotImplementedError()


class InMemoryRetriever(BaseRetriever):
    """一个非常简单的内存检索器，用于本地测试：存储一组文档并基于关键词返回匹配项。"""

    def __init__(self, docs=None):
        self.docs = docs or []

    def add(self, text: str):
        self.docs.append(text)

    def get(self, query: str, top_k: int = 5):
        # 简单包含匹配
        matches = [d for d in self.docs if query.lower() in d.lower()]
        return matches[:top_k] if matches else self.docs[:top_k]
