# Auth Service

Dịch vụ xác thực cho hệ thống Pathlight với đầy đủ các chức năng đăng ký, đăng nhập, xác thực email, quên mật khẩu, và OAuth.

## 🚀 Cách chạy

### Chạy với Docker (Khuyên dùng)

```bash
# Build và chạy service
./run.sh

# Hoặc sử dụng docker-compose trực tiếp
docker-compose up --build
```

### Chạy trực tiếp

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy service
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

## 📋 API Endpoints

### 1.1. Đăng ký
- **Endpoint**: `POST /api/v1/signup`
- **Request**:
```json
{
  "email": "hqvjet.1906@gmail.com",
  "password": "v1231233"
}
```
- **Success Response**:
```json
{
  "status": 200,
  "message": "Mã xác thực đã được gửi vào email của bạn, xin vui lòng xác thực email của bạn"
}
```

### 1.2. Xác thực Email
- **Endpoint**: `GET /api/v1/verify-email?token={token}`
- **Method**: GET (thông qua link trong email)
- **Success Response**:
```json
{
  "status": 200
}
```

### 1.3. Đăng nhập
- **Endpoint**: `POST /api/v1/signin`
- **Request**:
```json
{
  "email": "hqvjet.1906@gmail.com",
  "password": "v1231233"
}
```
- **Success Response**:
```json
{
  "status": 200,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 1.4. Đăng xuất
- **Endpoint**: `GET /api/v1/signout`
- **Headers**: `Authorization: Bearer {access_token}`
- **Success Response**:
```json
{
  "status": 200
}
```

### 1.5. Quên mật khẩu
- **Endpoint**: `POST /api/v1/forget-password`
- **Request**:
```json
{
  "email": "hqvjet.1906@gmail.com"
}
```
- **Success Response**:
```json
{
  "status": 200,
  "message": "Xin vui lòng kiểm tra email của bạn để reset mật khẩu"
}
```

### 1.6. Đặt lại mật khẩu
- **Endpoint**: `POST /api/v1/reset-password/{token}`
- **Request**:
```json
{
  "new_password": "newpassword123"
}
```
- **Success Response**:
```json
{
  "status": 200
}
```

### 1.7. Đăng nhập bằng Google OAuth
- **Endpoint**: `POST /api/v1/oauth-signin`
- **Request**:
```json
{
  "email": "hqvjet.1906@gmail.com",
  "google_id": "10769150350006150715113082367",
  "given_name": "Việt",
  "family_name": "Hoàng Quốc",
  "avatar_id": "https://lh3.googleusercontent.com/a-/AOh14GhX..."
}
```
- **Success Response**:
```json
{
  "status": 200,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 1.8. Đổi mật khẩu
- **Endpoint**: `POST /api/v1/user/change-password`
- **Headers**: `Authorization: Bearer {access_token}`
- **Request**:
```json
{
  "password": "v1231233",
  "new_password": "0838575535"
}
```
- **Success Response**:
```json
{
  "status": 200
}
```

### 1.9. Đăng nhập Admin
- **Endpoint**: `POST /api/v1/admin/signin`
- **Request**:
```json
{
  "username": "admin",
  "password": "admin"
}
```
- **Success Response**:
```json
{
  "status": 200,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## 🧪 Testing

```bash
# Test tất cả APIs
./test_apis.sh

# Hoặc test từng endpoint bằng curl
curl -X POST http://localhost:8001/api/v1/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

## 🔧 Configuration

Cấu hình thông qua biến môi trường:

```bash
# JWT
JWT_SECRET_KEY=your-secret-key

# Email SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourapp.com

# Frontend URL (để redirect sau verify email)
FRONTEND_URL=http://localhost:3000
```

## 📚 API Documentation

Sau khi chạy service, truy cập:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 🏗️ Architecture

- **Framework**: FastAPI
- **Authentication**: JWT tokens
- **Password Hashing**: bcrypt
- **Email**: aiosmtplib (SMTP)
- **Storage**: In-memory (có thể thay thế bằng database)

## 🔒 Security Features

- JWT token authentication
- Password hashing với bcrypt
- Token blacklisting cho logout
- Email verification
- Password reset với secure tokens
- OAuth integration

## 📝 Notes

- Admin mặc định: username=`admin`, password=`admin`
- Tokens email verification hết hạn sau 24 giờ
- Tokens reset password hết hạn sau 1 giờ
- Access tokens hết hạn sau 24 giờ
