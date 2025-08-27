from pydantic import BaseModel, Field
from typing import List, Optional


class CourseCreate(BaseModel):
    title: str
    description: str
    understand_level: str = Field(..., description="Trình độ người học (average, beginner, ...)")
    duration: int = Field(..., description="Số giờ khóa học")
    uploaded_file: List[str] = Field(..., description="Danh sách tên file đã upload lên S3")


class CourseInfoOut(BaseModel):
    course_id: str
    title: str
    description: str
    understand_level: str
    duration: int
    roadmap: Optional[str] = None

    class Config:
        from_attributes = True


class CourseCreatedResponse(BaseModel):
    status: int = 200
    message: str = "Đã tạo khóa học thành công"
