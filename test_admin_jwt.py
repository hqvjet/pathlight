#!/usr/bin/env python3
"""Test script to decode and verify admin JWT token."""

import sys
from jose import jwt

# Token from the request
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3NmI4MGFmNC1mNzA1LTQzMDktYTUxNy0xN2Y3MzQ1OTUwYWYiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NjcwNjgwNzMsInR5cGUiOiJhY2Nlc3MiLCJpYXQiOjE3NjY5ODE2NzMsImp0aSI6ImU0OGIzOWE5LTFkZDctNGQ4Zi04YmQyLTUxMTZlMzAyNjMyYSJ9.AEb2n80qivLoo89DqC6OG2_DzYZ5JJhLzi4zkuj9IiU"

print("=" * 80)
print("JWT Token Analysis")
print("=" * 80)

# Decode without verification
try:
    claims = jwt.get_unverified_claims(token)
    print("\n✅ Unverified Claims:")
    for key, value in claims.items():
        print(f"  {key}: {value}")
    
    role = claims.get("role")
    roles = claims.get("roles", [])
    print(f"\n🔑 Role Check:")
    print(f"  role field: {role}")
    print(f"  roles field: {roles}")
    print(f"  Is admin: {role == 'admin' or 'admin' in roles}")
    
except Exception as e:
    print(f"\n❌ Error decoding token: {e}")
    sys.exit(1)

# Try to decode with verification (will fail without secret)
print(f"\n⚠️  Note: Signature verification requires JWT_SECRET_KEY")
print(f"   The token can still be used with unverified claims in the code.")

print("\n" + "=" * 80)
print("Recommendations:")
print("=" * 80)
print("1. Ensure Lambda environment has JWT_SECRET_KEY set")
print("2. Check CloudWatch logs for 'Admin guard:' messages")
print("3. Verify API Gateway is routing /api/course/admin/courses correctly")
print("4. Check CORS headers are properly configured")
print("=" * 80)
