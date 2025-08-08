/**
 * =============================================================================
 * 🖼️ PATHLIGHT FRONTEND - USER AVATAR API ROUTES
 * =============================================================================
 * Next.js API routes for user avatar management
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_CONFIG } from '@/config/env';

// =============================================================================
// 🛠️ UTILITY FUNCTIONS
// =============================================================================

function createProxyHeaders(request: NextRequest, isFormData: boolean = false): Record<string, string> {
  const headers: Record<string, string> = {};

  // Only set Content-Type for JSON requests, let browser set it for FormData
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }

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
  body?: string | FormData
): Promise<Response> {
  const userServiceUrl = `${API_CONFIG.USER_SERVICE_URL}/users${endpoint}`;
  
  console.log(`[USER AVATAR API] Proxying ${method} request to: ${userServiceUrl}`);

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
        'Access-Control-Allow-Methods': 'GET, PUT, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      }
    });
  }

  // Handle binary responses (like images)
  const arrayBuffer = await response.arrayBuffer();
  return new NextResponse(arrayBuffer, {
    status: response.status,
    headers: {
      'Content-Type': contentType || 'application/octet-stream',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'public, max-age=31536000', // Cache avatars for 1 year
    },
  });
}

// =============================================================================
// 🌐 API ROUTE HANDLERS
// =============================================================================

/**
 * GET /api/users/avatar
 * Get user avatar by user_id or avatar_id query parameter
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('user_id');
    const avatarId = searchParams.get('avatar_id');
    
    if (!userId && !avatarId) {
      return NextResponse.json(
        { error: 'Either user_id or avatar_id must be provided' },
        { status: 400 }
      );
    }

    const headers = createProxyHeaders(request);
    const queryString = searchParams.toString();
    
    const response = await proxyToUserService(`/avatar/?${queryString}`, 'GET', headers);
    return handleApiResponse(response);
  } catch (error) {
    console.error('[USER AVATAR API] GET error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * PUT /api/users/avatar
 * Upload/update user avatar
 */
export async function PUT(request: NextRequest) {
  try {
    const formData = await request.formData();
    const headers = createProxyHeaders(request, true);

    const response = await proxyToUserService('/avatar', 'PUT', headers, formData);
    return handleApiResponse(response);
  } catch (error) {
    console.error('[USER AVATAR API] PUT error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/users/avatar
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
