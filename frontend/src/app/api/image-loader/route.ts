import { NextRequest, NextResponse } from 'next/server';

// Simple passthrough for images with cache headers
export async function GET(req: NextRequest) {
  try {
    const url = req.nextUrl.searchParams.get('url');
    if (!url) return NextResponse.json({ error: 'Missing url' }, { status: 400 });
    const res = await fetch(url, { cache: 'no-store' });
    const contentType = res.headers.get('content-type') || 'application/octet-stream';
    const buf = await res.arrayBuffer();
    return new NextResponse(buf, {
      status: res.status,
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=86400',
        'Access-Control-Allow-Origin': '*',
      },
    });
  } catch {
    return NextResponse.json({ error: 'Failed to load image' }, { status: 502 });
  }
}
