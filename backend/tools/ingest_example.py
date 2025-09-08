# 示例：抓取/清洗/分块并入向量库的脚本（占位）
# 生产环境请用 Claude Sonnet 3.5 生成更完善的清洗脚本与规则

import os
import sys

# Ensure backend root is on sys.path when run directly
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.services.vectorstore import InMemoryVectorStore


def simple_chunk(text, max_len=500):
    # 极简分块：按句号切分并合并到接近 max_len
    sents = [s.strip() for s in text.split('。') if s.strip()]
    chunks = []
    cur = ''
    for s in sents:
        if len(cur) + len(s) > max_len:
            if cur:
                chunks.append(cur)
            cur = s
        else:
            cur = (cur + '。' + s) if cur else s
    if cur:
        chunks.append(cur)
    return chunks


def fake_embed(text):
    # 占位 embedding：使用字符 ord 值的简易向量（仅测试用，非真实）
    return [float(sum(ord(c) for c in text) % 100) for _ in range(8)]


def ingest_example(docs):
    vs = InMemoryVectorStore()
    for i, doc in enumerate(docs):
        chunks = simple_chunk(doc)
        embeddings = [fake_embed(c) for c in chunks]
        metadatas = [{'source': f'doc{i}', 'text': c} for c in chunks]
        ids = [f'doc{i}_chunk{j}' for j in range(len(chunks))]
        vs.upsert(embeddings, metadatas, ids)
    return vs


if __name__ == '__main__':
    docs = [
        '示例法规条文一：关于消费者保护的若干条款。... 更多文本。',
        '示例金融建议：预算分配、债务重组、税务优化等。'
    ]
    store = ingest_example(docs)
    print('ingested', len(store.store))
