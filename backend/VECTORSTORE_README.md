Vector Store 使用说明（示例）

- `app/services/vectorstore.py` 包含 `InMemoryVectorStore` 的示例实现，适合本地测试。
- `tools/ingest_example.py` 演示了简单的抓取/分块/伪向量化并入库的流程，供调试使用。
- 生产环境推荐：
  - 使用 Claude Sonnet 3.5 生成清洗 + chunk 脚本
  - 将 `InMemoryVectorStore` 替换为 Pinecone/Chroma 的实际客户端实现
