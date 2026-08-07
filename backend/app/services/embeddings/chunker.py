"""
Chunker: Code-aware and Markdown-aware document chunker for RAG indexing.
"""
import re
from typing import Any, Dict, List


class DocumentChunker:
    def __init__(self, max_chunk_size: int = 800, overlap: int = 150) -> None:
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def chunk_document(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunks text into semantic chunks with associated metadata.
        Returns list of dicts with 'text' and 'metadata'.
        """
        if not text or not text.strip():
            return []

        doc_type = metadata.get("type", "code")
        if doc_type == "markdown" or metadata.get("path", "").endswith((".md", ".rst")):
            raw_chunks = self._chunk_markdown(text)
        elif doc_type == "code" or metadata.get("language") in ["python", "javascript", "typescript", "java", "cpp", "csharp"]:
            raw_chunks = self._chunk_code(text)
        else:
            raw_chunks = self._chunk_text_sliding_window(text)

        chunks = []
        for i, chunk_text in enumerate(raw_chunks):
            if not chunk_text.strip():
                continue
            chunk_meta = dict(metadata)
            chunk_meta["chunk_index"] = i
            chunk_meta["total_chunks"] = len(raw_chunks)
            chunk_meta["char_length"] = len(chunk_text)
            chunks.append({
                "text": chunk_text.strip(),
                "metadata": chunk_meta,
            })
        return chunks

    def _chunk_markdown(self, text: str) -> List[str]:
        # Split by headers (H1, H2, H3)
        sections = re.split(r"\n(?=#{1,3}\s)", text)
        chunks = []
        current = ""

        for sec in sections:
            if len(current) + len(sec) <= self.max_chunk_size:
                current += ("\n\n" if current else "") + sec
            else:
                if current:
                    chunks.append(current)
                if len(sec) > self.max_chunk_size:
                    chunks.extend(self._chunk_text_sliding_window(sec))
                    current = ""
                else:
                    current = sec

        if current:
            chunks.append(current)
        return chunks

    def _chunk_code(self, text: str) -> List[str]:
        # Split by class / function definitions
        blocks = re.split(r"\n(?=(?:class|def|function|async function|export|public class|interface|type)\s)", text)
        chunks = []
        current = ""

        for block in blocks:
            if len(current) + len(block) <= self.max_chunk_size:
                current += ("\n\n" if current else "") + block
            else:
                if current:
                    chunks.append(current)
                if len(block) > self.max_chunk_size:
                    chunks.extend(self._chunk_text_sliding_window(block))
                    current = ""
                else:
                    current = block

        if current:
            chunks.append(current)
        return chunks

    def _chunk_text_sliding_window(self, text: str) -> List[str]:
        lines = text.splitlines()
        chunks = []
        current_lines: List[str] = []
        current_size = 0

        for line in lines:
            if current_size + len(line) > self.max_chunk_size and current_lines:
                chunks.append("\n".join(current_lines))
                # keep overlap lines
                overlap_lines = []
                overlap_len = 0
                for l in reversed(current_lines):
                    if overlap_len + len(l) <= self.overlap:
                        overlap_lines.insert(0, l)
                        overlap_len += len(l)
                    else:
                        break
                current_lines = overlap_lines
                current_size = overlap_len

            current_lines.append(line)
            current_size += len(line)

        if current_lines:
            chunks.append("\n".join(current_lines))
        return chunks
