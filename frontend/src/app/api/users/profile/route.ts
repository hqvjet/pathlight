/**
 * =============================================================================
 * 👤 PATHLIGHT FRONTEND - USER PROFILE API ROUTES
 * =============================================================================
 * Next.js API routes for user profile management
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
  headers: Record<string, string>,
  body?: string
): Promise<Response> {
  const userServiceUrl = `${API_CONFIG.USER_SERVICE_URL}/users${endpoint}`;
  
  console.log(`[USER PROFILE API] Proxying ${method} request to: ${userServiceUrl}`);

  return fetch(userServiceUrl, {
    method,
    headers,
    body,
  });
}

async function handleApiResponse(response: Response): Promise<NextResponse> {
  const contentType = response.headers.get('content-type');
  
  if (contentType?.includes('application/json')) {
    const data = await response.json();
    return NextResponse.json(data, { 
      status: response.status,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      }
    });
  }

  const arrayBuffer = await response.arrayBuffer();
  return new NextResponse(arrayBuffer, {
    status: response.status,
    headers: {
      'Content-Type': contentType || 'application/octet-stream',
      'Access-Control-Allow-Origin': '*',
    },
  });
}

// =============================================================================
// 🌐 API ROUTE HANDLERS
// =============================================================================

/**
 * GET /api/users/profile
 * Get current user profile
 */
export async function GET(request: NextRequest) {
  try {
    const headers = createProxyHeaders(request);
    
    const response = await proxyToUserService('/profile', 'GET', headers);
    return handleApiResponse(response);
  } catch (error) {
    console.error('[USER PROFILE API] GET error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * PUT /api/users/profile
 * Update user profile (change-info endpoint)
 */
export async function PUT(request: NextRequest) {
  try {
    const body = await request.text();
    const headers = createProxyHeaders(request);

    const response = await proxyToUserService('/change-info', 'PUT', headers, body);
    return handleApiResponse(response);
  } catch (error) {
    console.error('[USER PROFILE API] PUT error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/users/profile
 * Handle CORS preflight requests
 */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, PUT, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  });
}
