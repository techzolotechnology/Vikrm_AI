import sys
sys.path.insert(0, '.')

from app.services.project.planning_agent import PlanningAgent
from app.services.project.code_synthesizer import LLMCodeSynthesizer
from app.services.project.agent_loop import AgentLoop, ProductionValidator, ProjectMetrics
from app.services.project.score_evaluator import ScoreEvaluator

test_cases = [
    ("Portfolio Website", "Build a developer portfolio website"),
    ("Blog CMS", "Build a blog CMS platform"),
    ("Ecommerce Store", "Build an ecommerce store with Stripe"),
    ("Hospital Management", "Build a hospital management system"),
    ("Enterprise ERP", "Build an enterprise resource planning ERP system"),
    ("Enterprise SaaS", "Build an enterprise SaaS platform with multi-tenancy"),
]

all_passed = True
print("=====================================================================================")
print(" VIKRM AI PLATFORM — UNLIMITED MULTI-FILE GENERATION VERIFICATION")
print("=====================================================================================")

for tier_label, prompt in test_cases:
    plan = PlanningAgent.plan(prompt)
    files = LLMCodeSynthesizer.synthesize(plan)
    passed, issues = ProductionValidator.validate(files)
    metrics = ProjectMetrics()
    metrics.compute(plan, files, passed, 0)
    score = ScoreEvaluator.evaluate(files, passed, 0)
    status = 'PASS' if passed else 'WARN(' + str(len(issues)) + ')'
    
    print(f"[{tier_label}] Complexity={plan.complexity} | Planned={plan.planned_files} | Generated={len(files)} | Status={status} | Score={score.overall_score}/100")
    print(f"  • Components: {metrics.components} | Pages: {metrics.pages} | Hooks: {metrics.hooks} | API Files: {metrics.api_files} | Server Files: {metrics.server_files}")
    if not passed:
        for issue in issues[:3]:
            print('  ! ' + issue)
        all_passed = False

print("\n=====================================================================================")
print('ALL UNLIMITED MULTI-FILE SUITES PASSED VERIFICATION' if all_passed else 'COMPLETE WITH WARNINGS')
print("=====================================================================================")
