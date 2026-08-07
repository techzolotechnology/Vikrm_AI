import sqlite3

db = sqlite3.connect(r'd:\vikrm-final-complete\backend\data\vikrm.db')
cur = db.cursor()

# Phase 1: Check for literal [object Object]
cur.execute("SELECT COUNT(*) FROM messages WHERE content LIKE '%[object Object]%'")
obj_count = cur.fetchone()[0]
print(f"\n[PHASE 1] Messages with literal [object Object]: {obj_count}")

# Phase 2: Check for leaked JSON dict content (e.g., {"role": "assistant"...})
cur.execute("SELECT id, conversation_id, role, LENGTH(content), SUBSTR(content, 1, 200) FROM messages WHERE content LIKE '{%' ORDER BY id DESC LIMIT 20")
json_rows = cur.fetchall()
print(f"\n[PHASE 2] Messages whose content starts with '{{' (JSON-like): {len(json_rows)}")
for mid, cid, role, clen, preview in json_rows:
    print(f"  id={mid} conv={cid} role={role} len={clen} | {repr(str(preview)[:180])}")

# Phase 3: Last 50 assistant messages
cur.execute("SELECT id, conversation_id, LENGTH(content), SUBSTR(content, 1, 300) FROM messages WHERE role='assistant' ORDER BY id DESC LIMIT 50")
rows = cur.fetchall()
print(f"\n[PHASE 3] Last 50 assistant messages:")
bad_count = 0
for mid, cid, clen, preview in rows:
    preview_str = str(preview) if preview is not None else 'NULL'
    is_bad = '[object Object]' in preview_str
    is_json = preview_str.strip().startswith('{') or preview_str.strip().startswith('[')
    flag = ''
    if is_bad:
        flag = ' <<< OBJECT_OBJECT'
        bad_count += 1
    elif is_json:
        flag = ' <<< JSON_LEAKED'
        bad_count += 1
    print(f"  id={mid} conv={cid} len={clen}{flag}")
    if flag:
        print(f"    CONTENT: {repr(preview_str[:250])}")

print(f"\n[SUMMARY] Bad messages found: {bad_count}")
db.close()
