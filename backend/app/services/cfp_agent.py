from typing import Dict, Any, List, Optional
from app.models.financials import FinancialStatement
from app.services.retriever import InMemoryRetriever
from app.services.model_clients import DummyModelClientLocal


class BaseModelClient:
    """模型客户端抽象：具体实现应封装模型API调用（Gemini 2.5 Pro / Claude / GPT 等）。

    请在生产中实现具体客户端：
      - 支持 sync/async 调用
      - 支持长上下文拆分、系统/用户/assistant 分段
      - 支持重试与超时
    """

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        raise NotImplementedError()


class CFPAgent:
    """更完善的 CFPAgent：包含 RAG 流程和 Prompt 模板。

    工作流程（高层）：
      1. 接收 FinancialStatement + 可选用户查询
      2. 使用 Retriever（知识库）检索相关文档片段（chunk）
      3. 构建 Prompt（系统指令 + 用户输入 + 检索到的上下文）
      4. 调用基础模型客户端（优先 Gemini）生成分析
      5. 解析并返回结构化 JSON

    注意：当前实现包含占位的 retriever 与 model client hook，实际部署需要实现向量数据库检索和模型 SDK。
    """

    def __init__(self, model_client: Optional[object] = None, retriever: Optional[object] = None):
        self.model_client = model_client or DummyModelClientLocal()
        self.retriever = retriever or InMemoryRetriever(docs=[
            "示例法规片段：消费者债务相关法律条款摘要",
            "示例金融建议：债务重组与利率优化最佳实践"
        ])

    # Gemini 指南：生成 prompt 时，请遵守以下模板并让模型输出严格的 JSON（no extra commentary）
    PROMPT_TEMPLATE = (
        "SYSTEM: 你是一个专业的注册理财顾问，输出必须遵循 JSON schema。\n"
        "INPUT: {input_summary}\n"
        "CONTEXT: {context_chunks}\n"
        "TASK: 请基于 INPUT 和 CONTEXT 提供（1）概述 overview，(2) 分步建议 recommendations 列表，(3) 风险点 risks 列表，(4) confidence（0-1 浮点数）。\n"
        "OUTPUT: 严格返回 JSON，仅包含 keys: overview, recommendations, risks, confidence。"
    )

    def _build_prompt(self, fs: FinancialStatement, docs: List[str]) -> str:
        input_summary = (
            f"assets={fs.assets}, liabilities={fs.liabilities}, income={fs.income}, expenses={fs.expenses}"
        )
        context_chunks = "\n---\n".join(docs) if docs else ""
        return self.PROMPT_TEMPLATE.format(input_summary=input_summary, context_chunks=context_chunks)

    def _retrieve(self, query: str, top_k: int = 5) -> List[str]:
        # 占位：实际实现应调用 self.retriever.get(query, top_k)
        if self.retriever:
            return self.retriever.get(query, top_k)
        return []

    def analyze(self, fs: FinancialStatement) -> Dict[str, Any]:
        # 1. 检索
        query = f"用户负债率分析 assets:{fs.assets} liabilities:{fs.liabilities}"
        docs = self._retrieve(query)

        # 2. 构建 prompt
        # ensure docs is List[str]
        if not isinstance(docs, list):
            docs = [str(docs)] if docs else []
        else:
            docs = [str(d) for d in docs]
        prompt = self._build_prompt(fs, docs)

        # 3. 调用模型
        if self.model_client is None:
            # 回退到简单规则引擎（保守返回），避免抛出错误
            debt_ratio = fs.debt_ratio()
            overview = f"用户当前负债率为 {debt_ratio:.2f}"
            recs = ["建议优先偿还高息负债，或调整预算以减少支出。"] if debt_ratio > 0.6 else ["保持良好预算习惯并建立应急基金。"]
            return {"overview": overview, "recommendations": recs, "risks": [], "confidence": 0.6}

        # 支持 model_client 的异步实现：优先调用 async_generate 或 await 可等待对象
        raw = None
        try:
            # prefer async_generate if available via getattr
            import asyncio, inspect
            async_gen = getattr(self.model_client, 'async_generate', None)
            gen = getattr(self.model_client, 'generate', None)

            loop_running = False
            try:
                loop = asyncio.get_event_loop()
                loop_running = loop.is_running()
            except Exception:
                loop_running = False

            if async_gen is not None and callable(async_gen):
                # If event loop is running (e.g. TestClient/uvicorn), avoid creating coroutines here
                if loop_running:
                    # fallback to sync generate if available
                    if gen is None:
                        raise RuntimeError('model_client has no generate method')
                    raw = gen(prompt)
                else:
                    # safe to run coroutine; ensure we pass a coroutine object
                    coro = async_gen(prompt)
                    if inspect.iscoroutine(coro):
                        raw = asyncio.run(coro)
                    elif inspect.isawaitable(coro):
                        async def _wrap():
                            return await coro
                        raw = asyncio.run(_wrap())
                    else:
                        raw = coro
            else:
                if gen is None:
                    raise RuntimeError('model_client has no generate method')
                maybe = gen(prompt)
                if inspect.isawaitable(maybe):
                    if loop_running:
                        # cannot await here; fallback to sync generate
                        raw = gen(prompt)
                    else:
                        if inspect.iscoroutine(maybe):
                            raw = asyncio.run(maybe)
                        elif inspect.isawaitable(maybe):
                            async def _wrap2():
                                return await maybe
                            raw = asyncio.run(_wrap2())
                        else:
                            raw = maybe
                else:
                    raw = maybe
        except Exception:
            # 如果在异步执行中出错，回退为同步调用（若可用）或规则引擎
            try:
                gen = getattr(self.model_client, 'generate', None)
                if gen is None:
                    raise RuntimeError('model_client has no generate method')
                raw = gen(prompt)
            except Exception:
                debt_ratio = fs.debt_ratio()
                overview = f"用户当前负债率为 {debt_ratio:.2f}"
                recs = ["建议优先偿还高息负债，或调整预算以减少支出。"] if debt_ratio > 0.6 else ["保持良好预算习惯并建立应急基金。"]
                return {"overview": overview, "recommendations": recs, "risks": [], "confidence": 0.6}

        # 4. 解析模型输出（期望严格 JSON）
        try:
            import json
            from app.schemas.agent_output import AgentOutputModel

            parsed = json.loads(str(raw))
            # 使用 Pydantic 验证严格的 JSON schema（符合 Gemini 指定要求）
            model = AgentOutputModel.parse_obj(parsed)
            return model.dict()
        except Exception as e:
            # 若解析失败，返回模型原始文本封装在 overview 中，同时信心为 0
            return {"overview": str(raw), "recommendations": [], "risks": [], "confidence": 0.0, "_error": str(e)}

    async def analyze_async(self, fs: FinancialStatement) -> Dict[str, Any]:
        """异步版本：优先使用 model_client.async_generate，如果不可用则在后台线程运行同步 generate。"""
        # 1. 检索（假设 retriever 也可能有 async 接口）
        query = f"用户负债率分析 assets:{fs.assets} liabilities:{fs.liabilities}"
        docs = []
        retrieve = getattr(self.retriever, 'aget', None) or getattr(self.retriever, 'get', None)
        if callable(retrieve):
            try:
                res = retrieve(query, 5)
                # 如果返回 awaitable，则 await，否则直接使用
                import inspect
                if inspect.isawaitable(res):
                    docs = await res
                else:
                    docs = res
            except Exception:
                docs = []

        # 2. 构建 prompt
        prompt = self._build_prompt(fs, docs)

        # 3. 调用 model_client 的异步接口或在线程池中运行同步方法
        raw = None
        async_gen = getattr(self.model_client, 'async_generate', None)
        if async_gen and callable(async_gen):
            try:
                res = async_gen(prompt)
                import inspect
                if inspect.isawaitable(res):
                    raw = await res
                else:
                    raw = res
            except Exception:
                # 回退到 sync generate
                gen = getattr(self.model_client, 'generate', None)
                if gen:
                    raw = gen(prompt)
        else:
            gen = getattr(self.model_client, 'generate', None)
            if gen:
                # run sync in threadpool
                import asyncio
                loop = asyncio.get_running_loop()
                raw = await loop.run_in_executor(None, lambda: gen(prompt))

        # 4. 解析与验证
        try:
            import json
            from app.schemas.agent_output import AgentOutputModel
            parsed = json.loads(str(raw))
            model = AgentOutputModel.parse_obj(parsed)
            result = model.dict()
            from app.services.compliance import check_compliance
            from app.services.audit import audit_record
            result = check_compliance(result)
            audit_record({"agent": "CFPAgent", "input": str(fs.dict()), "result": result})
            return result
        except Exception as e:
            fallback = {"overview": str(raw), "recommendations": [], "risks": [], "confidence": 0.0, "_error": str(e)}
            from app.services.compliance import check_compliance
            from app.services.audit import audit_record
            fallback = check_compliance(fallback)
            audit_record({"agent": "CFPAgent", "input": str(fs.dict()), "result": fallback})
            return fallback

    async def analyze_stream_async(self, fs: FinancialStatement) -> Dict[str, Any]:
        """尝试用模型的流式接口增量组装 JSON，并在可用时立即返回验证通过的结果。"""
        from app.services.stream_parser import StreamJSONBuilder

        query = f"用户负债率分析 assets:{fs.assets} liabilities:{fs.liabilities}"
        docs = []
        retrieve = getattr(self.retriever, 'aget', None) or getattr(self.retriever, 'get', None)
        if callable(retrieve):
            try:
                res = retrieve(query, 5)
                import inspect
                if inspect.isawaitable(res):
                    docs = await res
                else:
                    docs = res
            except Exception:
                docs = []

        if not isinstance(docs, list):
            docs = [str(docs)] if docs else []
        else:
            docs = [str(d) for d in docs]

        prompt = self._build_prompt(fs, docs)

        stream_gen = getattr(self.model_client, 'async_stream_generate', None)
        if not stream_gen or not callable(stream_gen):
            # 不支持流式，回退到普通 async 分析
            return await self.analyze_async(fs)

        builder = StreamJSONBuilder()
        try:
            import inspect
            stream_obj = stream_gen(prompt, max_tokens=512)
            # 如果返回的是 awaitable，需要先 await 得到 async iterable
            if inspect.isawaitable(stream_obj):
                stream_obj = await stream_obj

            # 期望 stream_obj 是异步可迭代对象
            if not hasattr(stream_obj, '__aiter__'):
                # 不支持异步迭代，回退
                raise RuntimeError('stream does not provide async iterator')

            async for chunk in stream_obj:
                try:
                    obj = builder.feed(chunk)
                    if obj is not None:
                        # 尝试用 schema 校验
                        from app.schemas.agent_output import AgentOutputModel
                        model = AgentOutputModel.parse_obj(obj)
                        result = model.dict()
                        from app.services.compliance import check_compliance
                        from app.services.audit import audit_record
                        result = check_compliance(result)
                        audit_record({"agent": "CFPAgent", "input": str(fs.dict()), "result": result})
                        return result
                except Exception:
                    # 当前片段不能组成合法 JSON，继续等待更多片段
                    continue
        except Exception:
            # 流式过程出错，回退
            pass

        # 流式结束但未能得到合法 JSON，回退到非流式生成
        try:
            gen = getattr(self.model_client, 'async_generate', None)
            if gen and callable(gen):
                res = gen(prompt)
                import inspect
                if inspect.isawaitable(res):
                    raw = await res
                else:
                    raw = res
                import json
                from app.schemas.agent_output import AgentOutputModel
                parsed = json.loads(str(raw))
                model = AgentOutputModel.parse_obj(parsed)
                result = model.dict()
                from app.services.compliance import check_compliance
                from app.services.audit import audit_record
                result = check_compliance(result)
                audit_record({"agent": "CFPAgent", "input": str(fs.dict()), "result": result})
                return result
        except Exception:
            pass

        # 最后退化到规则引擎
        debt_ratio = fs.debt_ratio()
        overview = f"用户当前负债率为 {debt_ratio:.2f}"
        recs = ["建议优先偿还高息负债，或调整预算以减少支出。"] if debt_ratio > 0.6 else ["保持良好预算习惯并建立应急基金。"]
        fallback = {"overview": overview, "recommendations": recs, "risks": [], "confidence": 0.6}
        from app.services.compliance import check_compliance
        from app.services.audit import audit_record
        fallback = check_compliance(fallback)
        audit_record({"agent": "CFPAgent", "input": str(fs.dict()), "result": fallback})
        return fallback


class DummyModelClient(BaseModelClient):
    """本地模拟模型客户端：将 prompt 标记并返回一个JSON字符串，方便本地测试。"""

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        # 解析 prompt 中的输入摘要（粗略）并返回示例 JSON
        import json
        return json.dumps({
            "overview": "基于输入的简要概述（模拟）",
            "recommendations": ["优先还款", "建立应急基金"],
            "risks": ["高负债风险"],
            "confidence": 0.8
        })

