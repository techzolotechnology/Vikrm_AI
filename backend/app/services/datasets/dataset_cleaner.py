"""
Dataset Cleaner: Normalizes, deduplicates, and cleans raw Hugging Face code records.
Filter out binary blobs, invalid UTF-8, empty files, and duplicate code snippets.
"""
import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple


class DatasetCleaner:
    def __init__(self) -> None:
        self._seen_hashes: set[str] = set()

    def reset_dedup_cache(self) -> None:
        self._seen_hashes.clear()

    @staticmethod
    def is_valid_text(content: str) -> bool:
        if not content or not isinstance(content, str):
            return False
        # Remove null bytes / binary characters check
        if "\x00" in content:
            return False
        # Check printable ratio
        printable_count = sum(1 for c in content if c.isprintable() or c in "\n\r\t")
        if len(content) > 0 and (printable_count / len(content)) < 0.85:
            return False
        return True

    @staticmethod
    def compute_code_hash(code: str) -> str:
        # Normalize whitespace before hashing for robust deduplication
        normalized = re.sub(r"\s+", " ", code).strip()
        return hashlib.sha256(normalized.encode("utf-8", errors="ignore")).hexdigest()

    def clean_record(
        self,
        raw_record: Dict[str, Any],
        dataset_name: str,
        default_lang: str = "text",
        default_framework: str = "general",
    ) -> Optional[Dict[str, Any]]:
        """
        Cleans and normalizes a single raw record into the Vikrm standard dataset schema.
        Schema:
          - language (str)
          - framework (str)
          - title (str)
          - description (str)
          - code (str)
          - path (str)
          - tags (list[str])
          - difficulty (str: beginner, intermediate, advanced)
        """
        # Extract code field from potential HF field names
        code = (
            raw_record.get("code")
            or raw_record.get("content")
            or raw_record.get("func_code_string")
            or raw_record.get("canonical_solution")
            or raw_record.get("solution")
            or raw_record.get("output")
            or raw_record.get("prompt")
            or raw_record.get("text")
            or ""
        )

        if not isinstance(code, str) or not code.strip():
            return None

        # Check UTF-8 validity & non-binary
        if not self.is_valid_text(code):
            return None

        code_clean = code.strip()
        if len(code_clean) < 10:  # Skip trivially tiny/empty snippets
            return None

        # Deduplication
        chash = self.compute_code_hash(code_clean)
        if chash in self._seen_hashes:
            return None
        self._seen_hashes.add(chash)

        # Extract title and description
        title = (
            raw_record.get("title")
            or raw_record.get("func_name")
            or raw_record.get("task_id")
            or raw_record.get("instruction")
            or raw_record.get("summary")
            or raw_record.get("problem_id")
            or f"{dataset_name}_example"
        )
        if not isinstance(title, str):
            title = str(title)

        description = (
            raw_record.get("description")
            or raw_record.get("docstring")
            or raw_record.get("instruction")
            or raw_record.get("output")
            or raw_record.get("question")
            or raw_record.get("summary")
            or ""
        )
        if not isinstance(description, str):
            description = str(description)

        language = (
            raw_record.get("language")
            or raw_record.get("lang")
            or default_lang
        )
        if not isinstance(language, str):
            language = default_lang

        framework = (
            raw_record.get("framework")
            or raw_record.get("repo")
            or default_framework
        )
        if not isinstance(framework, str):
            framework = default_framework

        path = raw_record.get("path") or raw_record.get("file_path") or f"{language}/{title}.txt"
        if not isinstance(path, str):
            path = f"{language}/sample.txt"

        tags = raw_record.get("tags") or [dataset_name, language.lower(), framework.lower()]
        if not isinstance(tags, list):
            tags = [str(tags)]

        difficulty = raw_record.get("difficulty") or "intermediate"
        if difficulty not in ["beginner", "intermediate", "advanced"]:
            difficulty = "intermediate"

        return {
            "language": language.lower(),
            "framework": framework.lower(),
            "title": title[:200],
            "description": description[:1000],
            "code": code_clean,
            "path": path,
            "tags": tags,
            "difficulty": difficulty,
        }

    def clean_batch(
        self,
        records: List[Dict[str, Any]],
        dataset_name: str,
        default_lang: str = "text",
        default_framework: str = "general",
    ) -> List[Dict[str, Any]]:
        cleaned = []
        for r in records:
            item = self.clean_record(
                raw_record=r,
                dataset_name=dataset_name,
                default_lang=default_lang,
                default_framework=default_framework,
            )
            if item:
                cleaned.append(item)
        return cleaned
