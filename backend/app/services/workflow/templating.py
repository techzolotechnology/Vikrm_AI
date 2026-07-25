"""
Workflow template resolution.

Node config fields (e.g. an LLM node's prompt) can reference upstream
values with `{{input}}` (the workflow's initial input) or
`{{node_id.output}}` (another node's output). Resolution is plain
regex substitution against a context dict — never `eval`/`format`-style
code execution — so a malicious or malformed template can only ever
produce missing/garbled text, never run arbitrary code.
"""
import re

_REF_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_\.]+)\s*\}\}")


def resolve_template(template: str, *, initial_input: str, node_outputs: dict[str, str]) -> str:
    def replace(match: re.Match) -> str:
        raw_ref = match.group(1).strip()
        # Strip trailing .output if present
        ref = raw_ref[:-7] if raw_ref.endswith(".output") else raw_ref

        if ref in ("input", "start"):
            return initial_input
        if ref == "previous":
            if node_outputs:
                # Return the output of the most recently added node
                return list(node_outputs.values())[-1]
            return initial_input
        if ref in node_outputs:
            return node_outputs[ref]
        return node_outputs.get(raw_ref, f"{{{{missing:{raw_ref}}}}}")

    return _REF_PATTERN.sub(replace, template)

