import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { API_CONFIG } from '@/config/env';

/**
 * POST /api/users/experience/deduct
 * Deduct EXP from user (for power-ups)
 */
export async function POST(request: NextRequest) {
  try {
    const cookieStore = await cookies();
    const accessToken = cookieStore.get('session_token')?.value;

    if (!accessToken) {
      return NextResponse.json(
        { error: 'Unauthorized - No access token' },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { exp } = body;

    if (!exp || exp <= 0) {
      return NextResponse.json(
        { error: 'Invalid EXP amount' },
        { status: 400 }
      );
    }

    // Call user-service to deduct EXP
    const userServiceUrl = `${API_CONFIG.USER_SERVICE_URL}/user/experience/deduct`;
    
    const response = await fetch(userServiceUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ exp }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.message || 'Failed to deduct EXP' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error deducting EXP:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
