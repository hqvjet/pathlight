import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ token: string }> }
) {
  const { token } = await params;
  
  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>Đặt lại mật khẩu - PathLight</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script>window.location.href = '/auth/reset-password/${token}';</script>
      </head>
      <body>
        <div style="display: flex; justify-content: center; align-items: center; min-height: 100vh; font-family: Arial, sans-serif;">
          <div style="text-align: center;">
            <h2>Đang chuyển hướng...</h2>
            <p>Nếu không được chuyển hướng tự động, <a href="/auth/reset-password/${token}">nhấp vào đây</a>.</p>
          </div>
        </div>
      </body>
    </html>
  `;
  
  return new NextResponse(html, {
    headers: { 'Content-Type': 'text/html' },
  });
}
