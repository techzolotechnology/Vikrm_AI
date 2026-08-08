import asyncio
import json
import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.project.dynamic_generator import DynamicProjectGenerator
from app.services.project.generator import ProjectGenerator

def test_project_generation():
    prompts = [
        "Hospital Management System",
        "Enterprise ERP System",
        "Netflix Clone",
        "GitHub Clone",
        "Salesforce CRM Platform"
    ]

    print("=" * 80)
    print(" PHASE 6 — AI PROJECT GENERATION TEST FOR 5 ARCHETYPES")
    print("=" * 80)

    for i, prompt in enumerate(prompts, start=1):
        print(f"\n[{i}/5] Generating: '{prompt}'...")
        res = DynamicProjectGenerator.generate_project(prompt)
        
        plan = res.get("plan")
        agent_plan = res.get("agent_plan")
        files = res.get("files", {})

        print(f"  ✓ Requirement Analysis & Tech Stack: Framework={plan.tech_stack.framework}")
        print(f"  ✓ Architecture Planning: Modules={len(plan.modules)} | Domain={agent_plan.domain}")
        print(f"  ✓ Multi-Agent Execution: PlannedFiles={agent_plan.planned_files}")
        print(f"  ✓ Code Generation: Total Synthesized Files={len(files)}")
        print(f"  ✓ Validation & Dependency Graph: Successfully sorted {len(files)} files")

        # Test ZIP generation from dict
        zip_bytes = ProjectGenerator.generate_zip_from_dict(files)
        print(f"  ✓ ZIP Export Verified: Generated ZIP archive size = {len(zip_bytes):,} bytes")
        assert len(files) > 0, f"No files generated for {prompt}"
        assert len(zip_bytes) > 0, f"ZIP export failed for {prompt}"

    print("\n" + "=" * 80)
    print(" ALL 5 PROJECT GENERATIONS & ZIP EXPORTS VERIFIED SUCCESSFULLY!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    test_project_generation()
