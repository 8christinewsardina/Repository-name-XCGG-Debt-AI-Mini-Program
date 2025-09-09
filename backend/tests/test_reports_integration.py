import json
from fastapi.testclient import TestClient
from app.main import app
from app.services.cfp_agent import CFPAgent
from app.services.model_clients import DummyModelClientLocal

client = TestClient(app)


def test_start_and_poll_report(monkeypatch, tmp_path):
    # monkeypatch CFPAgent to use DummyModelClientLocal to avoid real Gemini calls
    def dummy_init(self, model_client=None, retriever=None):
        # call original init with dummy client
        from app.services.retriever import InMemoryRetriever
        self.model_client = DummyModelClientLocal()
        self.retriever = retriever or InMemoryRetriever(docs=["doc1"])

    monkeypatch.setattr(CFPAgent, '__init__', dummy_init)

    payload = {
        "assets": 100000,
        "liabilities": 20000,
        "income": 10000,
        "expenses": 5000
    }

    # start job
    r = client.post('/api/v1/reports/start', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert 'job_id' in data
    job_id = data['job_id']

    # poll until done or timeout
    import time
    deadline = time.time() + 5
    status = None
    while time.time() < deadline:
        pr = client.get(f'/api/v1/reports/{job_id}')
        assert pr.status_code == 200
        job = pr.json()
        status = job.get('status')
        if status == 'done' or status == 'error':
            break
        time.sleep(0.2)

    assert status == 'done'
    assert job['result']['analysis']['confidence'] >= 0.0
