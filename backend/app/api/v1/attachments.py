"""
Attachments endpoints for file uploads and downloads.
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.chat import AttachmentResponse
from app.services.attachment_service import AttachmentService, AttachmentServiceError

router = APIRouter(tags=["Attachments"])


@router.post("/conversations/{conversation_id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    conversation_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AttachmentResponse:
    service = AttachmentService(db)
    try:
        attachment = await service.save_attachment(
            conversation_id=conversation_id, user_id=user.id, file=file
        )
    except AttachmentServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AttachmentResponse.model_validate(attachment)


@router.get("/attachments/{attachment_id}/file")
async def download_attachment_file(
    attachment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    service = AttachmentService(db)
    attachment = await service.get_attachment(attachment_id, user_id=user.id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return FileResponse(
        path=attachment.file_path,
        filename=attachment.filename,
        media_type=attachment.file_type,
    )


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = AttachmentService(db)
    attachment = await service.get_attachment(attachment_id, user_id=user.id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    await service.delete_attachment(attachment)
