from fastapi import APIRouter, Query, Request, UploadFile, File, Depends
from typing import List, Dict, Any, Optional
from src.controllers.course_controller import upload_files_docs, create_course, delete_single_course, delete_all_courses
from src.services.course_auth import require_bearer

router = APIRouter(prefix="/course", tags=["Course"])


@router.post("/upload/file")
async def upload_files(request: Request, files: List[UploadFile] = File(...), _auth=Depends(require_bearer)):
    return await upload_files_docs(request, files)

@router.post("/create")
async def create_course_endpoint(request: Request, payload: Dict[str, Any], _auth=Depends(require_bearer)):
    return await create_course(request, payload)

@router.delete("/delete")
async def delete_course(request: Request, course_id: Optional[str] = Query(default=None), _auth=Depends(require_bearer)):
    return await delete_single_course(request, course_id)


@router.delete("/delete/all")
async def delete_all_course(request: Request, _auth=Depends(require_bearer)):
    return await delete_all_courses(request)


