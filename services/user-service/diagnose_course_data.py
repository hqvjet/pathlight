#!/usr/bin/env python3
"""
Diagnostic script to check course data fetching for user-service
Run this from the user-service directory: python diagnose_course_data.py
"""

import os
import sys
import requests
from pathlib import Path

# Try to load from .env
try:
    from dotenv import load_dotenv
    for env_path in [".env", "../.env", "../../.env", "../../../.env"]:
        if Path(env_path).exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

def color_print(text, color="reset"):
    colors = {
        "reset": "\033[0m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
    }
    print(f"{colors.get(color, colors['reset'])}{text}{colors['reset']}")

def check_env_vars():
    color_print("\n📋 Step 1: Checking Environment Variables", "cyan")
    color_print("=" * 60, "cyan")
    
    course_url = os.getenv("COURSE_SERVICE_URL")
    quiz_url = os.getenv("QUIZ_SERVICE_URL")
    user_port = os.getenv("USER_SERVICE_PORT", "8004")
    
    if course_url:
        color_print(f"✅ COURSE_SERVICE_URL: {course_url}", "green")
    else:
        color_print("❌ COURSE_SERVICE_URL not set!", "red")
        color_print("   Using default: http://localhost:8002", "yellow")
        course_url = "http://localhost:8002"
    
    if quiz_url:
        color_print(f"✅ QUIZ_SERVICE_URL: {quiz_url}", "green")
    else:
        color_print("⚠️  QUIZ_SERVICE_URL not set", "yellow")
    
    color_print(f"✅ USER_SERVICE_PORT: {user_port}", "green")
    
    return course_url

def check_service_health(url, service_name):
    color_print(f"\n🏥 Step 2: Checking {service_name} Health", "cyan")
    color_print("=" * 60, "cyan")
    
    try:
        health_url = f"{url}/health"
        color_print(f"Testing: {health_url}", "blue")
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            color_print(f"✅ {service_name} is UP and responding!", "green")
            return True
        else:
            color_print(f"⚠️  {service_name} responded with status {response.status_code}", "yellow")
            return False
    except requests.exceptions.ConnectionError:
        color_print(f"❌ Cannot connect to {service_name} at {url}", "red")
        color_print(f"   Is {service_name} running?", "yellow")
        return False
    except requests.exceptions.Timeout:
        color_print(f"❌ {service_name} timeout after 5 seconds", "red")
        return False
    except Exception as e:
        color_print(f"❌ Error checking {service_name}: {e}", "red")
        return False

def test_course_api(course_url):
    color_print(f"\n🧪 Step 3: Testing Course API (without auth)", "cyan")
    color_print("=" * 60, "cyan")
    
    try:
        api_url = f"{course_url}/api/course/all"
        color_print(f"Testing: {api_url}", "blue")
        response = requests.get(api_url, timeout=5)
        
        color_print(f"Status Code: {response.status_code}", "blue")
        
        if response.status_code == 401:
            color_print("✅ Got 401 - This is expected (authentication required)", "green")
            color_print("   Course API is working but needs valid JWT token", "green")
            return True
        elif response.status_code == 200:
            color_print("✅ Got 200 - API is accessible!", "green")
            try:
                data = response.json()
                courses = data.get("courses", [])
                color_print(f"   Found {len(courses)} courses in response", "green")
            except:
                pass
            return True
        else:
            color_print(f"⚠️  Unexpected status code: {response.status_code}", "yellow")
            color_print(f"   Response: {response.text[:200]}", "yellow")
            return False
            
    except requests.exceptions.ConnectionError:
        color_print(f"❌ Cannot connect to Course API", "red")
        return False
    except Exception as e:
        color_print(f"❌ Error: {e}", "red")
        return False

def check_docker_services():
    color_print(f"\n🐳 Step 4: Checking Docker Services", "cyan")
    color_print("=" * 60, "cyan")
    
    try:
        import subprocess
        result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'], 
                               capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            services = {}
            for line in lines:
                if '\t' in line:
                    name, status = line.split('\t', 1)
                    services[name] = status
            
            # Check for relevant services
            course_running = any('course-service' in name.lower() for name in services)
            user_running = any('user-service' in name.lower() for name in services)
            
            if course_running:
                color_print("✅ Course service container is running", "green")
            else:
                color_print("⚠️  Course service container not found", "yellow")
            
            if user_running:
                color_print("✅ User service container is running", "green")
            else:
                color_print("⚠️  User service container not found", "yellow")
            
            if services:
                color_print("\nRunning containers:", "blue")
                for name, status in services.items():
                    if any(s in name.lower() for s in ['course', 'user', 'quiz', 'auth']):
                        color_print(f"  • {name}: {status}", "green" if "Up" in status else "red")
        else:
            color_print("⚠️  Could not get Docker container status", "yellow")
            
    except FileNotFoundError:
        color_print("⚠️  Docker command not found (not using Docker?)", "yellow")
    except Exception as e:
        color_print(f"⚠️  Could not check Docker: {e}", "yellow")

def print_summary():
    color_print("\n📝 Summary & Next Steps", "cyan")
    color_print("=" * 60, "cyan")
    color_print("\n✅ If all checks passed:", "green")
    color_print("   The issue might be with authentication or user-specific data", "green")
    color_print("   Check the actual logs when making a dashboard request:", "green")
    color_print("   - docker logs pathlight-user-service -f | grep COURSE_CLIENT", "blue")
    color_print("   - Check browser console for frontend logs", "blue")
    
    color_print("\n❌ If checks failed:", "red")
    color_print("   1. Start the missing services", "yellow")
    color_print("   2. Verify COURSE_SERVICE_URL environment variable", "yellow")
    color_print("   3. Check network connectivity between services", "yellow")
    color_print("   4. Review troubleshooting guide: docs/TROUBLESHOOTING_COURSE_DATA.md", "yellow")
    
    color_print("\n📚 Additional Resources:", "magenta")
    color_print("   - Troubleshooting Guide: docs/TROUBLESHOOTING_COURSE_DATA.md", "blue")
    color_print("   - Test Script: ./test_dashboard_course_data.sh", "blue")

def main():
    color_print("\n" + "=" * 60, "magenta")
    color_print("🔍 Course Data Diagnostic Tool", "magenta")
    color_print("=" * 60 + "\n", "magenta")
    
    # Step 1: Check environment
    course_url = check_env_vars()
    
    # Step 2: Check service health
    course_healthy = check_service_health(course_url, "Course Service")
    
    # Step 3: Test API
    if course_healthy:
        test_course_api(course_url)
    
    # Step 4: Check Docker
    check_docker_services()
    
    # Summary
    print_summary()
    
    color_print("\n" + "=" * 60, "magenta")
    color_print("✨ Diagnostic Complete!", "magenta")
    color_print("=" * 60 + "\n", "magenta")

if __name__ == "__main__":
    main()
