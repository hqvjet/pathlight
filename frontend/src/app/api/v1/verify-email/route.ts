import { NextRequest, NextResponse } from 'next/server';
import { API_CONFIG } from '@/config/env';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const token = searchParams.get('token');
  
  if (!token) {
    // Nếu không có token, redirect về signin với lỗi
    return NextResponse.redirect(new URL('/auth/signin?error=missing_token', request.url));
  }

  try {
    // Gọi trực tiếp backend để verify email
  // Always use unified backend base URL (no localhost fallback)
  const base = API_CONFIG.BASE_URL.replace(/\/$/, '');
  // Avoid double /api when BASE_URL already ends with /api
  const verifyPath = base.match(/\/api$/) ? '/verify-email' : '/api/verify-email';
  const response = await fetch(`${base}${verifyPath}?token=${token}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const result = await response.json();

    if (response.ok && result.status === 200) {
      // Verify thành công, redirect về signin với thông báo thành công
      return NextResponse.redirect(new URL('/auth/signin?verified=true', request.url));
    } else {
      // Verify thất bại, redirect về signin với thông báo lỗi
      return NextResponse.redirect(new URL('/auth/signin?error=invalid_token', request.url));
    }
  } catch (error) {
    console.error('Error verifying email:', error);
    // Lỗi server, redirect về signin với thông báo lỗi
    return NextResponse.redirect(new URL('/auth/signin?error=server_error', request.url));
  }
}
