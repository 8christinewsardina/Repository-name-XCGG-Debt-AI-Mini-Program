"""简单审计记录器：按 JSON 行写入本地审计日志（供合规和追溯）。"""
import json
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, 'audit.log')


def audit_record(record: dict):
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        **record
    }
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
