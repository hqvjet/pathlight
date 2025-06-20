#!/bin/bash

echo "🚀 Testing All Services..."
echo "=========================="

BASE_AUTH="http://localhost:8001"
BASE_COURSE="http://localhost:8002"
BASE_QUIZ="http://localhost:8003"
BASE_USER="http://localhost:8004"

echo "1. Testing Health Endpoints..."
curl -s $BASE_AUTH/health | jq .
curl -s $BASE_COURSE/health | jq .
curl -s $BASE_QUIZ/health | jq .
curl -s $BASE_USER/health | jq .
echo ""

echo "2. Testing Auth Service - Admin Login..."
ADMIN_RESPONSE=$(curl -s -X POST "$BASE_AUTH/api/v1/admin/signin" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}')
echo $ADMIN_RESPONSE | jq .

ADMIN_TOKEN=$(echo $ADMIN_RESPONSE | jq -r '.access_token // empty')
echo ""

if [ ! -z "$ADMIN_TOKEN" ]; then
  echo "✅ Admin token: ${ADMIN_TOKEN:0:20}..."
  
  echo "3. Testing Course Service - Create Course..."
  COURSE_RESPONSE=$(curl -s -X POST "$BASE_COURSE/api/v1/courses" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{
      "title": "Test Course",
      "description": "A test course",
      "instructor": "Admin",
      "duration": 120,
      "level": "beginner",
      "price": 99.99
    }')
  echo $COURSE_RESPONSE | jq .
  
  COURSE_ID=$(echo $COURSE_RESPONSE | jq -r '.course.id // empty')
  echo ""
  
  if [ ! -z "$COURSE_ID" ]; then
    echo "4. Testing Course Service - Create Lesson..."
    curl -s -X POST "$BASE_COURSE/api/v1/courses/$COURSE_ID/lessons" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -d '{
        "course_id": '$COURSE_ID',
        "title": "Test Lesson",
        "content": "Lesson content",
        "duration": 30,
        "order": 1
      }' | jq .
    echo ""
    
    echo "5. Testing Course Service - Create Test..."
    curl -s -X POST "$BASE_COURSE/api/v1/courses/$COURSE_ID/tests" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -d '{
        "course_id": '$COURSE_ID',
        "title": "Test Quiz",
        "description": "A test quiz",
        "questions": [{"question": "What is 2+2?", "options": ["3", "4", "5"], "correct": 1}],
        "passing_score": 70,
        "time_limit": 60
      }' | jq .
    echo ""
  fi
  
  echo "6. Testing Quiz Service - Create Quiz..."
  curl -s -X POST "$BASE_QUIZ/api/v1/quizzes" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{
      "title": "General Knowledge Quiz",
      "description": "Test your knowledge",
      "questions": [{"question": "Capital of Vietnam?", "options": ["Hanoi", "HCMC", "Da Nang"], "correct": 0}],
      "time_limit": 30,
      "difficulty": "easy",
      "category": "general"
    }' | jq .
  echo ""
  
  echo "7. Testing User Service - Get Profile..."
  curl -s -X GET "$BASE_USER/api/v1/profile" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq .
  echo ""
  
  echo "8. Testing User Service - Update Profile..."
  curl -s -X PUT "$BASE_USER/api/v1/profile" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{
      "email": "admin@example.com",
      "first_name": "Admin",
      "last_name": "User",
      "bio": "System Administrator"
    }' | jq .
  echo ""
  
else
  echo "❌ Failed to get admin token"
fi

echo "✅ All service tests completed!"
