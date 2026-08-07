import asyncio
import json
import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.llm.base import normalize_content_chunk


def test_normalize_content_chunk():
    print("► Testing normalize_content_chunk()...")

    # 1. Plain string test
    assert normalize_content_chunk("Hello World") == "Hello World"
    print("  ✓ Plain string test passed")

    # 2. Literal '[object Object]' filtering
    assert normalize_content_chunk("[object Object]") == ""
    print("  ✓ Literal '[object Object]' test passed")

    # 3. Structured files payload
    files_payload = {
        "files": [
            {"path": "src/App.tsx", "content": 'export function App() { return <h1>Hello</h1>; }'},
            {"path": "src/index.css", "content": "body { margin: 0; }"},
        ]
    }
    normalized_files = normalize_content_chunk(files_payload)
    assert "### src/App.tsx" in normalized_files
    assert "```tsx\nexport function App()" in normalized_files
    assert "### src/index.css" in normalized_files
    assert "[object Object]" not in normalized_files
    print("  ✓ Structured files payload test passed")

    # 4. JSON string containing files
    json_files_str = json.dumps(files_payload)
    normalized_json_str = normalize_content_chunk(json_files_str)
    assert "### src/App.tsx" in normalized_json_str
    assert "```tsx" in normalized_json_str
    print("  ✓ JSON string containing files test passed")

    # 5. Dict with text/content key
    dict_payload = {"content": "This is stream content"}
    assert normalize_content_chunk(dict_payload) == "This is stream content"
    print("  ✓ Dict with content key test passed")

    # 6. Generic nested dict fallback
    generic_dict = {"status": "ok", "count": 5}
    generic_norm = normalize_content_chunk(generic_dict)
    assert "```json" in generic_norm
    assert '"status": "ok"' in generic_norm
    print("  ✓ Generic dict fallback test passed")

    print("\nALL BACKEND NORMALIZATION TESTS PASSED CLEANLY! ZERO [object Object] DETECTED.\n")


if __name__ == "__main__":
    test_normalize_content_chunk()
