"""
Project Score Evaluator for Vikrm AI Platform — Quality Metrics Report.

Phase 1 Status: Metrics marked with is_estimated=True. Real measurement objects land in Phase 4.
"""

from typing import Dict
from pydantic import BaseModel


class ProjectScoreReport(BaseModel):
    is_estimated: bool = True
    evaluation_status: str = "estimated (real sandbox profiling pending Phase 4)"
    build_status: str = "SIMULATED"
    runtime_status: str = "NOT_YET_TESTED"
    generation_score: int = 100
    compilation_score: int = 100
    runtime_score: int = 100
    architecture_score: int = 95
    security_score: int = 90
    performance_score: int = 90
    accessibility_score: int = 90
    maintainability_score: int = 90
    test_coverage: str = "estimated (pending Phase 4 sandbox runner)"
    bundle_size: str = "estimated (pending Phase 4 build output)"
    overall_score: int = 92

    def format_summary(self) -> str:
        return (
            "### 📊 Professional AI IDE — Quality Metrics Report\n"
            f"> [!NOTE]\n"
            f"> Status: `{self.evaluation_status}`\n\n"
            f"- **Overall Estimated Score**: `{self.overall_score}/100` (Estimated)\n"
            f"- **Build Status**: `{self.build_status}` | **Runtime Status**: `{self.runtime_status}`\n"
            f"- **Generation Score**: `{self.generation_score}/100` | **Compilation Score**: `{self.compilation_score}/100`\n"
            f"- **Security Score**: `{self.security_score}/100` | **Performance Score**: `{self.performance_score}/100`\n"
            f"- **Test Coverage**: `{self.test_coverage}` | **Bundle Size**: `{self.bundle_size}`\n"
        )


class ScoreEvaluator:
    @classmethod
    def evaluate(cls, files: Dict[str, str], build_success: bool, repair_attempts: int) -> ProjectScoreReport:
        compilation = 95 if build_success else 60
        compilation = max(50, compilation - (repair_attempts * 5))

        has_pkg = "package.json" in files
        has_app = any("App." in k for k in files)
        has_server = any("main.py" in k or "server" in k for k in files)
        has_docker = "Dockerfile" in files or "docker-compose.yml" in files

        gen_score = 95 if (has_pkg and has_app) else 75
        arch_score = 95 if (has_server and has_docker) else 85
        sec_score = 92 if any("Auth" in k for k in files) else 85

        overall = int((gen_score + compilation + arch_score + sec_score + 90 + 90 + 90) / 7.0)

        return ProjectScoreReport(
            is_estimated=True,
            evaluation_status="estimated (real sandbox profiling pending Phase 4)",
            build_status="SIMULATED" if build_success else "FAILED",
            runtime_status="NOT_YET_TESTED",
            generation_score=gen_score,
            compilation_score=compilation,
            runtime_score=90 if build_success else 60,
            architecture_score=arch_score,
            security_score=sec_score,
            performance_score=90,
            accessibility_score=90,
            maintainability_score=90,
            test_coverage="estimated (pending Phase 4 sandbox runner)",
            bundle_size="estimated (pending Phase 4 build output)",
            overall_score=overall,
        )
