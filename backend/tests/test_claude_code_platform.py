"""
Comprehensive Test Suite for Claude Code-Level Autonomous Platform Capabilities:
- Dynamic Project Architecture Planning & Synthesis
- Incremental Workspace Editing
- Pre-Flight Multi-File Validation & Automated Self-Repair Loop
- Project Export & ZIP Package Generation
"""

import pytest
import asyncio
from app.services.project.planning_agent import PlanningAgent
from app.services.project.architecture_planner import ArchitecturePlanner
from app.services.project.dynamic_generator import DynamicProjectGenerator
from app.services.project.incremental_edit_engine import IncrementalEditEngine, WorkspaceContext
from app.services.project.generator import ProjectGenerator
from app.services.validation_service import ValidationService, ValidationResult


def test_dynamic_architecture_planning():
    """Verify dynamic architecture inference from user requirement prompt."""
    prompt = "Build a real-time hospital management system with patient records and doctor schedules"
    plan = ArchitecturePlanner.infer_and_plan(prompt)
    
    assert plan.domain == "healthcare"
    assert "FastAPI" in plan.tech_stack.framework or "React" in plan.tech_stack.framework
    assert plan.planned_files > 0
    assert len(plan.modules) > 0


def test_dynamic_project_generator_structure():
    """Verify dynamic generator produces sorted files without static stubs."""
    prompt = "Build an e-commerce platform with stripe checkout and inventory dashboard"
    res = DynamicProjectGenerator.generate_project(prompt)
    
    assert "plan" in res
    assert "agent_plan" in res
    assert "files" in res
    
    files = res["files"]
    assert "package.json" in files
    assert "src/App.tsx" in files
    assert "src/index.css" in files


def test_incremental_edit_engine_targeted_patching():
    """Verify incremental edit engine modifies only affected target files."""
    initial_files = {
        "package.json": '{\n  "name": "app",\n  "dependencies": {}\n}',
        "src/App.tsx": "export function App() { return <div>App</div>; }",
        "README.md": "# App Documentation"
    }
    
    ctx = WorkspaceContext()
    ctx.load_from_files(initial_files)
    
    delta, changed_paths = IncrementalEditEngine.apply_edit(ctx, "Add Stripe payment integration")
    
    assert len(changed_paths) > 0
    assert "package.json" in changed_paths
    assert "package.json" in delta
    # Ensure unchanged files are preserved in workspace context
    assert "src/App.tsx" in ctx.files


def test_validation_service_import_resolution_and_repair():
    """Verify multi-file import resolution and self-repair capabilities."""
    valid_files = {
        "src/utils.ts": "export function add(a: number, b: number): number { return a + b; }",
        "src/main.ts": "import { add } from './utils';\nconsole.log(add(1, 2));",
        "package.json": '{\n  "name": "test-pkg",\n  "dependencies": {}\n}'
    }
    
    results = ValidationService.validate_file_map(valid_files)
    for path, res in results.items():
        assert res.is_valid, f"File {path} failed validation: {res.issues}"

    # Test auto self-repair on minor syntax errors (e.g. unclosed braces)
    flawed_files = {
        "src/broken.ts": "export function broken() { console.log('hello'); // TODO: fix"
    }
    
    loop = asyncio.get_event_loop()
    repaired = loop.run_until_complete(ValidationService.self_repair_loop(flawed_files, max_attempts=2))
    
    assert "src/broken.ts" in repaired
    assert "// TODO:" not in repaired["src/broken.ts"]


def test_zip_archive_generation():
    """Verify in-memory ZIP archive generation for export."""
    files = {
        "README.md": "# Test Project",
        "src/main.ts": "console.log('test');"
    }
    
    zip_bytes = ProjectGenerator.generate_zip_from_dict(files)
    assert zip_bytes is not None
    assert len(zip_bytes) > 0
    assert zip_bytes.startswith(b"PK")  # Standard ZIP file magic number bytes
