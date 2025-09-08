import asyncio
from app.services.cfp_agent import CFPAgent
from app.services.model_clients import DummyModelClientLocal
from app.models.financials import FinancialStatement


async def dummy_stream_gen(prompt: str, max_tokens: int = 512):
    # simulate streaming fragments that eventually assemble to JSON
    parts = ["{\"overview\": \"模拟流式概述\", ", "\"recommendations\": [\"先偿还高息\"], ", "\"risks\": [\"高利率\"], ", "\"confidence\": 0.7}"]
    for p in parts:
        await asyncio.sleep(0.1)
        yield p


class DummyAsyncClient(DummyModelClientLocal):
    async def async_stream_generate(self, prompt: str, max_tokens: int = 512):
        async for c in dummy_stream_gen(prompt, max_tokens=max_tokens):
            yield c


async def run():
    client = DummyAsyncClient()
    agent = CFPAgent(model_client=client)
    fs = FinancialStatement(assets=100000, liabilities=40000, income=10000, expenses=5000)
    res = await agent.analyze_stream_async(fs)
    print(res)


if __name__ == '__main__':
    asyncio.run(run())
