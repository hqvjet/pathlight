BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE user_profile (
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name TEXT,
    last_name TEXT,
    dob DATE NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,
    current_exp BIGINT NOT NULL DEFAULT 0,
    sex BOOLEAN NOT NULL,
    bio TEXT
);

CREATE TABLE "user" (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    CONSTRAINT fk_user_profile FOREIGN KEY (profile_id)
        REFERENCES user_profile(profile_id) ON DELETE CASCADE
);
CREATE INDEX idx_user_profile_id ON "user" (profile_id);

CREATE TABLE admin (
    admin_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE understand_level_tag (
    understand_level_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    understand_level TEXT NOT NULL
);

CREATE TABLE course_info (
    course_info_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    understand_level_id UUID NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    roadmap TEXT,
    remind_time TEXT,
    CONSTRAINT fk_course_info_understand_level FOREIGN KEY (understand_level_id)
        REFERENCES understand_level_tag(understand_level_id) ON DELETE CASCADE
);
CREATE INDEX idx_course_info_understand_level_id ON course_info (understand_level_id);

CREATE TABLE course (
    course_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_info_id UUID NOT NULL,
    user_id UUID NOT NULL,
    finish BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_course_info FOREIGN KEY (course_info_id)
        REFERENCES course_info(course_info_id) ON DELETE CASCADE,
    CONSTRAINT fk_course_user FOREIGN KEY (user_id)
        REFERENCES "user"(user_id) ON DELETE CASCADE
);
CREATE INDEX idx_course_course_info_id ON course (course_info_id);
CREATE INDEX idx_course_user_id ON course (user_id);

CREATE TABLE lesson (
    lesson_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    description TEXT NOT NULL,
    img_url TEXT,
    finish BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_lesson_course FOREIGN KEY (course_id)
        REFERENCES course(course_id) ON DELETE CASCADE
);
CREATE INDEX idx_lesson_course_id ON lesson (course_id);

CREATE TABLE test (
    test_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id UUID NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    duration INTEGER NOT NULL,
    exp INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_test_lesson FOREIGN KEY (lesson_id)
        REFERENCES lesson(lesson_id) ON DELETE CASCADE
);
CREATE INDEX idx_test_lesson_id ON test (lesson_id);

CREATE TABLE difficult_level (
    difficult_level_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    difficult_level TEXT NOT NULL
);

CREATE TABLE lesson_qa (
    qa_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID NOT NULL,
    difficult_level_id UUID NOT NULL,
    question TEXT NOT NULL,
    explain TEXT NOT NULL,
    option1 TEXT NOT NULL,
    option2 TEXT NOT NULL,
    option3 TEXT NOT NULL,
    option4 TEXT NOT NULL,
    CONSTRAINT fk_lesson_qa_test FOREIGN KEY (test_id)
        REFERENCES test(test_id) ON DELETE CASCADE,
    CONSTRAINT fk_lesson_qa_difficult_level FOREIGN KEY (difficult_level_id)
        REFERENCES difficult_level(difficult_level_id) ON DELETE CASCADE
);
CREATE INDEX idx_lesson_qa_test_id ON lesson_qa (test_id);
CREATE INDEX idx_lesson_qa_difficult_level_id ON lesson_qa (difficult_level_id);

CREATE TABLE final_test (
    final_test_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    duration INTEGER NOT NULL,
    exp INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_final_test_course FOREIGN KEY (course_id)
        REFERENCES course(course_id) ON DELETE CASCADE
);
CREATE INDEX idx_final_test_course_id ON final_test (course_id);

CREATE TABLE final_qa (
    final_qa_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    final_test_id UUID NOT NULL,
    question TEXT NOT NULL,
    explain TEXT NOT NULL,
    option1 TEXT NOT NULL,
    option2 TEXT NOT NULL,
    option3 TEXT NOT NULL,
    option4 TEXT NOT NULL,
    CONSTRAINT fk_final_qa_final_test FOREIGN KEY (final_test_id)
        REFERENCES final_test(final_test_id) ON DELETE CASCADE
);
CREATE INDEX idx_final_qa_final_test_id ON final_qa (final_test_id);

CREATE TABLE quiz_info (
    quiz_info_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    remind_time TEXT
);

CREATE TABLE quiz (
    quiz_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_info_id UUID NOT NULL,
    user_id UUID NOT NULL,
    finish BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    upload_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_quiz_info FOREIGN KEY (quiz_info_id)
        REFERENCES quiz_info(quiz_info_id) ON DELETE CASCADE,
    CONSTRAINT fk_quiz_user FOREIGN KEY (user_id)
        REFERENCES "user"(user_id) ON DELETE CASCADE
);
CREATE INDEX idx_quiz_quiz_info_id ON quiz (quiz_info_id);
CREATE INDEX idx_quiz_user_id ON quiz (user_id);

CREATE TABLE quiz_qa (
    qa_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL,
    question TEXT NOT NULL,
    explain TEXT NOT NULL,
    option1 TEXT NOT NULL,
    option2 TEXT NOT NULL,
    option3 TEXT NOT NULL,
    option4 TEXT NOT NULL,
    CONSTRAINT fk_quiz_qa_quiz FOREIGN KEY (quiz_id)
        REFERENCES quiz(quiz_id) ON DELETE CASCADE
);
CREATE INDEX idx_quiz_qa_quiz_id ON quiz_qa (quiz_id);

COMMIT;
