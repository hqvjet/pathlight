from fastapi import APIRouter, Request, UploadFile, File, Depends
from typing import List, Dict, Any
from src.controllers.course_controller import upload_files_docs, create_course
from src.services.course_auth import require_bearer

router = APIRouter(prefix="", tags=["Course"])


@router.post("/upload/file")
async def upload_files(request: Request, files: List[UploadFile] = File(...), _auth=Depends(require_bearer)):
    return await upload_files_docs(request, files)


@router.post("/create")
async def create_course_endpoint(request: Request, payload: Dict[str, Any], _auth=Depends(require_bearer)):
    return await create_course(request, payload)


