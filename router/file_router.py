from fastapi import APIRouter, Depends, File, Query, UploadFile

from core.domain_exceptions import DomainError
from router.common import raise_http_error
from schemas.dependencies import get_file_controller
from schemas.response import R


router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    ctrl=Depends(get_file_controller),
):
    try:
        payloads = []
        for file in files:
            payloads.append(
                {
                    "filename": file.filename or "",
                    "content_type": file.content_type,
                    "content": await file.read(),
                }
            )
        return R.success(data=ctrl.upload_files(payloads))
    except DomainError as exc:
        raise_http_error(exc)


@router.get("")
def list_files(
    search: str | None = Query(default=None),
    ctrl=Depends(get_file_controller),
):
    try:
        return R.success(data=ctrl.list_files(search))
    except DomainError as exc:
        raise_http_error(exc)


@router.get("/{file_id}")
def get_file(file_id: str, ctrl=Depends(get_file_controller)):
    try:
        return R.success(data=ctrl.get_file(file_id))
    except DomainError as exc:
        raise_http_error(exc)


@router.delete("/{file_id}")
def delete_file(file_id: str, ctrl=Depends(get_file_controller)):
    try:
        ctrl.delete_file(file_id)
        return R.success(message="File deleted successfully.")
    except DomainError as exc:
        raise_http_error(exc)
