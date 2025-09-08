from app.services.model_clients import create_gemini_client_from_env, DummyModelClientLocal
from app.services.cfp_agent import CFPAgent
from app.models.financials import FinancialStatement


def run():
    client = create_gemini_client_from_env()
    if client is None:
        print('GEMINI not configured, using DummyModelClientLocal')
        client = DummyModelClientLocal()

    agent = CFPAgent(model_client=client)
    fs = FinancialStatement(assets=90000, liabilities=30000, income=9000, expenses=4000)
    print(agent.analyze(fs))


if __name__ == '__main__':
    run()
