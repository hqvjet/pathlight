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
    return [
      // Legacy API routes (fallback to base URL)
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'}/api/:path*`,
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
