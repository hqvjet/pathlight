/**
 * =============================================================================
 * 👤 PATHLIGHT FRONTEND - USER API ROUTES
 * =============================================================================
 * Next.js API routes for user management - proxies to user service
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_CONFIG } from '@/config/env';

// =============================================================================
// 🔧 TYPES & INTERFACES
// =============================================================================

interface ProxyRequestConfig {
  method: string;
  headers: Record<string, string>;
  body?: string;
}

// =============================================================================
// 🛠️ UTILITY FUNCTIONS
// =============================================================================

/**
 * Create headers for proxying requests to backend service
 */
function createProxyHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Forward authorization header
  const authHeader = request.headers.get('authorization');
  if (authHeader) {
    headers.Authorization = authHeader;
  }

  // Forward other relevant headers
  const userAgent = request.headers.get('user-agent');
  if (userAgent) {
    headers['User-Agent'] = userAgent;
  }

  const xForwardedFor = request.headers.get('x-forwarded-for');
  if (xForwardedFor) {
    headers['X-Forwarded-For'] = xForwardedFor;
  }

  return headers;
}

/**
 * Proxy request to user service
 */
async function proxyToUserService(
  endpoint: string,
  config: ProxyRequestConfig
): Promise<Response> {
  const userServiceUrl = `${API_CONFIG.USER_SERVICE_URL}/users${endpoint}`;
  
  console.log(`[USER API] Proxying ${config.method} request to: ${userServiceUrl}`);

  try {
    const response = await fetch(userServiceUrl, {
      method: config.method,
      headers: config.headers,
      body: config.body,
    });

    return response;
  } catch (error) {
    console.error('[USER API] Proxy error:', error);
    throw new Error('Failed to proxy request to user service');
  }
}

/**
 * Handle API response and convert to NextResponse
 */
async function handleApiResponse(response: Response): Promise<NextResponse> {
  const contentType = response.headers.get('content-type');
  
  // Handle different content types
  if (contentType?.includes('application/json')) {
    try {
      const data = await response.json();
      return NextResponse.json(data, { 
        status: response.status,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }
      });
    } catch (error) {
      console.error('[USER API] Failed to parse JSON response:', error);
      return NextResponse.json(
        { error: 'Failed to parse response' },
        { status: 500 }
      );
    }
  }

  // Handle non-JSON responses (like file downloads)
  const arrayBuffer = await response.arrayBuffer();
  return new NextResponse(arrayBuffer, {
    status: response.status,
    headers: {
      'Content-Type': contentType || 'application/octet-stream',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}

// =============================================================================
// 🌐 API ROUTE HANDLERS
// =============================================================================

/**
 * GET /api/users
 * Get all users (admin only) or user list endpoints
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const endpoint = searchParams.size > 0 ? `/all?${searchParams.toString()}` : '/all';
    
    const headers = createProxyHeaders(request);
    
    const response = await proxyToUserService(endpoint, {
      method: 'GET',
      headers,
    });

    return handleApiResponse(response);
  } catch (error) {
    console.error('[USER API] GET error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/users
 * Handle POST requests (like users-by-ids)
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.text();
    const headers = createProxyHeaders(request);

    // Default to users-by-ids endpoint for POST requests to /api/users
    const response = await proxyToUserService('/users-by-ids', {
      method: 'POST',
      headers,
      body,
    });

    return handleApiResponse(response);
  } catch (error) {
    console.error('[USER API] POST error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/users
 * Handle CORS preflight requests
 */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  });
}
