"""
Text chunking for RAG.

Splits on paragraph/sentence boundaries where possible rather than
cutting mid-sentence, while enforcing a maximum chunk size (in
characters — good enough without pulling in a tokenizer dependency;
`chunk_size` is set conservatively below typical embedding model
context limits). Adjacent chunks overlap so a fact spanning a chunk
boundary isn't lost to either chunk's retrieval.
"""
import re

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 150


def chunk_text(
    text: str, *, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP
) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    sentences = _split_sentences(text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            # Start the next chunk with the tail of the previous one for overlap.
            current = _tail(current, overlap) + " " + sentence
        else:
            # A single sentence longer than chunk_size: hard-split it.
            for part in _hard_split(sentence, chunk_size):
                chunks.append(part)
            current = ""

    if current.strip():
        chunks.append(current.strip())

    return chunks


def _split_sentences(text: str) -> list[str]:
    # Split on paragraph breaks first, then sentence-ending punctuation
    # within each paragraph — keeps related sentences together longer
    # than a naive global sentence split would.
    paragraphs = re.split(r"\n\s*\n", text)
    sentences: list[str] = []
    for paragraph in paragraphs:
        parts = re.split(r"(?<=[.!?])\s+", paragraph.strip())
        sentences.extend(p for p in parts if p)
    return sentences


def _tail(text: str, length: int) -> str:
    if len(text) <= length:
        return text
    return text[-length:]


def _hard_split(text: str, size: int) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]
