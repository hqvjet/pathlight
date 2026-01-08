/**
 * =============================================================================
 * ℹ️ PATHLIGHT FRONTEND - USER INFO API ROUTES
 * =============================================================================
 * Next.js API routes for user information retrieval
 */

import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { API_CONFIG } from '@/config/env';

// =============================================================================
// 🛠️ UTILITY FUNCTIONS
// =============================================================================

function createProxyHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // First try Authorization header (for direct API calls)
  const authHeader = request.headers.get('authorization');
  if (authHeader) {
    headers.Authorization = authHeader;
  }

  return headers;
}

async function proxyToUserService(
  endpoint: string,
  method: string,
  headers: Record<string, string>,
  accessToken?: string
): Promise<Response> {
  const userServiceUrl = `${API_CONFIG.USER_SERVICE_URL}/user${endpoint}`;
  
  // Use access_token from cookies if available
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }
  
  console.log(`[USER INFO API] Proxying ${method} request to: ${userServiceUrl}`);

  return fetch(userServiceUrl, {
    method,
    headers,
  });
}

async function handleApiResponse(response: Response): Promise<NextResponse> {
  const data = await response.json();
  return NextResponse.json(data, { 
    status: response.status,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }
  });
}

// =============================================================================
// 🌐 API ROUTE HANDLERS
// =============================================================================

/**
 * GET /api/user/info
 * Get user information (no query params)
 */
export async function GET(request: NextRequest) {
  try {
    // Get access token from cookies
    const cookieStore = await cookies();
    const accessToken = cookieStore.get('session_token')?.value;

    if (!accessToken) {
      return NextResponse.json(
        { error: 'Unauthorized - No access token' },
        { status: 401 }
      );
    }

    const headers = createProxyHeaders(request);
    const response = await proxyToUserService('/info', 'GET', headers, accessToken);
    return handleApiResponse(response);
  } catch (error) {
    console.error('[USER INFO API] GET error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/user/info
 * Handle CORS preflight requests
 */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  });
}
