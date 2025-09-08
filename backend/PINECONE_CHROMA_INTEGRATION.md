向量数据库集成（Pinecone / Chroma）示例说明

1) 概述
- 提供如何将清洗后的 chunk 向 Pinecone 或 Chroma 写入的脚本示例。
- 脚本为模板：在缺少依赖或 API key 时不会发起外网调用。

2) Pinecone 示例（使用 pinecone-client）
- env: PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX
- 伪代码：

```python
import os
try:
    import pinecone
except Exception:
    raise RuntimeError('pinecone not installed; pip install pinecone-client')

api_key = os.getenv('PINECONE_API_KEY')
if not api_key:
    raise RuntimeError('PINECONE_API_KEY not set')

pinecone.init(api_key=api_key, environment=os.getenv('PINECONE_ENV'))
index = pinecone.Index(os.getenv('PINECONE_INDEX'))
# upsert vectors
# index.upsert(vectors=[(id, vector, metadata), ...])
```

3) Chroma 示例（使用 chromadb）
- env: none required for local
- 伪代码：

```python
try:
    import chromadb
except Exception:
    raise RuntimeError('chromadb not installed; pip install chromadb')

client = chromadb.Client()
# client.create_collection('mycoll')
# collection.add(documents=[...], metadatas=[...], ids=[...])
```

4) 安全与流程
- 在 CI/生产中使用 Secrets 管理 API keys
- 在 Ingestion 阶段做去重与来源标注
- 推荐使用 Claude Sonnet 3.5 生成清洗脚本

5) 本地测试
- 我们提供 `tools/ingest_example.py` 与 `app/services/vectorstore.py` 作为本地替代，方便离线测试。
