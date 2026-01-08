#!/usr/bin/env python3
"""Index test courses for recommendation testing."""

import sys
import os

# Load .env
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

sys.path.insert(0, 'src')

from services.recommendation_service import RecommendationService

rec_service = RecommendationService()

print('📚 Indexing test courses...')

# Index 3 test courses
courses = [
    {
        'course_id': 'test-course-001',
        'title': 'Python Programming Basics',
        'description': 'Learn Python programming fundamentals and best practices',
        'user_id': 'other-user-1',
        'publish': True,
        'level': 'easy',
        'duration': 30
    },
    {
        'course_id': 'test-course-002',
        'title': 'Machine Learning with Python',
        'description': 'Advanced machine learning techniques using Python and scikit-learn',
        'user_id': 'other-user-2',
        'publish': True,
        'level': 'hard',
        'duration': 60
    },
    {
        'course_id': 'test-course-003',
        'title': 'Data Science Fundamentals',
        'description': 'Introduction to data science, statistics, and data visualization',
        'user_id': 'other-user-3',
        'publish': True,
        'level': 'medium',
        'duration': 45
    }
]

for course in courses:
    rec_service.index_course_vector(**course)
    print(f"  ✅ Indexed {course['course_id']}: {course['title']}")

print('\n🎉 All test courses indexed!')
