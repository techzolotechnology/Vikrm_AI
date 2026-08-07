import os
import sqlite3
import sys

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "vikrm.db")
if not os.path.exists(db_path):
    print("No DB file found at", db_path)
    sys.exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, role, content FROM messages")
rows = cursor.fetchall()

corrupted_count = 0
for msg_id, role, content in rows:
    if not content:
        continue
    trimmed = content.strip()
    if trimmed == "[object Object]" or "[object Object]" in content or (trimmed.startswith("{") and trimmed.endswith("}")):
        corrupted_count += 1
        print(f"ID={msg_id} Role={role} Content Snippet={repr(content[:120])}")

print(f"\nTotal messages: {len(rows)} | Corrupted/Object messages: {corrupted_count}")
conn.close()
