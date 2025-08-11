/**
 * =============================================================================
 * 📈 PATHLIGHT FRONTEND - USER ACTIVITY API ROUTES
 * =============================================================================
 * Next.js API routes for user activity tracking
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
  const userServiceUrl = `${API_CONFIG.USER_SERVICE_URL}/user${endpoint}`;
  
  console.log(`[USER ACTIVITY API] Proxying ${method} request to: ${userServiceUrl}`);

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
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }
  });
}

// =============================================================================
// 🌐 API ROUTE HANDLERS
// =============================================================================

/**
 * GET /api/user/activity
 * Get user activity data (no query params)
 */
export async function GET(request: NextRequest) {
  try {
    const headers = createProxyHeaders(request);
    const response = await proxyToUserService('/activity', 'GET', headers);
    return handleApiResponse(response);
  } catch (error) {
    console.error('[USER ACTIVITY API] GET error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/user/activity
 * Save user activity milestone or batch (when activityData is provided)
 */
export async function POST(request: NextRequest) {
  try {
    const headers = createProxyHeaders(request);
    const rawBody = await request.text();

    // Decide endpoint based on payload shape
    let endpoint = '/activity';
    try {
      if (rawBody) {
        const parsed = JSON.parse(rawBody) as Record<string, unknown>;
        if (parsed && typeof parsed === 'object' && parsed.activityData) {
          endpoint = '/activity/batch';
        }
      }
    } catch {
      // If body isn't JSON, default to single activity endpoint
    }

    const response = await proxyToUserService(endpoint, 'POST', headers, rawBody || undefined);
    return handleApiResponse(response);
  } catch (error) {
    console.error('[USER ACTIVITY API] POST error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/user/activity
 * Handle CORS preflight requests
 */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  });
}
