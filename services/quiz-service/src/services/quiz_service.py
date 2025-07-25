quizzes_db = {}
quiz_counter = 1

def get_all_quizzes():
    return list(quizzes_db.values())

def create_quiz(quiz_data):
    global quiz_counter
    quiz_data["id"] = quiz_counter
    quizzes_db[quiz_counter] = quiz_data
    quiz_counter += 1
    return quiz_data

def get_quiz_by_id(quiz_id):
    return quizzes_db.get(quiz_id)

def update_quiz(quiz_id, update_data):
    if quiz_id in quizzes_db:
        quizzes_db[quiz_id].update(update_data)
        return quizzes_db[quiz_id]
    return None

def delete_quiz(quiz_id):
    if quiz_id in quizzes_db:
        del quizzes_db[quiz_id]
        return True
    return False
