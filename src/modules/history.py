"""
历史记录模块
"""

import json
import os
from datetime import datetime

from .config import HISTORY_DIR


class HistoryManager:
    def __init__(self):
        self.records = []
        self._load()

    def _load(self):
        os.makedirs(HISTORY_DIR, exist_ok=True)
        files = sorted(os.listdir(HISTORY_DIR), reverse=True)
        for f in files:
            if f.endswith(".json"):
                try:
                    with open(os.path.join(HISTORY_DIR, f), "r", encoding="utf-8") as fh:
                        self.records.append(json.load(fh))
                except Exception:
                    continue

    def add_record(self, record: dict):
        record["id"] = str(len(self.records) + 1)
        record["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.records.insert(0, record)
        self._save(record)

    def _save(self, record):
        filename = f"{record['timestamp'].replace(':', '-')}_{record['id']}.json"
        filepath = os.path.join(HISTORY_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

    def get_all(self):
        return self.records

    def clear(self):
        self.records = []
        for f in os.listdir(HISTORY_DIR):
            if f.endswith(".json"):
                os.remove(os.path.join(HISTORY_DIR, f))