from typing import List, Dict, Any


class BaseVectorStore:
    def upsert(self, embeddings: List[List[float]], metadatas: List[Dict[str, Any]], ids: List[str]):
        raise NotImplementedError()

    def query(self, vector: List[float], top_k: int = 5):
        raise NotImplementedError()


class InMemoryVectorStore(BaseVectorStore):
    def __init__(self):
        self.store = []  # list of (id, vector, metadata)

    def upsert(self, embeddings: List[List[float]], metadatas: List[Dict[str, Any]], ids: List[str]):
        for i, v in enumerate(embeddings):
            self.store.append((ids[i], v, metadatas[i]))

    def query(self, vector: List[float], top_k: int = 5):
        # 朴素的 L2 距离排序
        import math

        def dist(a, b):
            return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

        scored = [(dist(vector, v), _id, meta) for (_id, v, meta) in self.store]
        scored.sort(key=lambda x: x[0])
        return scored[:top_k]
