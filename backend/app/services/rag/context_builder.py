"""
Context Builder: Synthesizes retrieved code examples, official documentation, and project templates
into structured Markdown system context for LLM prompt augmentation.
"""
from typing import Any, Dict, List


class RAGContextBuilder:
    def __init__(self, max_context_chars: int = 12000) -> None:
        self.max_context_chars = max_context_chars

    def build_augmented_prompt(self, user_query: str, retrieval_results: Dict[str, Any]) -> str:
        """
        Combines retrieved knowledge into a rich system context prompt.
        """
        sections: List[str] = []

        # 1. Project Templates Section
        templates = retrieval_results.get("templates", [])
        if templates:
            t_blocks = []
            for t in templates:
                files_preview = []
                for fname, fcontent in t.get("files", {}).items():
                    files_preview.append(f"### {fname}\n```\n{fcontent[:500]}\n```")
                t_blocks.append(
                    f"#### Template: {t.get('title')} ({t.get('framework')})\n"
                    f"Description: {t.get('description')}\n"
                    + "\n\n".join(files_preview[:4])
                )
            sections.append(
                "## 📁 RECOMMENDED PROJECT TEMPLATES & BOILERPLATE\n" + "\n\n".join(t_blocks)
            )

        # 2. Official Documentation Section
        docs = retrieval_results.get("docs", [])
        if docs:
            doc_blocks = []
            for d in docs:
                meta = d.get("metadata", {})
                doc_blocks.append(
                    f"### [{meta.get('tech', 'Doc')}] {meta.get('title', 'Official Ref')}\n"
                    f"{d.get('document', '')[:1000]}"
                )
            sections.append(
                "## 📚 OFFICIAL TECHNICAL DOCUMENTATION & SPECIFICATIONS\n" + "\n\n".join(doc_blocks)
            )

        # 3. Relevant Dataset Code Examples
        examples = retrieval_results.get("examples", [])
        if examples:
            ex_blocks = []
            for i, ex in enumerate(examples[:6]):
                meta = ex.get("metadata", {})
                ex_blocks.append(
                    f"### Example {i+1}: {meta.get('title', 'Code Snippet')} [{meta.get('language', 'code')}]\n"
                    f"{ex.get('document', '')[:1200]}"
                )
            sections.append(
                "## 💡 HUGGING FACE DATASET CODE EXAMPLES\n" + "\n\n".join(ex_blocks)
            )

        if not sections:
            return user_query

        context_str = "\n\n".join(sections)
        if len(context_str) > self.max_context_chars:
            context_str = context_str[: self.max_context_chars] + "\n...[Context truncated for token limits]"

        system_augmented_context = (
            "================================================================================\n"
            "VIKRM RETRIEVAL-AUGMENTED CONTEXT (HUGGING FACE DATASETS + TEMPLATES + DOCS)\n"
            "Use the following retrieved project templates, documentation, and code examples\n"
            "to guide your software engineering implementation:\n"
            "================================================================================\n\n"
            f"{context_str}\n\n"
            "================================================================================\n"
            f"USER REQUEST: {user_query}\n"
            "Provide a complete, production-ready response adhering to the retrieved architecture standards."
        )

        return system_augmented_context
