from src.schemas.course_schemas import CourseCreate, CourseUpdate
from fastapi import Request

courses_db = {}
course_counter = 1

def get_courses_controller():
    return {"status": 200, "courses": list(courses_db.values())}

def create_course_controller(request: Request):
    global course_counter
    course_data = {"id": course_counter, "title": "Demo Course"}
    courses_db[course_counter] = course_data
    course_counter += 1
    return {"status": 200, "course": course_data}

def get_course_controller(course_id: int):
    if course_id not in courses_db:
        return {"status": 404, "message": "Course not found"}
    return {"status": 200, "course": courses_db[course_id]}

def update_course_controller(course_id: int, request: Request):
    if course_id not in courses_db:
        return {"status": 404, "message": "Course not found"}
    courses_db[course_id]["title"] = "Updated Title"
    return {"status": 200, "course": courses_db[course_id]}

def delete_course_controller(course_id: int, request: Request):
    if course_id not in courses_db:
        return {"status": 404, "message": "Course not found"}
    del courses_db[course_id]
    return {"status": 200, "message": "Course deleted"}
