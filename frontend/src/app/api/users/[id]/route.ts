/**
 * =============================================================================
 * 👤 PATHLIGHT FRONTEND - INDIVIDUAL USER API ROUTES
 * =============================================================================
 * Next.js API routes for individual user operations (admin)
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
  
  console.log(`[USER ID API] Proxying ${method} request to: ${userServiceUrl}`);

  return fetch(userServiceUrl, {
    method,
    headers,
    body,
  });
}

async function handleApiResponse(response: Response): Promise<NextResponse> {
  const data = await response.json();
  return NextResponse.json(data, { 
    status: response.status,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }
  });
}

// =============================================================================
// 🌐 API ROUTE HANDLERS
// =============================================================================

/**
 * GET /api/users/[id]
 * Get specific user by ID (admin only)
 */
export async function GET(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const headers = createProxyHeaders(request);
    
    // For individual user info, use the /info endpoint with id parameter
    const response = await proxyToUserService(`/info?id=${params.id}`, 'GET', headers);
    return handleApiResponse(response);
  } catch (error) {
    console.error('[USER ID API] GET error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * PUT /api/users/[id]
 * Update specific user by ID (admin only)
 */
export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const body = await request.text();
    const headers = createProxyHeaders(request);

    // Note: This would need a corresponding admin endpoint in the user service
    const response = await proxyToUserService(`/${params.id}`, 'PUT', headers, body);
    return handleApiResponse(response);
  } catch (error) {
    console.error('[USER ID API] PUT error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/users/[id]
 * Delete specific user by ID (admin only)
 */
export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const headers = createProxyHeaders(request);

    // Note: This would need a corresponding admin endpoint in the user service
    const response = await proxyToUserService(`/${params.id}`, 'DELETE', headers);
    return handleApiResponse(response);
  } catch (error) {
    console.error('[USER ID API] DELETE error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/users/[id]
 * Handle CORS preflight requests
 */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  });
}
