from fastapi import APIRouter, Request, UploadFile, File, Depends
from typing import List
from src.controllers.course_controller import upload_files_docs
from src.services.course_auth import require_bearer

router = APIRouter(prefix="", tags=["Course"])


@router.post("/upload/file")
async def upload_files(request: Request, files: List[UploadFile] = File(...), _auth=Depends(require_bearer)):
    return await upload_files_docs(request, files)


