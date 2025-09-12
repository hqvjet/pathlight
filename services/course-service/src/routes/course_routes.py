from fastapi import APIRouter, Request, UploadFile, File, Depends, Query
from typing import List, Optional
from src.controllers.course_controller import upload_files_docs, delete_single_course, delete_all_courses

from src.services.course_auth import require_bearer
from src.services.status_service import fetch_generation_status

router = APIRouter(prefix="", tags=["Course"])


@router.post("/upload/file")
async def upload_files(request: Request, files: List[UploadFile] = File(...), _auth=Depends(require_bearer)):
    return await upload_files_docs(request, files)


@router.delete("/delete")
async def delete_course(request: Request, course_id: Optional[str] = Query(default=None), _auth=Depends(require_bearer)):
    return await delete_single_course(request, course_id)


@router.delete("/delete/all")
async def delete_all_course(request: Request, _auth=Depends(require_bearer)):
    return await delete_all_courses(request)

@router.get("/status")
async def get_generation_status(course_id: str = Query(...), _auth=Depends(require_bearer)):
        """Check generation status for a course by querying DynamoDB.

        Response shape (200):
        {
            "status": 200,
            "body": {
                "status": false,
                "vectorized": true,
                "generated_plan": true,
                "generated_lessons": true,
                "generated_final_test": false
            }
        }
        On not found: {"status": 501, "message": "Không tìm thấy khóa học này, xin vui lòng thử lại"}
        """
        result = fetch_generation_status(course_id)
        if not result:
                return {"status": 501, "message": "Không tìm thấy khóa học này, xin vui lòng thử lại"}
        return {"status": 200, "body": result}

