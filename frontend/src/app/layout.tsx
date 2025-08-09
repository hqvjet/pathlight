import type { Metadata } from "next";
import { Montserrat } from 'next/font/google';
import "./globals.css";
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import CookieWarning from '@/components/common/CookieWarning';

const montserrat = Montserrat({
  subsets: ['latin'],
  variable: '--font-montserrat',
  display: 'swap',
});

export const metadata: Metadata = {
  title: {
    default: 'PathLight',
    template: '%s | PathLight'
  },
  description: 'Nền tảng AI dẫn lối tự học cá nhân hóa',
  icons: {
    icon: '/assets/icons/logo.png',
    shortcut: '/assets/icons/logo.png',
    apple: '/assets/icons/logo.png'
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
        <CookieWarning />
        {children}
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
