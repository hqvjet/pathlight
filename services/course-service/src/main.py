from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from jose import jwt
from datetime import datetime, timedelta
import logging

from .config import config

app = FastAPI(title="Course Service", version="1.0.0")

JWT_SECRET_KEY = config.JWT_SECRET_KEY
JWT_ALGORITHM = config.JWT_ALGORITHM

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=config.ALLOWED_METHODS,
    allow_headers=config.ALLOWED_HEADERS,
)

class Course(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    instructor: str
    duration: int
    level: str
    price: float
    created_at: Optional[datetime] = None

class Lesson(BaseModel):
    id: Optional[int] = None
    course_id: int
    title: str
    content: str
    video_url: Optional[str] = None
    duration: int
    order: int
    created_at: Optional[datetime] = None

class Test(BaseModel):
    id: Optional[int] = None
    course_id: int
    title: str
    description: str
    questions: List[Dict[str, Any]]
    passing_score: int
    time_limit: int
    created_at: Optional[datetime] = None

class TestResult(BaseModel):
    id: Optional[int] = None
    test_id: int
    user_email: str
    score: int
    answers: List[Dict[str, Any]]
    completed_at: Optional[datetime] = None

courses_db = {}
lessons_db = {}
tests_db = {}
test_results_db = {}
course_counter = 1
lesson_counter = 1
test_counter = 1
result_counter = 1

def verify_token(request: Request):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except Exception as e:
        print(f"Token verify error: {str(e)}")
        return None

@app.get("/")
async def root():
    return {"message": "Course Service đang chạy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "course-service"}

@app.get("/api/v1/courses")
async def get_courses():
    return {"status": 200, "courses": list(courses_db.values())}

@app.post("/api/v1/courses")
async def create_course(course: Course, request: Request):
    global course_counter
    user = verify_token(request)
    if not user:
        print("Create course: Unauthorized")
        return {"status": 401, "message": "Unauthorized"}
    course_data = course.dict()
    course_data["id"] = course_counter
    course_data["created_at"] = datetime.utcnow()
    courses_db[course_counter] = course_data
    course_counter += 1
    print(f"Course created: {course_data['title']}")
    return {"status": 200, "course": course_data}

@app.get("/api/v1/courses/{course_id}")
async def get_course(course_id: int):
    if course_id not in courses_db:
        return {"status": 404, "message": "Course not found"}
    
    course = courses_db[course_id]
    course_lessons = [lesson for lesson in lessons_db.values() if lesson["course_id"] == course_id]
    course_tests = [test for test in tests_db.values() if test["course_id"] == course_id]
    
    return {
        "status": 200,
        "course": course,
        "lessons": course_lessons,
        "tests": course_tests
    }

@app.put("/api/v1/courses/{course_id}")
async def update_course(course_id: int, course: Course, request: Request):
    user = verify_token(request)
    if not user:
        print("Update course: Unauthorized")
        return {"status": 401, "message": "Unauthorized"}
    if course_id not in courses_db:
        print("Update course: Not found")
        return {"status": 404, "message": "Course not found"}
    course_data = course.dict()
    course_data["id"] = course_id
    course_data["created_at"] = courses_db[course_id]["created_at"]
    courses_db[course_id] = course_data
    print(f"Course updated: {course_data['title']}")
    return {"status": 200, "course": course_data}

@app.delete("/api/v1/courses/{course_id}")
async def delete_course(course_id: int, request: Request):
    user = verify_token(request)
    if not user:
        print("Delete course: Unauthorized")
        return {"status": 401, "message": "Unauthorized"}
    if course_id not in courses_db:
        print("Delete course: Not found")
        return {"status": 404, "message": "Course not found"}
    del courses_db[course_id]
    lessons_db.clear()
    tests_db.clear()
    print(f"Course deleted: {course_id}")
    return {"status": 200, "message": "Course deleted"}

@app.get("/api/v1/courses/{course_id}/lessons")
async def get_lessons(course_id: int):
    if course_id not in courses_db:
        return {"status": 404, "message": "Course not found"}
    
    course_lessons = [lesson for lesson in lessons_db.values() if lesson["course_id"] == course_id]
    return {"status": 200, "lessons": course_lessons}

@app.post("/api/v1/courses/{course_id}/lessons")
async def create_lesson(course_id: int, lesson: Lesson, request: Request):
    global lesson_counter
    user = verify_token(request)
    if not user:
        print("Create lesson: Unauthorized")
        return {"status": 401, "message": "Unauthorized"}
    if course_id not in courses_db:
        print("Create lesson: Course not found")
        return {"status": 404, "message": "Course not found"}
    lesson_data = lesson.dict()
    lesson_data["id"] = lesson_counter
    lesson_data["course_id"] = course_id
    lesson_data["created_at"] = datetime.utcnow()
    lessons_db[lesson_counter] = lesson_data
    lesson_counter += 1
    print(f"Lesson created: {lesson_data['title']}")
    return {"status": 200, "lesson": lesson_data}

@app.get("/api/v1/lessons/{lesson_id}")
async def get_lesson(lesson_id: int):
    if lesson_id not in lessons_db:
        return {"status": 404, "message": "Lesson not found"}
    
    return {"status": 200, "lesson": lessons_db[lesson_id]}

@app.put("/api/v1/lessons/{lesson_id}")
async def update_lesson(lesson_id: int, lesson: Lesson, request: Request):
    user = verify_token(request)
    if not user:
        print("Update lesson: Unauthorized")
        return {"status": 401, "message": "Unauthorized"}
    if lesson_id not in lessons_db:
        print("Update lesson: Not found")
        return {"status": 404, "message": "Lesson not found"}
    lesson_data = lesson.dict()
    lesson_data["id"] = lesson_id
    lesson_data["created_at"] = lessons_db[lesson_id]["created_at"]
    lessons_db[lesson_id] = lesson_data
    print(f"Lesson updated: {lesson_data['title']}")
    return {"status": 200, "lesson": lesson_data}

@app.delete("/api/v1/lessons/{lesson_id}")
async def delete_lesson(lesson_id: int, request: Request):
    user = verify_token(request)
    if not user:
        print("Delete lesson: Unauthorized")
        return {"status": 401, "message": "Unauthorized"}
    if lesson_id not in lessons_db:
        print("Delete lesson: Not found")
        return {"status": 404, "message": "Lesson not found"}
    del lessons_db[lesson_id]
    print(f"Lesson deleted: {lesson_id}")
    return {"status": 200, "message": "Lesson deleted"}

@app.get("/api/v1/courses/{course_id}/tests")
async def get_tests(course_id: int):
    if course_id not in courses_db:
        return {"status": 404, "message": "Course not found"}
    
    course_tests = [test for test in tests_db.values() if test["course_id"] == course_id]
    return {"status": 200, "tests": course_tests}

@app.post("/api/v1/courses/{course_id}/tests")
async def create_test(course_id: int, test: Test, request: Request):
    global test_counter
    user = verify_token(request)
    if not user:
        print("Create test: Unauthorized")
        return {"status": 401, "message": "Unauthorized"}
    if course_id not in courses_db:
        print("Create test: Course not found")
        return {"status": 404, "message": "Course not found"}
    test_data = test.dict()
    test_data["id"] = test_counter
    test_data["course_id"] = course_id
    test_data["created_at"] = datetime.utcnow()
    tests_db[test_counter] = test_data
    test_counter += 1
    print(f"Test created: {test_data['title']}")
    return {"status": 200, "test": test_data}

@app.get("/api/v1/tests/{test_id}")
async def get_test(test_id: int):
    if test_id not in tests_db:
        return {"status": 404, "message": "Test not found"}
    
    return {"status": 200, "test": tests_db[test_id]}

@app.post("/api/v1/tests/{test_id}/submit")
async def submit_test(test_id: int, result: TestResult, request: Request):
    global result_counter
    user = verify_token(request)
    if not user:
        print("Submit test: Unauthorized")
        return {"status": 401, "message": "Unauthorized"}
    if test_id not in tests_db:
        print("Submit test: Test not found")
        return {"status": 404, "message": "Test not found"}
    result_data = result.dict()
    result_data["id"] = result_counter
    result_data["test_id"] = test_id
    result_data["user_email"] = user
    result_data["completed_at"] = datetime.utcnow()
    test_results_db[result_counter] = result_data
    result_counter += 1
    print(f"Test submitted: {test_id} by {user}")
    return {"status": 200, "result": result_data}

@app.get("/api/v1/user/test-results")
async def get_user_test_results(request: Request):
    user = verify_token(request)
    if not user:
        return {"status": 401, "message": "Unauthorized"}
    
    user_results = [result for result in test_results_db.values() if result["user_email"] == user]
    return {"status": 200, "results": user_results}

if __name__ == "__main__":
    import uvicorn
    port = config.SERVICE_PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
