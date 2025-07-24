courses_db = {}
course_counter = 1

def get_all_courses():
    return list(courses_db.values())

def create_course(course_data):
    global course_counter
    course_data["id"] = course_counter
    courses_db[course_counter] = course_data
    course_counter += 1
    return course_data

def get_course_by_id(course_id):
    return courses_db.get(course_id)

def update_course(course_id, update_data):
    if course_id in courses_db:
        courses_db[course_id].update(update_data)
        return courses_db[course_id]
    return None

def delete_course(course_id):
    if course_id in courses_db:
        del courses_db[course_id]
        return True
    return False
