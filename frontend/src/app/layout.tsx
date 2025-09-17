import type { Metadata } from "next";
import { Montserrat } from 'next/font/google';
import "./globals.css";
import "./global-nav.css";
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import CookieWarning from '@/components/common/CookieWarning';
import React from 'react';
import GlobalNavWrapper from '@/components/layout/GlobalNavWrapper';
import { AuthProvider } from '@/context/AuthContext';

const montserrat = Montserrat({
  subsets: ['latin'],
  variable: '--font-montserrat',
  display: 'swap',
});

export const metadata: Metadata = {
  // Used to resolve absolute URLs for Open Graph/Twitter images and links
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
  title: {
    default: 'PathLight',
    template: '%s | PathLight'
  },
  description: 'Nền tảng AI dẫn lối tự học cá nhân hóa',
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/assets/icons/logo.png?v=1', type: 'image/png' }
    ],
    apple: [
      { url: '/assets/icons/logo.png?v=1' }
    ],
    shortcut: ['/favicon.ico']
  },
  openGraph: {
    title: 'PathLight',
    description: 'Nền tảng AI dẫn lối tự học cá nhân hóa',
    siteName: 'PathLight',
    images: [
      {
        url: '/assets/icons/logo.png',
        width: 120,
        height: 32,
        alt: 'PathLight'
      }
    ],
    type: 'website',
    locale: 'vi_VN'
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${montserrat.variable} font-sans antialiased`}
      >        
        <AuthProvider>
          <CookieWarning />
          <GlobalNavWrapper />
          <div className="pt-[var(--global-nav-offset,0px)]">
            {children}
          </div>
        </AuthProvider>
        <ToastContainer
          position="top-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
          theme="light"
        />
      </body>
    </html>
  );
}
