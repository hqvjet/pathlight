# Pathlight User Service 👤

Standalone user management service for the Pathlight learning platform. This service handles all user-related operations including authentication, profile management, and user data.

## 🚀 Features

- **User Profile Management**: Complete CRUD operations for user profiles
- **Avatar Management**: Upload and serve user avatars
- **Authentication**: JWT-based authentication with role-based access
- **Dashboard Data**: User statistics and learning progress
- **Study Reminders**: Configurable daily study notifications
- **Admin Operations**: Administrative user management functions

## 📋 API Endpoints

### User Management
- `PUT /api/v1/user/change-info` - Update user personal information
- `GET /api/v1/user/` - Get user information (by ID or current user)
- `GET /api/v1/user/profile` - Get current user's profile
- `GET /api/v1/user/me` - Get basic current user info

### Avatar Management
- `GET /api/v1/user/avatar/?avatar_id=<id>` - Get avatar image
- `PUT /api/v1/user/avatar` - Upload/update avatar

### Dashboard & Activity
- `GET /api/v1/user/dashboard` - Get user dashboard data
- `POST /api/v1/user/activity` - Save user activity milestone
- `PUT /api/v1/user/notify-time` - Set study reminder time

### Admin Only
- `GET /api/v1/user/all` - Get all users (admin only)

## 🛠️ Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database
- pip (Python package manager)

### Installation

1. **Clone and navigate to the service directory:**
```bash
cd pathlight/services/user-service
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
Create a `.env` file in the service root:
```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/pathlight

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256

# Service Configuration
USER_SERVICE_PORT=8002
DEBUG=true
LOG_LEVEL=INFO

# Frontend (for CORS)
FRONTEND_URL=http://localhost:3000
```

4. **Start the service:**
```bash
# Using the startup script
python start.py

# Or directly with uvicorn
uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
```

5. **Verify the service is running:**
- API Documentation: http://localhost:8002/docs
- Health Check: http://localhost:8002/health
- Service Info: http://localhost:8002/

## 📊 Database Schema

The service uses the following main table:

### Users Table
- `id` (String, Primary Key) - UUID
- `email` (String, Unique) - User email
- `password` (String, Nullable) - Hashed password
- `given_name`, `family_name` (String) - User names
- `avatar_url` (String) - Avatar image URL
- `dob` (DateTime) - Date of birth
- `sex` (String) - Gender (Male/Female/Other)
- `bio` (Text) - User biography
- `level`, `current_exp`, `require_exp` - Gamification fields
- `remind_time` (String) - Daily study reminder time
- `is_active`, `is_email_verified` (Boolean) - Account status
- `created_at`, `updated_at`, `last_login` (DateTime) - Timestamps

## 🔧 Configuration

Key configuration options in `src/config.py`:

```python
class UserServiceConfig:
    SERVICE_PORT: int = 8002
    DATABASE_URL: str = "postgresql://..."
    JWT_SECRET_KEY: str = "your-secret-key"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
```

## 🐳 Docker Support

```bash
# Build the Docker image
docker build -t pathlight-user-service .

# Run the container
docker run -p 8002:8002 \
  -e DATABASE_URL=postgresql://... \
  -e JWT_SECRET_KEY=your-secret \
  pathlight-user-service
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src tests/
```

## 📝 Development

### Project Structure
```
user-service/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app setup
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── auth.py              # Authentication logic
│   ├── controllers/         # Business logic
│   │   └── user_controller.py
│   ├── routes/              # API routes
│   │   └── user_routes.py
│   └── schemas/             # Pydantic schemas
│       └── user_schemas.py
├── start.py                 # Standalone startup script
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
└── README.md               # This file
```

### Adding New Features

1. **Add new endpoints**: Update `src/routes/user_routes.py`
2. **Business logic**: Add functions in `src/controllers/user_controller.py`
3. **Data models**: Update `src/schemas/user_schemas.py`
4. **Database changes**: Create Alembic migrations

## 🔍 Monitoring & Logging

The service includes comprehensive logging for:
- Request/response tracking
- Authentication events
- Database operations
- Error handling

Logs are structured and include user email context where appropriate.

## 🚀 Production Deployment

For production deployment:

1. Set `DEBUG=false`
2. Use a production-grade database
3. Configure proper CORS origins
4. Set up SSL/TLS
5. Use environment-specific secrets
6. Configure log aggregation
7. Set up health monitoring

## 📞 Support

For issues or questions:
- Check the API documentation at `/docs`
- Review logs for error details
- Ensure database connectivity
- Verify JWT token configuration
