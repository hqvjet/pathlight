# Hướng Dẫn Debug và Fix Vấn Đề "Không Thể Lấy Tổng Số Course"

## 🔍 Tổng Quan Vấn Đề

Dashboard hiển thị "0" cho "Tổng Số Khóa Học" mặc dù user có courses.

## 🏗️ Kiến Trúc Hệ Thống

```
Frontend (Next.js)
    ↓ GET /user/dashboard
User Service (Python/FastAPI)
    ↓ GET /api/course/all
Course Service (Python/FastAPI)
```

## ✅ Những Gì Đã Được Fix

### 1. **Cải Thiện Logging trong Backend** ✓
File: `services/user-service/src/services/external/course_client.py`

- Thêm detailed logging cho mọi bước của quá trình fetch course data
- Log configuration (URL, headers)
- Log response (status, body, parsing)
- Log errors với context đầy đủ

### 2. **Thêm Debug Logging trong Frontend** ✓
File: `frontend/src/components/user/dashboard/StatsGrid.tsx`

- Log course data khi totalCourses = 0 trong development mode
- Giúp debug frontend parsing issues

### 3. **Tạo Test Script** ✓
File: `test_dashboard_course_data.sh`

- Script để test connectivity và endpoints

## 🔧 Cách Debug

### Bước 1: Kiểm Tra Logs

#### Backend Logs (User Service)
```bash
# Nếu dùng Docker
docker logs pathlight-user-service -f | grep COURSE_CLIENT

# Nếu chạy local
# Check terminal running user-service
```

Tìm các dòng bắt đầu với `[COURSE_CLIENT]`:
- ✅ `[COURSE_CLIENT] ✅ Final Stats:` - Thành công
- ❌ `[COURSE_CLIENT] ❌` - Có lỗi
- ⚠️ `[COURSE_CLIENT] ⚠️` - Cảnh báo

#### Frontend Logs (Browser Console)
```javascript
// Mở DevTools > Console
// Tìm các logs:
- "🔍 Dashboard API Response"
- "📊 Dashboard Data Parsing"
- "✅ Final Profile Data"
- "⚠️ StatsGrid Debug - Course Data"
```

### Bước 2: Xác Định Root Cause

#### Case 1: Course Service Không Chạy
**Triệu chứng:**
```
[COURSE_CLIENT] 🔌 CONNECTION ERROR
Cannot connect to course service at http://localhost:8002
```

**Giải pháp:**
```bash
# Kiểm tra course service
curl http://localhost:8002/health

# Hoặc nếu dùng Docker
docker ps | grep course-service
docker logs pathlight-course-service

# Start course service nếu chưa chạy
docker-compose up -d course-service
# hoặc
cd services/course-service && python src/main.py
```

#### Case 2: Sai URL Configuration
**Triệu chứng:**
```
[COURSE_CLIENT] 🌐 COURSE_SERVICE_URL: http://wrong-url
```

**Giải pháp:**
```bash
# Kiểm tra environment variables
echo $COURSE_SERVICE_URL

# Nếu dùng Docker, check docker-compose.yml
# Nếu local, check .env file
```

Thêm/sửa trong `.env` hoặc `docker-compose.yml`:
```bash
# For Docker
COURSE_SERVICE_URL=http://course-service:8002

# For local development
COURSE_SERVICE_URL=http://localhost:8002
```

#### Case 3: User Không Có Course
**Triệu chứng:**
```
[COURSE_CLIENT] ⚠️ No courses found for user {user_id}
[COURSE_CLIENT] ✅ Final Stats: {'total_courses': 0, ...}
```

**Giải pháp:**
- Đây là trường hợp bình thường nếu user chưa tạo/enroll khóa học nào
- Tạo course mới hoặc enroll user vào course

#### Case 4: API Response Format Sai
**Triệu chứng:**
```
[COURSE_CLIENT] 🔑 Response keys: ['message', 'data']  # Không có 'courses' key
```

**Giải pháp:**
- Check course-service API response format
- Có thể cần update course_client.py để parse đúng structure

### Bước 3: Test Trực Tiếp

#### Test Course Service Endpoint
```bash
# 1. Get auth token (login first)
TOKEN="your_jwt_token_here"

# 2. Test course service directly
curl -X GET \
  http://localhost:8002/api/course/all \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Expected response:
{
  "status": 200,
  "courses": [
    {
      "id": "...",
      "title": "...",
      "finish": false,
      "lesson_num": 5,
      ...
    }
  ]
}
```

#### Test User Service Dashboard Endpoint
```bash
curl -X GET \
  http://localhost:8004/user/dashboard \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Check response:
{
  "status": 200,
  "info": {
    "total_courses": 5,  # <-- Should NOT be 0 if user has courses
    "course_num": 5,
    ...
  }
}
```

## 🔍 Common Issues & Solutions

### Issue: "total_courses": 0 nhưng user có courses

**Nguyên nhân có thể:**
1. Course service không accessible từ user service
2. COURSE_SERVICE_URL config sai
3. Authentication/Authorization issues
4. Network issues (Docker network, firewall)
5. Course service trả về format khác

**Debug steps:**
```bash
# 1. Check services are running
docker ps

# 2. Check network connectivity (if using Docker)
docker exec pathlight-user-service curl http://course-service:8002/health

# 3. Check logs
docker logs pathlight-user-service | tail -100
docker logs pathlight-course-service | tail -100

# 4. Test API directly
./test_dashboard_course_data.sh
```

## 📝 Quick Fix Checklist

- [ ] Course service đang chạy
- [ ] User service đang chạy  
- [ ] COURSE_SERVICE_URL được set đúng
- [ ] Network connectivity OK (services có thể gọi nhau)
- [ ] User đã có courses trong database
- [ ] JWT token valid và được truyền đúng
- [ ] Course service API trả về format đúng
- [ ] Check logs không có errors

## 🎯 Expected Behavior

Sau khi fix:
1. Backend logs sẽ show:
   ```
   [COURSE_CLIENT] ✅ Final Stats: {'total_courses': 5, 'completed_courses': 2, 'total_lessons': 15}
   ```

2. Frontend console sẽ show trong "Final Profile Data":
   ```
   Total Courses: 5  (not 0)
   ```

3. Dashboard UI sẽ hiển thị số đúng thay vì "0"

## 🆘 Nếu Vẫn Không Work

1. **Restart services:**
   ```bash
   docker-compose restart user-service course-service
   # or
   docker-compose down && docker-compose up -d
   ```

2. **Clear cache:**
   ```bash
   # Frontend
   # Clear localStorage in browser DevTools > Application > Local Storage
   
   # Backend - restart services
   ```

3. **Check network configuration:**
   ```bash
   # If using Docker
   docker network ls
   docker network inspect pathlight_default
   ```

4. **Verify data in database:**
   ```sql
   -- Check if courses exist for user
   SELECT * FROM courses WHERE user_id = 'your-user-id';
   ```

## 📧 Contact & Support

Nếu issue vẫn còn sau khi làm theo hướng dẫn:
1. Collect logs từ cả user-service và course-service
2. Screenshot browser console
3. Output của test script
4. Config files (.env, docker-compose.yml)
