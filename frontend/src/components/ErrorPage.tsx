'use client';

import Image from 'next/image';
import Link from 'next/link';

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
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Image 
                src="/assets/icons/LOGO.svg" 
                alt="PathLive logo" 
                width={120} 
                height={32} 
                className="h-8 w-auto" 
              />
            </div>
            
            {/* Social Media Icons */}
            <div className="flex items-center space-x-4">
              <a href="#" className="text-gray-400 hover:text-gray-600 transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-gray-600 transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-gray-600 transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12.046 0C5.374 0 0 5.373 0 12s5.374 12 12.046 12S24 18.627 24 12S18.627 0 12.046 0zM12.046 2.182c5.423 0 9.818 4.395 9.818 9.818s-4.395 9.818-9.818 9.818S2.228 17.423 2.228 12S6.623 2.182 12.046 2.182zM12.046 14.5c-1.381 0-2.5-1.119-2.5-2.5s1.119-2.5 2.5-2.5s2.5 1.119 2.5 2.5S13.427 14.5 12.046 14.5z"/>
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-gray-600 transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M22.46 6c-.77.35-1.6.58-2.46.69.88-.53 1.56-1.37 1.88-2.38-.83.5-1.75.85-2.72 1.05C18.37 4.5 17.26 4 16 4c-2.35 0-4.27 1.92-4.27 4.29 0 .34.04.67.11.98C8.28 9.09 5.11 7.38 3 4.79c-.37.63-.58 1.37-.58 2.15 0 1.49.75 2.81 1.91 3.56-.71 0-1.37-.2-1.95-.5v.03c0 2.08 1.48 3.82 3.44 4.21a4.22 4.22 0 0 1-1.93.07 4.28 4.28 0 0 0 4 2.98 8.521 8.521 0 0 1-5.33 1.84c-.34 0-.68-.02-1.02-.06C3.44 20.29 5.7 21 8.12 21 16 21 20.33 14.46 20.33 8.79c0-.19 0-.37-.01-.56.84-.6 1.56-1.36 2.14-2.23z"/>
                </svg>
              </a>
            </div>
          </div>
        </div>
      </header>

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
