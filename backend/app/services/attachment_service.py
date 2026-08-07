"""
Attachment service for uploading, validating, storing, and extracting text from documents and images.
"""
import io
import os
import uuid
from typing import BinaryIO

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment
from app.repositories.attachment_repository import AttachmentRepository

UPLOAD_DIR = os.path.join(os.getcwd(), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "pdf", "docx", "doc", "txt", "md", "csv", "xlsx", "json",
    "py", "js", "ts", "tsx", "html", "css", "png", "jpg", "jpeg", "gif", "webp"
}


class AttachmentServiceError(Exception):
    pass


def extract_text_from_file(filename: str, content: bytes) -> str | None:
    """Extract plain text content from PDF, DOCX, TXT, CSV, MD, or Images."""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    try:
        if ext in ["txt", "md", "csv", "json", "py", "js", "html", "css", "ts", "tsx"]:
            return content.decode("utf-8", errors="replace")
        
        elif ext == "pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(content))
                text_parts = [page.extract_text() for page in reader.pages if page.extract_text()]
                return "\n".join(text_parts) if text_parts else None
            except Exception:
                return None
                
        elif ext == "docx":
            try:
                import docx
                doc = docx.Document(io.BytesIO(content))
                text_parts = [p.text for p in doc.paragraphs if p.text]
                return "\n".join(text_parts) if text_parts else None
            except Exception:
                return None

        elif ext in ["png", "jpg", "jpeg", "gif", "webp"]:
            return f"[Attached Image: {filename} ({len(content) // 1024} KB)]"
    except Exception:
        return None
    return None


class AttachmentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._attachments = AttachmentRepository(session)

    async def save_attachment(
        self,
        *,
        conversation_id: int,
        user_id: int,
        file: UploadFile,
        message_id: int | None = None,
    ) -> Attachment:
        original_filename = os.path.basename(file.filename or "file")
        ext = original_filename.split(".")[-1].lower() if "." in original_filename else ""

        if ext not in ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise AttachmentServiceError(
                f"Unsupported file format '.{ext}'. Supported formats: {allowed_list}"
            )

        content = await file.read()
        file_size = len(content)

        if file_size > 20 * 1024 * 1024:  # 20MB limit
            raise AttachmentServiceError("File size exceeds maximum 20MB limit.")

        unique_name = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)

        with open(file_path, "wb") as f:
            f.write(content)

        extracted_text = extract_text_from_file(original_filename, content)

        attachment = await self._attachments.create(
            conversation_id=conversation_id,
            user_id=user_id,
            message_id=message_id,
            filename=original_filename,
            file_type=file.content_type or f"application/{ext}",
            file_size=file_size,
            file_path=file_path,
            extracted_text=extracted_text,
        )
        await self._session.commit()
        return attachment

    async def list_for_conversation(self, conversation_id: int) -> list[Attachment]:
        attachments = await self._attachments.list_for_conversation(conversation_id)
        return list(attachments)

    async def get_attachment(self, attachment_id: int, *, user_id: int) -> Attachment | None:
        return await self._attachments.get_by_id(attachment_id, user_id=user_id)

    async def delete_attachment(self, attachment: Attachment) -> None:
        if os.path.exists(attachment.file_path):
            try:
                os.remove(attachment.file_path)
            except OSError:
                pass
        await self._attachments.delete(attachment)
        await self._session.commit()
