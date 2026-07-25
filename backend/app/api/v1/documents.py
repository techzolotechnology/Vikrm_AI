"""
Document endpoints: upload (multipart), list, detail, delete, and a
semantic chunk-search endpoint used both by a citation-viewer UI and
internally by ChatService.

Upload is processed synchronously (parse → chunk → embed → store)
within the request — see RagService for why. Max upload size is
enforced here rather than relying on a proxy default, so the error is
a clear 413 rather than a generic connection reset.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.document import DocumentChunkResult, DocumentResponse, DocumentSearchRequest
from app.services.rag.parsers import SUPPORTED_EXTENSIONS
from app.services.rag_service import RagService

router = APIRouter(prefix="/documents", tags=["Documents"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20MB


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[DocumentResponse]:
    service = RagService(db)
    documents = await service.list_documents(user_id=user.id)
    return [DocumentResponse.model_validate(d) for d in documents]


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    if not file.filename:
        raise HTTPException(status_code=422, detail="Uploaded file has no filename")

    extension = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{extension}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB upload limit",
        )

    service = RagService(db)
    document = await service.process_upload(
        user_id=user.id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    service = RagService(db)
    document = await service.get_document(document_id=document_id, user_id=user.id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = RagService(db)
    document = await service.get_document(document_id=document_id, user_id=user.id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    await service.delete_document(document=document)


@router.post("/search", response_model=list[DocumentChunkResult])
async def search_documents(
    body: DocumentSearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentChunkResult]:
    service = RagService(db)
    matches = await service.search_chunks(user_id=user.id, query=body.query, top_k=body.top_k)
    return [
        DocumentChunkResult(
            document_id=match["metadata"]["document_id"],
            filename=match["metadata"]["filename"],
            chunk_index=match["metadata"]["chunk_index"],
            content=match["document"],
            distance=match["distance"],
        )
        for match in matches
    ]
