import type { NextConfig } from 'next';

/**
 * Next.js configuration (Next.js 14+)
 * - Updated to use `serverExternalPackages` (stable) instead of the removed `experimental.serverComponentsExternalPackages`.
 * - Replaced deprecated `images.domains` with `images.remotePatterns`.
 * - Added `turbo: false` to silence Turbopack warnings until you migrate.
 */
const nextConfig: NextConfig = {
  // =============================================================================
  // 🌍 ENVIRONMENT VARIABLES
  // =============================================================================
  env: {
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,
    NEXT_PUBLIC_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION,
    NEXT_PUBLIC_ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT,
  },

  // =============================================================================
  // 🖼️ IMAGE OPTIMIZATION
  // =============================================================================
  images: {
    formats: ['image/webp', 'image/avif'],
    dangerouslyAllowSVG: true,
    contentDispositionType: 'attachment',
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
    /**
     * `domains` is deprecated since v14 — switch to `remotePatterns`.
     * Add any additional production domains or CDN hosts below.
     */
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        pathname: '/**',
      },
      {
        protocol: 'http',
        hostname: '127.0.0.1',
        pathname: '/**',
      },
      // Example production host:
      // {
      //   protocol: 'https',
      //   hostname: 'cdn.example.com',
      //   pathname: '/**',
      // },
    ],
  },

  // =============================================================================
  // 🔄 REDIRECTS & REWRITES
  // =============================================================================
  async redirects() {
    return [
      { source: '/login', destination: '/auth/signin', permanent: true },
      { source: '/register', destination: '/auth/signup', permanent: true },
    ];
  },

  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/:path*`,
      },
    ];
  },

  // =============================================================================
  // 🔧 BUILD CONFIGURATION
  // =============================================================================
  /**
   * Stable since v15.0.0 — list packages that rely on Node APIs so they
   * are excluded from the Server Components bundle. Replace the placeholder
   * with actual deps (e.g. 'bcrypt', 'sharp', '@prisma/client', ...).
   */
  serverExternalPackages: ['bcrypt', 'sharp', '@prisma/client'],

  /**
   * Disable Turbopack until you intentionally migrate (suppresses warnings).
   */
  turbo: false,

  /**
   * Enable standalone output for Docker production builds
   */
  output: 'standalone',

  // =============================================================================
  // 🛡️ SECURITY HEADERS
  // =============================================================================
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'origin-when-cross-origin' },
        ],
      },
    ];
  },

  // =============================================================================
  // 📦 WEBPACK CONFIGURATION
  // =============================================================================
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      } as any;
    }
    return config;
  },
};

export default nextConfig;
