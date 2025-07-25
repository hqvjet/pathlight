from src.schemas.quiz_schemas import QuizCreate, QuizUpdate
from fastapi import Request

quizzes_db = {}
quiz_counter = 1

def get_quizzes_controller():
    return {"status": 200, "quizzes": list(quizzes_db.values())}

def create_quiz_controller(request: Request):
    global quiz_counter
    quiz_data = {"id": quiz_counter, "title": "Demo Quiz"}
    quizzes_db[quiz_counter] = quiz_data
    quiz_counter += 1
    return {"status": 200, "quiz": quiz_data}

def get_quiz_controller(quiz_id: int):
    if quiz_id not in quizzes_db:
        return {"status": 404, "message": "Quiz not found"}
    return {"status": 200, "quiz": quizzes_db[quiz_id]}

def update_quiz_controller(quiz_id: int, request: Request):
    if quiz_id not in quizzes_db:
        return {"status": 404, "message": "Quiz not found"}
    quizzes_db[quiz_id]["title"] = "Updated Title"
    return {"status": 200, "quiz": quizzes_db[quiz_id]}

def delete_quiz_controller(quiz_id: int, request: Request):
    if quiz_id not in quizzes_db:
        return {"status": 404, "message": "Quiz not found"}
    del quizzes_db[quiz_id]
    return {"status": 200, "message": "Quiz deleted"}
