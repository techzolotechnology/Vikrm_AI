import sys
import os
import time
import json
import tracemalloc

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, '.')

from app.services.intent_service import IntentService, ResponseMode
from app.services.project.planning_agent import PlanningAgent
from app.services.project.architecture_planner import ArchitecturePlanner
from app.services.project.dependency_graph import DependencyGraphResolver
from app.services.project.code_synthesizer import LLMCodeSynthesizer
from app.services.project.incremental_edit_engine import WorkspaceContext
from app.services.chat_service import get_knowledge_retriever

print("=====================================================================================")
print(" VIKRM AI PLATFORM -- 18-STAGE PIPELINE FORENSIC TRACE")
print("=====================================================================================")

tracemalloc.start()
prompt = "Build a complete Enterprise Hospital Management System"

print(f"\nTracing prompt: '{prompt}'\n")

# 1. IntentService
t0 = time.perf_counter()
intent = IntentService.classify_intent(prompt, has_active_workspace=True)
t1 = time.perf_counter()
print(f"Stage 1  [IntentService]       : OutputMode={intent['mode']}, Conf={intent['confidence']} (Time: {(t1-t0)*1000:.2f} ms)")

# 2. PlanningAgent
t0 = time.perf_counter()
plan = PlanningAgent.plan(prompt)
t1 = time.perf_counter()
print(f"Stage 2  [PlanningAgent]       : PlannedFiles={plan.planned_files}, Tasks={len(plan.tasks)}, Tier={plan.complexity} (Time: {(t1-t0)*1000:.2f} ms)")

# 3. ArchitecturePlanner
t0 = time.perf_counter()
arch = ArchitecturePlanner.infer_and_plan(prompt)
t1 = time.perf_counter()
print(f"Stage 3  [ArchitecturePlanner] : Framework='{arch.tech_stack.framework}', Modules={len(arch.modules)} (Time: {(t1-t0)*1000:.2f} ms)")

# 4. DependencyGraphResolver
t0 = time.perf_counter()
synth_raw = LLMCodeSynthesizer.synthesize(plan)
sorted_files = DependencyGraphResolver.sort_files(synth_raw)
t1 = time.perf_counter()
print(f"Stage 4  [DependencyGraph]      : SortedFiles={len(sorted_files)} (Time: {(t1-t0)*1000:.2f} ms)")

# 5. Knowledge Retrieval
t0 = time.perf_counter()
retriever = get_knowledge_retriever()
chunks = retriever.retrieve_context(prompt, top_k=3)
t1 = time.perf_counter()
print(f"Stage 5  [Knowledge Retrieval] : ChunksRetrieved={len(chunks)} (Time: {(t1-t0)*1000:.2f} ms)")

# 6. CodeSynthesizer
t0 = time.perf_counter()
synthesized = LLMCodeSynthesizer.synthesize(plan)
t1 = time.perf_counter()
print(f"Stage 6  [CodeSynthesizer]     : SynthesizedFiles={len(synthesized)} (Time: {(t1-t0)*1000:.2f} ms)")

# 7. WorkspaceBuilder / Context
t0 = time.perf_counter()
ctx = WorkspaceContext(project_name=plan.project_name, domain=plan.domain)
ctx.load_from_files(synthesized)
t1 = time.perf_counter()
print(f"Stage 7  [WorkspaceBuilder]    : SavedContextFiles={len(ctx.files)} (Time: {(t1-t0)*1000:.2f} ms)")

# 8. API Serialization Model
t0 = time.perf_counter()
api_files = [
    {"id": idx + 1, "path": p, "content": c, "language": "typescript"}
    for idx, (p, c) in enumerate(sorted_files.items())
]
t1 = time.perf_counter()
print(f"Stage 8  [API Serialization]   : SerializedFiles={len(api_files)} (Time: {(t1-t0)*1000:.2f} ms)")

# 9. SSE Streaming Text Simulation
t0 = time.perf_counter()
stream_text = ""
for path, content in sorted_files.items():
    stream_text += f"### {path}\n```typescript\n{content}\n```\n\n"
t1 = time.perf_counter()
print(f"Stage 9  [SSE Stream Output]   : StreamedBytes={len(stream_text):,} chars for {len(sorted_files)} files (Time: {(t1-t0)*1000:.2f} ms)")

# 10. Frontend Parser Regex Match
t0 = time.perf_counter()
import re
file_block_regex = re.compile(r"###\s+([^\n]+)\s*\n+```(\w+)?\n([\s\S]*?)```")
parsed_files = [m.group(1).strip() for m in file_block_regex.finditer(stream_text)]
t1 = time.perf_counter()
print(f"Stage 10 [Frontend Parser]      : ParsedFiles={len(parsed_files)} (Time: {(t1-t0)*1000:.2f} ms)")

# 11. React File Explorer Tree Build
t0 = time.perf_counter()
def build_tree(paths):
    tree = []
    for p in paths:
        parts = p.split("/")
        curr = tree
        for idx, part in enumerate(parts):
            is_last = idx == len(parts) - 1
            node = next((n for n in curr if n["name"] == part), None)
            if not node:
                node = {"name": part, "isFolder": not is_last, "children": [] if not is_last else None}
                curr.append(node)
            if not is_last:
                curr = node["children"]
    return tree

tree = build_tree(parsed_files)
t1 = time.perf_counter()
print(f"Stage 11 [React File Explorer]  : ExplorerNodesCount={len(parsed_files)} (Time: {(t1-t0)*1000:.2f} ms)")

current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"\nPeak Memory Usage: {peak / 1024 / 1024:.2f} MB")

print("\n=====================================================================================")
print(" PIPELINE FORENSIC SUMMARY")
print("=====================================================================================")
print(f"  PlannedFiles    : {plan.planned_files}")
print(f"  SynthesizedFiles: {len(synthesized)}")
print(f"  SavedContext    : {len(ctx.files)}")
print(f"  SerializedFiles : {len(api_files)}")
print(f"  ParsedFiles     : {len(parsed_files)}")
print(f"  ExplorerFiles   : {len(parsed_files)}")
print("=====================================================================================")
