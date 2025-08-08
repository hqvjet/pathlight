/**
 * =============================================================================
 * ℹ️ PATHLIGHT FRONTEND - USER INFO API ROUTES
 * =============================================================================
 * Next.js API routes for user information retrieval
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_CONFIG } from '@/config/env';

// =============================================================================
// 🛠️ UTILITY FUNCTIONS
// =============================================================================

function createProxyHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const authHeader = request.headers.get('authorization');
  if (authHeader) {
    headers.Authorization = authHeader;
  }

  return headers;
}

async function proxyToUserService(
  endpoint: string,
  method: string,
  headers: Record<string, string>
): Promise<Response> {
  const userServiceUrl = `${API_CONFIG.USER_SERVICE_URL}/users${endpoint}`;
  
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
 * GET /api/users/info
 * Get user information (with optional id parameter for specific user)
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    
    const headers = createProxyHeaders(request);
    const endpoint = id ? `/info?id=${id}` : '/info';
    
    const response = await proxyToUserService(endpoint, 'GET', headers);
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
 * OPTIONS /api/users/info
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
