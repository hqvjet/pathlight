'use client';

import Image from 'next/image';
import Link from 'next/link';
import Header from './Header';

interface ErrorPageProps {
  errorCode?: string;
  title?: string;
  subtitle?: string;
  buttonText?: string;
  buttonLink?: string;
}

export default function ErrorPage({
  errorCode = "404",
  title = "Ôi không! Có vẻ bạn đang bị lạc đường",
  subtitle = "",
  buttonText = "Trở Về Trang Chính",
  buttonLink = "/"
}: ErrorPageProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <Header 
        variant="auth" 
        showSocialLinks={true}
        backgroundColor="transparent"
      />

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-4 py-16">
        <div className="max-w-6xl w-full flex flex-col lg:flex-row items-center justify-between">
          {/* Left Side - Text Content */}
          <div className="flex-1 text-center lg:text-left mb-12 lg:mb-0 lg:pr-12">
            <h1 className="text-6xl lg:text-8xl font-light text-gray-300 mb-4">
              Error {errorCode}
            </h1>
            <h2 className="text-2xl lg:text-3xl font-bold text-gray-800 mb-6">
              {title}
            </h2>
            {subtitle && (
              <p className="text-lg text-gray-600 mb-8">
                {subtitle}
              </p>
            )}
            <Link 
              href={buttonLink}
              className="inline-block bg-orange-500 hover:bg-orange-600 text-white font-semibold px-8 py-3 rounded-lg transition-colors duration-200 transform hover:scale-105"
            >
              {buttonText}
            </Link>
          </div>

          {/* Right Side - Error Illustration */}
          <div className="flex-1 relative flex items-center justify-center">
            <div className="relative max-w-md w-full">
              {/* Error Image */}
              <div className="relative animate-float">
                <Image 
                  src="/assets/images/error_page.png" 
                  alt="Error page illustration" 
                  width={400} 
                  height={400} 
                  className="w-full h-auto drop-shadow-lg"
                  priority
                />
              </div>
              
              {/* Floating decorative elements */}
              <div className="absolute -top-4 -left-4 text-2xl animate-pulse">❓</div>
              <div className="absolute top-8 -right-6 text-xl animate-pulse delay-300">😕</div>
              <div className="absolute -bottom-4 left-8 text-lg animate-pulse delay-500">💭</div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center space-x-6 text-sm text-gray-500">
            <Link href="/faqs" className="hover:text-gray-700 transition-colors">FAQs</Link>
            <Link href="/privacy" className="hover:text-gray-700 transition-colors">Privacy Policy</Link>
            <Link href="/terms" className="hover:text-gray-700 transition-colors">Terms & Condition</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
