# Pathlight Services

Hệ thống microservices cho nền tảng học tập trực tuyến Pathlight.

## 🏗️ Kiến trúc

### Services:
- **Auth Service** (Port 8001): Xác thực và ủy quyền
- **Course Service** (Port 8002): Quản lý khóa học, bài học và bài kiểm tra
- **Quiz Service** (Port 8003): Quản lý quiz và bảng xếp hạng
- **User Service** (Port 8004): Quản lý hồ sơ người dùng và tiến độ học tập

## 🚀 Cách chạy

### Chạy tất cả services:
```bash
./run_all.sh
```

### Chạy từng service riêng biệt:
```bash
cd auth-service && docker-compose up --build
cd course-service && docker-compose up --build
cd quiz-service && docker-compose up --build
cd user-service && docker-compose up --build
```

## 🧪 Testing

```bash
# Test tất cả services
./test_all_services.sh

# Test từng service
cd auth-service && ./test_apis.sh
```

## 📋 API Endpoints

### Auth Service (8001)
- `POST /api/v1/signup` - Đăng ký
- `GET /api/v1/verify-email?token=...` - Xác thực email
- `POST /api/v1/signin` - Đăng nhập
- `GET /api/v1/signout` - Đăng xuất
- `POST /api/v1/forget-password` - Quên mật khẩu
- `POST /api/v1/reset-password/{token}` - Đặt lại mật khẩu
- `POST /api/v1/oauth-signin` - Đăng nhập OAuth
- `POST /api/v1/user/change-password` - Đổi mật khẩu
- `POST /api/v1/admin/signin` - Đăng nhập admin

### Course Service (8002)
- `GET /api/v1/courses` - Danh sách khóa học
- `POST /api/v1/courses` - Tạo khóa học
- `GET /api/v1/courses/{id}` - Chi tiết khóa học
- `PUT /api/v1/courses/{id}` - Cập nhật khóa học
- `DELETE /api/v1/courses/{id}` - Xóa khóa học
- `GET /api/v1/courses/{id}/lessons` - Danh sách bài học
- `POST /api/v1/courses/{id}/lessons` - Tạo bài học
- `GET /api/v1/lessons/{id}` - Chi tiết bài học
- `PUT /api/v1/lessons/{id}` - Cập nhật bài học
- `DELETE /api/v1/lessons/{id}` - Xóa bài học
- `GET /api/v1/courses/{id}/tests` - Danh sách bài kiểm tra
- `POST /api/v1/courses/{id}/tests` - Tạo bài kiểm tra
- `GET /api/v1/tests/{id}` - Chi tiết bài kiểm tra
- `POST /api/v1/tests/{id}/submit` - Nộp bài kiểm tra
- `GET /api/v1/user/test-results` - Kết quả kiểm tra của user

### Quiz Service (8003)
- `GET /api/v1/quizzes` - Danh sách quiz
- `POST /api/v1/quizzes` - Tạo quiz
- `GET /api/v1/quizzes/{id}` - Chi tiết quiz
- `POST /api/v1/quizzes/{id}/attempt` - Làm quiz
- `GET /api/v1/user/quiz-attempts` - Lịch sử làm quiz
- `GET /api/v1/quizzes/{id}/leaderboard` - Bảng xếp hạng

### User Service (8004)
- `GET /api/v1/profile` - Hồ sơ người dùng
- `PUT /api/v1/profile` - Cập nhật hồ sơ
- `POST /api/v1/enrollments` - Đăng ký khóa học
- `GET /api/v1/enrollments` - Danh sách khóa học đã đăng ký
- `DELETE /api/v1/enrollments/{course_id}` - Hủy đăng ký
- `POST /api/v1/progress` - Cập nhật tiến độ
- `GET /api/v1/progress` - Xem tiến độ
- `GET /api/v1/progress/course/{id}` - Tiến độ theo khóa học

## 🔐 Authentication

Tất cả APIs (trừ public endpoints) yêu cầu JWT token trong header:
```
Authorization: Bearer {access_token}
```

### Admin mặc định:
- Username: `admin`
- Password: `admin`

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Authentication**: JWT
- **Containerization**: Docker
- **API Documentation**: Swagger UI

## 📝 Features

### ✅ Đã hoàn thành:
- [x] Authentication service với email verification
- [x] Course management với lessons và tests
- [x] Quiz system với leaderboard
- [x] User profile và enrollment management
- [x] JWT-based authorization
- [x] Docker containerization
- [x] API documentation

### 🔄 Có thể mở rộng:
- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] File upload service
- [ ] Notification service
- [ ] Payment service
- [ ] API Gateway với rate limiting
- [ ] Monitoring và logging

## 📊 Monitoring

```bash
# Xem logs tất cả services
docker-compose logs -f

# Xem logs service cụ thể
docker-compose logs -f auth-service

# Xem resource usage
docker stats
```

## 🛑 Dừng services

```bash
docker-compose down

# Xóa volumes (nếu cần)
docker-compose down -v
```
