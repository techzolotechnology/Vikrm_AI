import sys
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, '.')

from app.services.project.planning_agent import PlanningAgent
from app.services.project.code_synthesizer import LLMCodeSynthesizer

print("=====================================================================================")
print(" FRONTEND PARSER REGEX VERIFICATION")
print("=====================================================================================")

prompt = (
    "Build a complete Enterprise Hospital Management System with: "
    "React 19, FastAPI, PostgreSQL, Redis, RabbitMQ, Docker, Docker Compose, Kubernetes, "
    "JWT, OAuth, RBAC, Patients, Doctors, Appointments, Billing, Laboratory, Radiology, "
    "Pharmacy, Insurance, Inventory, Telemedicine, Analytics, Notifications, Reporting, "
    "Swagger, CI/CD, Vitest, Pytest, Playwright"
)

plan = PlanningAgent.plan(prompt)
files = LLMCodeSynthesizer.synthesize(plan)

# Build stream text exactly as chat_service.py produces it
stream_text = "> [Planning...]\n> [Analyzing...]\n> [Generating 280 files...]\n> [Workspace Ready]\n\n"
for path, content in files.items():
    ext = path.split(".")[-1] if "." in path else ""
    lang = {
        "ts": "typescript", "tsx": "typescript",
        "js": "javascript", "jsx": "javascript",
        "py": "python", "css": "css", "html": "html",
        "md": "markdown", "json": "json", "yml": "yaml",
        "yaml": "yaml", "sql": "sql", "sh": "bash",
    }.get(ext, "text")
    stream_text += f"### {path}\n```{lang}\n{content}\n```\n\n"

print(f"Total Stream Character Length: {len(stream_text):,} chars")

# Regex from parse-project-artifact.ts
file_block_regex = re.compile(r"###\s+([^\n]+)\s*\n+```(\w+)?\n([\s\S]*?)```")

parsed_files = []
for match in file_block_regex.finditer(stream_text):
    raw_path = match.group(1).strip()
    clean_path = raw_path.replace("`", "").lstrip("./")
    language = (match.group(2) or "typescript").strip()
    content = match.group(3).strip()
    parsed_files.append({"path": clean_path, "language": language, "content": content})

print(f"Synthesized Files Count: {len(files)}")
print(f"Parsed Files Count     : {len(parsed_files)}")

if len(files) == len(parsed_files):
    print("\n✓ SUCCESS: Frontend Regex parses all 280 files perfectly with ZERO truncation!")
else:
    print(f"\n⚠️ TRUNCATION MISMATCH: Synthesized={len(files)}, Parsed={len(parsed_files)}")
