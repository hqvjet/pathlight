# Database Migrations - PathLight Project

Đây là tài liệu hướng dẫn về các migration Alembic cho các microservices trong dự án PathLight.

## Cấu trúc Database theo ERD

### 1. Auth Service
- **admin**: Bảng quản trị viên với thông tin đăng nhập

### 2. User Service  
- **user**: Thông tin người dùng (email, password, google_id)
- **user_profile**: Profile chi tiết của người dùng (tên, avatar, level, exp, v.v.)

### 3. Course Service
- **course**: Khóa học của người dùng
- **course_info**: Thông tin chi tiết khóa học  
- **understand_level_tag**: Tag mức độ hiểu biết
- **lesson**: Bài học trong khóa học
- **test**: Bài kiểm tra của lesson
- **lesson_qa**: Câu hỏi trong bài test
- **difficult_level**: Mức độ khó của câu hỏi

### 4. Quiz Service
- **quiz_info**: Thông tin tổng quan về quiz
- **quiz**: Quiz instance của user
- **quiz_qa**: Câu hỏi quiz với đáp án

## Cách chạy migrations

### ✅ FIXED - Migrations đã sẵn sàng sử dụng với SQLite

Các migrations hiện đã được cấu hình để sử dụng SQLite làm database mặc định để tránh lỗi dependencies và dễ dàng development.

### Chạy migrations cho từng service:

#### Auth Service
```bash
cd services/auth-service
alembic upgrade head
```

#### User Service  
```bash
cd services/user-service
alembic upgrade head
```

#### Course Service
```bash
cd services/course-service
alembic upgrade head
```

#### Quiz Service
```bash
cd services/quiz-service
alembic upgrade head
```

### ✅ Trạng thái migrations:
- ✅ **auth-service**: Migration thành công → `auth.db`
- ✅ **user-service**: Migration thành công → `user.db`  
- ✅ **course-service**: Migration thành công → `course.db`
- ✅ **quiz-service**: Migration thành công → `quiz.db`

## Environment Variables

### Development (Hiện tại - SQLite)
Các service hiện sử dụng SQLite cho development:

- **AUTH_SERVICE**: `sqlite:///./auth.db`
- **USER_SERVICE**: `sqlite:///./user.db`  
- **COURSE_SERVICE**: `sqlite:///./course.db`
- **QUIZ_SERVICE**: `sqlite:///./quiz.db`

### Production (PostgreSQL)
Để chuyển sang PostgreSQL trong production, set environment variables:

- **AUTH_SERVICE**: `DATABASE_URL=postgresql://user:password@localhost/auth_db`
- **USER_SERVICE**: `DATABASE_URL=postgresql://user:password@localhost/user_db`  
- **COURSE_SERVICE**: `DATABASE_URL=postgresql://user:password@localhost/course_db`
- **QUIZ_SERVICE**: `DATABASE_URL=postgresql://user:password@localhost/quiz_db`

Và cài đặt psycopg2: `pip install psycopg2-binary`

## Lưu ý quan trọng

1. **Foreign Key Cross-Service**: 
   - User service có references tới user từ các service khác
   - Trong thực tế production cần cân nhắc sử dụng UUID hoặc distributed ID

2. **Migration Order**:
   - Chạy migration theo thứ tự: auth → user → course → quiz
   - Các bảng có foreign key phải được tạo sau bảng được reference

3. **Data Types**:
   - String columns được sử dụng cho IDs (có thể thay bằng UUID)
   - DateTime có timezone support
   - BigInteger cho exp points để support large numbers

## Rollback Migrations

Để rollback migrations:
```bash
cd services/<service-name>
alembic downgrade base  # Rollback tất cả
alembic downgrade -1    # Rollback 1 revision
```

## Development Workflow

1. Thay đổi models trong `src/models.py`
2. Generate migration: `alembic revision --autogenerate -m "Description"`
3. Review migration file trong `alembic/versions/`
4. Apply migration: `alembic upgrade head`

## Troubleshooting

- Nếu gặp lỗi import SQLAlchemy, cài đặt dependencies: `pip install -e .`
- Nếu migration conflict, check revision history: `alembic history`
- Database connection issues: check DATABASE_URL environment variable
