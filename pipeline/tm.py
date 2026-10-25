#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite translation memory / resume cache."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sqlite3
import time


class TM:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tm (
                key TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                model TEXT,
                glossary_version TEXT,
                kind TEXT,
                status TEXT,
                issues TEXT,
                created_at REAL,
                updated_at REAL
            )
        """)
        self.conn.commit()

    @staticmethod
    def make_key(model: str, glossary_version: str, source: str, kind: str) -> str:
        h = hashlib.sha1()
        h.update("|".join([model, glossary_version, kind, source]).encode("utf-8"))
        return h.hexdigest()

    def get(self, key: str) -> dict | None:
        row = self.conn.execute(
            "SELECT source,target,status,issues FROM tm WHERE key=? AND status='ok'", (key,)
        ).fetchone()
        if not row:
            return None
        return {"source": row[0], "target": row[1], "status": row[2],
                "issues": json.loads(row[3] or "[]")}

    def put(self, key: str, source: str, target: str, model: str,
            glossary_version: str, kind: str, status: str = "ok",
            issues: list | None = None) -> None:
        now = time.time()
        self.conn.execute("""
            INSERT INTO tm(key,source,target,model,glossary_version,kind,status,issues,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(key) DO UPDATE SET
              target=excluded.target, status=excluded.status, issues=excluded.issues,
              updated_at=excluded.updated_at
        """, (key, source, target, model, glossary_version, kind, status,
              json.dumps(issues or [], ensure_ascii=False), now, now))
        self.conn.commit()

    def count(self) -> dict:
        rows = self.conn.execute("SELECT status, COUNT(*) FROM tm GROUP BY status").fetchall()
        return {r[0]: r[1] for r in rows}

    def export_csv(self, path: str) -> int:
        rows = self.conn.execute(
            "SELECT source,target,kind,status FROM tm ORDER BY updated_at"
        ).fetchall()
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["source", "target", "kind", "status"])
            w.writerows(rows)
        return len(rows)

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tm", default=os.path.join(os.path.dirname(__file__), "..", "data", "translations", "tm.sqlite"))
    ap.add_argument("--export", default="")
    args = ap.parse_args()
    tm = TM(args.tm)
    print(tm.count())
    if args.export:
        print("exported", tm.export_csv(args.export))
