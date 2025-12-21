import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// =============================================================================
// 🛡️ PATHLIGHT FRONTEND - MIDDLEWARE CONFIGURATION
// =============================================================================

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const url = request.nextUrl.clone();

  if (pathname === '/signin') { url.pathname = '/auth/signin'; return NextResponse.redirect(url); }

  // =============================================================================
  // 🔄 API REDIRECTS
  // =============================================================================
  
  // Handle reset password redirects from backend
  if (pathname.startsWith('/reset-password/')) {
    const token = pathname.split('/reset-password/')[1];
    if (token && token.length > 0) {
      // Redirect to the frontend reset password page
      url.pathname = `/reset-password/${token}`;
      return NextResponse.redirect(url);
    }
  }

  // Handle email verification redirects from backend
  if (pathname.startsWith('/verify-email/')) {
    const token = pathname.split('/verify-email/')[1];
    if (token && token.length > 0) {
      // Redirect to the frontend email verification page
      url.pathname = `/verify-email/${token}`;
      return NextResponse.redirect(url);
    }
  }

  // =============================================================================
  // 🔒 AUTHENTICATION CHECKS (ENHANCED COOKIE SUPPORT)
  // =============================================================================
  
  // Get auth token from cookies (prioritize persistent, then session)
  let authToken = request.cookies.get('auth_token')?.value || 
                   request.cookies.get('session_token')?.value ||
                   request.headers.get('authorization')?.replace('Bearer ', '');

  // Helper: check JWT expiry (gracefully handles non-JWT tokens)
  const isTokenExpired = (token?: string | null): boolean => {
    if (!token || token.split('.').length !== 3) return false;
    try {
      const base64 = token.split('.')[1].replace(/-/g,'+').replace(/_/g,'/');
      const json = JSON.parse(atob(base64));
      if (!json.exp) return false;
      return json.exp * 1000 < Date.now();
    } catch { return false; }
  };

  const tokenExpired = isTokenExpired(authToken);

  // If token expired, prepare to clear it and treat as unauthenticated
  let clearExpiredCookiesResponse: NextResponse | null = null;
  if (authToken && tokenExpired) {
    authToken = null; // treat as unauthenticated below
    clearExpiredCookiesResponse = NextResponse.next();
    clearExpiredCookiesResponse.cookies.set('auth_token','',{maxAge:0,path:'/'});
    clearExpiredCookiesResponse.cookies.set('session_token','',{maxAge:0,path:'/'});
    clearExpiredCookiesResponse.cookies.set('remember_me','',{maxAge:0,path:'/'});
  }

  // Global guard: everything requires auth except home and auth/reset flows
  const isHome = pathname === '/' || pathname === '';
  const isAuthFlow = pathname.startsWith('/auth');
  const isResetFlow = pathname.startsWith('/reset-password') || pathname.startsWith('/verify-email');
  const isPublicRoute = isHome || isAuthFlow || isResetFlow;

  if (!isPublicRoute && !authToken) {
    url.pathname = '/auth/signin';
    url.searchParams.set('redirect', pathname);
    const resp = NextResponse.redirect(url);
    if (clearExpiredCookiesResponse) {
      resp.cookies.set('auth_token','',{maxAge:0,path:'/'});
      resp.cookies.set('session_token','',{maxAge:0,path:'/'});
      resp.cookies.set('remember_me','',{maxAge:0,path:'/'});
    }
    return resp;
  }

  // Redirect authenticated users away from public auth screens (but keep redirect intent)
  if (isAuthFlow && authToken) {
    const hasRedirectBack = request.nextUrl.searchParams.get('redirect');
    if (!hasRedirectBack) {
      url.pathname = '/user/dashboard';
      return NextResponse.redirect(url);
    }
  }

  // Continue with (possible) cookie clearing if token expired but route is public (e.g. /auth/signin)
  if (clearExpiredCookiesResponse) return clearExpiredCookiesResponse;

  // =============================================================================
  // 🌐 CORS HEADERS (for API routes)
  // =============================================================================
  
  if (pathname.startsWith('/')) {
    const response = NextResponse.next();
    response.headers.set('Access-Control-Allow-Origin', '*');
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    return response;
  }

  // =============================================================================
  // 📱 MOBILE/DEVICE DETECTION
  // =============================================================================
  
  const userAgent = request.headers.get('user-agent') || '';
  const isMobile = /Android|BlackBerry|iPhone|iPad|iPod|Opera Mini|IEMobile|WPDesktop/i.test(userAgent);
  
  // Add device info to headers for components to use
  const response = NextResponse.next();
  response.headers.set('x-device-type', isMobile ? 'mobile' : 'desktop');
  
  return response;
}

// =============================================================================
// ⚙️ MIDDLEWARE CONFIGURATION
// =============================================================================

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder files
     */
    '/((?!_next/static|_next/image|favicon.ico|public|assets).*)',
    
    // Specifically match API routes and auth redirects
    '/auth/reset-password/:token*',
    '/auth/verify-email/:token*',
    
    // Match protected and public routes
    '/user/dashboard/:path*',
    '/user/profile/:path*',
    '/courses/:path*',
    '/quizzes/:path*',
    '/admin/:path*',
    '/auth/:path*',
    '/:path*',
  ],
};
