"""
Test suite for IntentService and ValidationService.
"""
import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.intent_service import IntentService, ResponseMode
from app.services.validation_service import ValidationService


def test_intent_classification():
    print("► Testing IntentService classification...")

    # 1. Debug Mode
    res1 = IntentService.classify_intent("Traceback (most recent call last):\n  File 'app.py', line 10, in <module>\nValueError: invalid literal")
    assert res1["mode"] == ResponseMode.DEBUG
    print("  ✓ Debug intent classification passed")

    # 2. Architect Mode
    res2 = IntentService.classify_intent("Create a system design and ER diagram for microservices banking platform")
    assert res2["mode"] == ResponseMode.ARCHITECT
    print("  ✓ Architect intent classification passed")

    # 3. Artifact Project Mode (Testing required prompts)
    required_prompts = [
        "Build an ecommerce website",
        "Create a Netflix clone",
        "Build a hospital management system",
        "Develop a React admin dashboard",
        "Create a portfolio website",
        "Create a full stack portfolio website in React and FastAPI"
    ]
    for prompt in required_prompts:
        r = IntentService.classify_intent(prompt)
        assert r["mode"] == ResponseMode.ARTIFACT_PROJECT, f"Failed for prompt: {prompt}"
        print(f"  ✓ ARTIFACT_PROJECT intent passed for prompt: '{prompt}' (Confidence: {r['confidence']})")

    # 4. Small Code Mode
    res4 = IntentService.classify_intent("Write bubble sort in Python")
    assert res4["mode"] == ResponseMode.SMALL_CODE
    print("  ✓ Small Code intent classification passed")

    # 5. Conversational Mode
    res5 = IntentService.classify_intent("What is the difference between REST and GraphQL?")
    assert res5["mode"] == ResponseMode.CONVERSATIONAL
    print("  ✓ Conversational intent classification passed")

    print("ALL INTENT CLASSIFICATION TESTS PASSED CLEANLY!\n")


def test_validation_service():
    print("► Testing ValidationService...")

    # Python AST check
    v1 = ValidationService.validate_and_sanitize("def hello():\n    print('Hello World')", "python")
    assert v1.is_valid
    print("  ✓ Python valid syntax passed")

    v2 = ValidationService.validate_and_sanitize("def hello():\n    print('Hello World'", "python")
    assert not v2.is_valid
    print("  ✓ Python syntax error detection passed")

    # [object Object] sanitization
    v3 = ValidationService.validate_and_sanitize("const x = [object Object];", "javascript")
    assert "[object Object]" not in v3.sanitized_code
    print("  ✓ [object Object] sanitization passed")

    # Markdown block extraction
    content = "### src/App.tsx\n```tsx\nexport function App() { return <div>App</div>; }\n```"
    extracted = ValidationService.extract_file_blocks(content)
    assert len(extracted) == 1
    assert extracted[0]["path"] == "src/App.tsx"
    assert extracted[0]["language"] == "tsx"
    print("  ✓ Markdown file block extraction passed")

    print("ALL VALIDATION SERVICE TESTS PASSED CLEANLY!\n")


if __name__ == "__main__":
    test_intent_classification()
    test_validation_service()
