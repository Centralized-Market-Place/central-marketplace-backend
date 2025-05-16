from centeral_marketplace.users.core import User
from fastapi import APIRouter, Depends, HTTPException
from fastapi_injector import Injected
from middleware import get_current_user

from centeral_marketplace.files.core import (
    SignedUrlRequest,
    SignedUrlResponse,
    FileType,
)
from centeral_marketplace.files.service import FileService

files_router = APIRouter(prefix="/files", tags=["files"])


@files_router.post("/signed-upload-url", response_model=SignedUrlResponse)
async def get_signed_upload_url(
    request: SignedUrlRequest,
    file_service: FileService = Injected(FileService),
    _: User = Depends(get_current_user),
):
    try:
        result = file_service.generate_signed_upload_url(
            file_type=request.file_type, folder=request.folder
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating signed URL: {str(e)}"
        )


@files_router.get("/allowed-file-types", response_model=list[str])
async def get_allowed_file_types():
    return [file_type.value for file_type in FileType]
