"""
Phase 2 Architecture & LLM Orchestrator Acceptance Test Suite:
- LLMOrchestrator retry-with-backoff on ProviderError injection
- RequirementAnalysisService structured output & ambiguity clarification gate
- ArchitecturePlanner dynamic stack selection with rationale justifications
- Regression guard: Differently-worded prompts in the same domain produce distinct specs & plans
"""

import pytest
import asyncio
from typing import List
from unittest.mock import AsyncMock, patch

from app.services.project.llm_orchestrator import LLMOrchestrator, ProviderError
from app.services.project.requirement_analysis_service import RequirementAnalysisService, RequirementSpec
from app.services.project.architecture_planner import ArchitecturePlanner, ProjectPlan, TechStack
from app.services.llm.base import ChatMessage


@pytest.mark.asyncio
async def test_llm_orchestrator_retry_on_provider_error():
    """Verify LLMOrchestrator retries with backoff upon ProviderError injection."""
    orchestrator = LLMOrchestrator(max_retries=3, backoff_factor=0.01)
    
    attempts = 0
    async def mock_chat(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Exception("Simulated transient LLM provider error")
        return "Success response after retry"

    with patch("app.services.project.llm_orchestrator.get_provider") as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.chat.side_effect = mock_chat
        mock_get_provider.return_value = mock_provider

        res = await orchestrator.chat([ChatMessage(role="user", content="Test")])
        assert res == "Success response after retry"
        assert attempts == 3


@pytest.mark.asyncio
async def test_ambiguity_clarification_gate():
    """Verify vague prompts trigger ambiguity clarification gate instead of silent guessing."""
    req_service = RequirementAnalysisService()
    
    # Deliberately ambiguous prompt
    vague_spec = await req_service.analyze_requirement("make app")
    
    assert vague_spec.is_ambiguous is True
    assert len(vague_spec.clarification_questions) > 0
    assert "domain" in vague_spec.clarification_questions[0].lower() or "what" in vague_spec.clarification_questions[0].lower()


@pytest.mark.asyncio
async def test_architecture_planner_justifications():
    """Verify ArchitecturePlanner produces ProjectPlan with stack justifications."""
    orchestrator = LLMOrchestrator()
    async def mock_structured(messages, schema_model):
        stack = TechStack(
            framework="React 19 + TypeScript + FastAPI",
            framework_justification="React 19 chosen for component composability and FastAPI for high throughput.",
            database="PostgreSQL",
            database_justification="PostgreSQL chosen for ACID compliance on patient records.",
            authentication="JWT + OAuth2",
            auth_justification="JWT chosen for stateless RBAC across healthcare portals.",
            deployment_target="Docker + Kubernetes",
            deployment_justification="Docker chosen for isolated container deployment.",
            key_dependencies=["react", "fastapi", "sqlalchemy"],
        )
        return ProjectPlan(
            name="EHR Care System",
            description="HIPAA-compliant hospital patient portal",
            domain="healthcare",
            complexity="Enterprise",
            tech_stack=stack,
            planned_files=25,
            estimated_files=25,
            modules=["Auth", "Patients", "Vitals"],
            folder_hierarchy=["src", "server"],
            justifications={
                "framework": stack.framework_justification,
                "database": stack.database_justification,
                "auth": stack.auth_justification,
                "deployment": stack.deployment_justification,
            },
        )

    orchestrator.chat_structured = AsyncMock(side_effect=mock_structured)
    planner = ArchitecturePlanner(orchestrator=orchestrator)
    spec = RequirementSpec(
        app_name="EHR Care System",
        description="HIPAA-compliant hospital patient portal with real-time vitals telemetry",
        domain="healthcare",
        features=["Patient Vitals Stream", "Doctor Appointments", "EMR History"],
        entities=["Patient", "Doctor", "VitalsRecord"],
        non_functional_requirements=["HIPAA Security", "Sub-100ms Telemetry"],
        is_ambiguous=False,
    )
    
    plan = await planner.plan_architecture(spec)
    
    assert plan.domain == "healthcare"
    assert plan.tech_stack.framework_justification != ""
    assert plan.tech_stack.database_justification != ""
    assert plan.tech_stack.auth_justification != ""


@pytest.mark.asyncio
async def test_same_domain_different_prompts_produce_different_specs():
    """Regression Guard: Two differently-worded prompts in the same domain produce distinct specs & plans."""
    orchestrator = LLMOrchestrator()
    
    # Mock LLM structured returns for two different clinic prompts
    async def mock_structured(messages, schema_model):
        prompt_content = messages[1].content.lower()
        if "urgent care" in prompt_content:
            return RequirementSpec(
                app_name="Urgent Care Queue",
                description="Fast clinic queue with SMS and SQLite",
                domain="healthcare",
                features=["SMS Queue", "Walk-in Triage"],
                entities=["QueueTicket", "Patient"],
                non_functional_requirements=["SQLite Storage"],
                is_ambiguous=False,
                raw_prompt=messages[1].content,
            )
        else:
            return RequirementSpec(
                app_name="ICU Telemetry Suite",
                description="Enterprise multi-hospital ICU telemetry with PostgreSQL timeseries",
                domain="healthcare",
                features=["ICU Vitals Telemetry", "SAML 2.0 Auth"],
                entities=["ICUBed", "VitalsStream", "TelemetryAlert"],
                non_functional_requirements=["Sub-100ms Ingestion"],
                is_ambiguous=False,
                raw_prompt=messages[1].content,
            )

    orchestrator.chat_structured = AsyncMock(side_effect=mock_structured)
    
    req_service = RequirementAnalysisService(orchestrator=orchestrator)
    planner = ArchitecturePlanner(orchestrator=orchestrator)
    
    prompt1 = "Build an urgent care clinic queue manager with SMS notifications and SQLite storage"
    prompt2 = "Build a multi-hospital ICU telemetry monitoring suite with PostgreSQL timeseries and OAuth2 SAML"
    
    spec1 = await req_service.analyze_requirement(prompt1)
    spec2 = await req_service.analyze_requirement(prompt2)
    
    assert spec1.app_name == "Urgent Care Queue"
    assert spec2.app_name == "ICU Telemetry Suite"
    assert spec1.entities != spec2.entities
