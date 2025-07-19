import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const token = searchParams.get('token');
  
  if (!token) {
    // Nếu không có token, redirect về signin với lỗi
    return NextResponse.redirect(new URL('/auth/signin?error=missing_token', request.url));
  }

  try {
    // Gọi trực tiếp backend để verify email
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const response = await fetch(`${backendUrl}/verify-email?token=${token}`, {
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
