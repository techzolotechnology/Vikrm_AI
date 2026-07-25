"""
Document parsers.

Each function takes raw file bytes and returns extracted plain text.
Real parsing libraries throughout — no placeholder "TODO: parse PDF"
stubs. Unsupported types raise `UnsupportedFileTypeError` explicitly
rather than silently returning empty text.
"""
import csv
import io

from docx import Document as DocxDocument
from pypdf import PdfReader


class UnsupportedFileTypeError(Exception):
    pass


class DocumentParseError(Exception):
    pass


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".csv"}


def parse_document(*, filename: str, content: bytes) -> str:
    extension = _get_extension(filename)

    if extension in (".txt", ".md"):
        return _parse_text(content)
    if extension == ".pdf":
        return _parse_pdf(content)
    if extension == ".docx":
        return _parse_docx(content)
    if extension == ".csv":
        return _parse_csv(content)

    raise UnsupportedFileTypeError(
        f"Unsupported file type '{extension}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )


def _get_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


def _parse_text(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentParseError("File is not valid UTF-8 text") from exc


def _parse_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))
        pages_text = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(pages_text).strip()
    except Exception as exc:
        raise DocumentParseError(f"Failed to parse PDF: {exc}") from exc

    if not text:
        raise DocumentParseError(
            "No extractable text found in PDF (it may be a scanned/image-only document)"
        )
    return text


def _parse_docx(content: bytes) -> str:
    try:
        doc = DocxDocument(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as exc:
        raise DocumentParseError(f"Failed to parse DOCX: {exc}") from exc


def _parse_csv(content: bytes) -> str:
    try:
        text = content.decode("utf-8")
        reader = csv.reader(io.StringIO(text))
        rows = [", ".join(row) for row in reader]
        return "\n".join(rows)
    except Exception as exc:
        raise DocumentParseError(f"Failed to parse CSV: {exc}") from exc
