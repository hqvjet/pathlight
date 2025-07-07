import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// =============================================================================
// 🛡️ PATHLIGHT FRONTEND - MIDDLEWARE CONFIGURATION
// =============================================================================

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const url = request.nextUrl.clone();

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
  // 🔒 AUTHENTICATION CHECKS
  // =============================================================================
  
  // Get auth token from request
  const token = request.cookies.get('token')?.value || 
                request.headers.get('authorization')?.replace('Bearer ', '');

  // Protected routes that require authentication
  const protectedRoutes = [
    '/dashboard',
    '/profile',
    '/courses',
    '/quizzes',
    '/admin',
  ];

  // Public routes that should redirect authenticated users
  const publicRoutes = [
    '/signin',
    '/signup',
    '/forgot-password',
  ];

  const isProtectedRoute = protectedRoutes.some(route => 
    pathname.startsWith(route)
  );
  
  const isPublicRoute = publicRoutes.some(route => 
    pathname.startsWith(route)
  );

  // Redirect unauthenticated users from protected routes
  if (isProtectedRoute && !token) {
    url.pathname = '/signin';
    url.searchParams.set('redirect', pathname);
    return NextResponse.redirect(url);
  }

  // Redirect authenticated users from public auth routes
  if (isPublicRoute && token) {
    url.pathname = '/dashboard';
    return NextResponse.redirect(url);
  }

  // =============================================================================
  // 🌐 CORS HEADERS (for API routes)
  // =============================================================================
  
  if (pathname.startsWith('/')) {
    const response = NextResponse.next();
    
    // Add CORS headers for API routes
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
    '/reset-password/:token*',
    '/verify-email/:token*',
    
    // Match protected and public routes
    '/dashboard/:path*',
    '/profile/:path*',
    '/courses/:path*',
    '/quizzes/:path*',
    '/admin/:path*',
    '/:path*',
  ],
};
