import type { NextConfig } from 'next'

/**
 * Next.js configuration (tested with v15.x)
 * -----------------------------------------------------------------------------
 * – Switched from deprecated `images.domains` to `images.remotePatterns`.
 * – Removed the unsupported `turbo` key that caused the “Unrecognized key” error.
 * – Left a commented `turbopack` section in case you want to experiment later.
 * – Added safe defaults for image security, headers, rewrites, and live‑reload in Docker.
 */
const nextConfig: NextConfig = {
  // ---------------------------------------------------------------------------
  // 🌍  Public environment variables (exposed on the client)
  // ---------------------------------------------------------------------------
  env: {
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,
    NEXT_PUBLIC_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION,
    NEXT_PUBLIC_ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT,
  },

  // ---------------------------------------------------------------------------
  // 🖼️  Image optimisation
  // ---------------------------------------------------------------------------
  images: {
    formats: ['image/avif', 'image/webp'],
    dangerouslyAllowSVG: true,
    contentDispositionType: 'attachment',
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
    remotePatterns: [
      { protocol: 'https', hostname: 'xmicux090i.execute-api.ap-northeast-1.amazonaws.com', pathname: '/**' },
      { protocol: 'https', hostname: 'pathlight-user.s3.ap-northeast-1.amazonaws.com', pathname: '/**' }, // S3 bucket for avatars
      { protocol: 'http', hostname: 'localhost', port: '8001', pathname: '/**' }, // auth-service
      { protocol: 'http', hostname: 'localhost', port: '8002', pathname: '/**' }, // user-service
      { protocol: 'http', hostname: 'localhost', port: '8003', pathname: '/**' }, // course-service
      { protocol: 'http', hostname: 'localhost', port: '8004', pathname: '/**' }, // quiz-service
      { protocol: 'http', hostname: 'localhost', port: '8005', pathname: '/**' }, // agentic-service
      { protocol: 'http', hostname: 'localhost', port: '', pathname: '/**' },
      { protocol: 'http', hostname: '127.0.0.1', port: '', pathname: '/**' },
      { protocol: 'https', hostname: 'lh3.googleusercontent.com', pathname: '/**' },
      // Example production host:
      // { protocol: 'https', hostname: 'cdn.example.com', pathname: '/**' },
    ],
  },

  // ---------------------------------------------------------------------------
  // 🔄  Redirects & Rewrites
  // ---------------------------------------------------------------------------
  async redirects() {
    return [
      { source: '/login',    destination: '/signin', permanent: true },
      { source: '/register', destination: '/signup', permanent: true },
    ]
  },

  async rewrites() {
    // In development, don't proxy to AWS - let the frontend handle API routing to individual services
    if (process.env.NODE_ENV === 'development') {
      return []
    }
    
    return [
      // API routes proxy to backend (production only)
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL || 'https://xmicux090i.execute-api.ap-northeast-1.amazonaws.com/api'}/:path*`,
      },
    ]
  },

  // ---------------------------------------------------------------------------
  // 🛡️  Security headers
  // ---------------------------------------------------------------------------
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options',       value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy',        value: 'origin-when-cross-origin' },
        ],
      },
    ]
  },

  // ---------------------------------------------------------------------------
  // ⚙️  Webpack tweaks (watch mode friendly for Docker/WSL)
  // ---------------------------------------------------------------------------
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      }
    }
    return config
  },
}

export default nextConfig
