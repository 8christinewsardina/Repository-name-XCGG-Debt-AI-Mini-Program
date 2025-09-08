from fastapi.testclient import TestClient
from app.main import app


def run_test():
    client = TestClient(app)
    payload = {"assets": 120000, "liabilities": 40000, "income": 15000, "expenses": 8000}
    r = client.post('/api/v1/reports', json=payload)
    print('status_code=', r.status_code)
    print('response=', r.json())
    assert r.status_code == 200
    data = r.json()
    assert 'debt_ratio' in data and 'analysis' in data


if __name__ == '__main__':
    run_test()
