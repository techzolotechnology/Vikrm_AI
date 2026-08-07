"""
Script to check DB schema and seed default data.
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "data", "vikrm.db")
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cur.fetchall()]
print(f"Total tables: {len(tables)}")
print("Tables:", tables)

for t in ["users", "conversations", "messages", "agents", "workflows", "projects", "memories", "folders"]:
    if t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = cur.fetchone()[0]
        print(f"Table '{t}': {cnt} records")

conn.close()
