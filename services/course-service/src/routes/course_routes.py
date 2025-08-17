from fastapi import APIRouter, Request, UploadFile, File
from typing import List
from src.controllers.course_controller import upload_files_docs

router = APIRouter(prefix="", tags=["Course"])


@router.post("/upload/file")
async def upload_files(request: Request, files: List[UploadFile] = File(...)):
    return await upload_files_docs(request, files)


