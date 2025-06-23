import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const token = searchParams.get('token');
  
  if (!token) {
    // Nếu không có token, redirect về signin
    return NextResponse.redirect(new URL('/auth/signin', request.url));
  }
  
  // Redirect về trang frontend verify-email với token
  return NextResponse.redirect(new URL(`/auth/verify-email?token=${token}`, request.url));
}
