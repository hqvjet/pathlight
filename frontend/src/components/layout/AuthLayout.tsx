'use client';

import Image from 'next/image';
import { ReactNode } from 'react';
import Header from './Header';
import { Montserrat } from 'next/font/google';

const montserrat = Montserrat({
  subsets: ['latin', 'vietnamese'],
  display: 'swap',
});

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  imageSrc: string;
  imageAlt: string;
  children: ReactNode;
  headerVariant?: 'default' | 'auth' | 'minimal';
  showSocialLinks?: boolean;
}

export default function AuthLayout({ 
  title, 
  subtitle, 
  imageSrc,
  imageAlt,
  children,
  headerVariant = 'auth',
  showSocialLinks = true
}: AuthLayoutProps) {
  return (
    <div className={`h-screen bg-white flex flex-col overflow-hidden ${montserrat.className}`}>
      {/* Header */}
      <Header 
        variant={headerVariant} 
        showSocialLinks={showSocialLinks}
        backgroundColor="white"
      />

      {/* Main Content */}
      <div className="flex flex-1 h-[calc(100vh-80px)]">
        {/* Left side - Image */}
        <div className="hidden lg:flex lg:w-1/2 items-center justify-center p-4 xl:p-6 bg-gray-50">
          <div className="w-full max-w-3xl">
            <Image
              src={imageSrc}
              alt={imageAlt}
              width={800}
              height={650}
              className="w-full h-auto object-contain"
              priority
            />
          </div>
        </div>

        {/* Right side - Content */}
        <div className="w-full lg:w-1/2 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-4 bg-white">
          <div className="w-full max-w-lg space-y-8">
            {/* Title and Subtitle */}
            <div className="text-center space-y-4">
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
                {title}
              </h1>
              <p className="text-gray-600 text-lg sm:text-xl">
                {subtitle}
              </p>
            </div>

            {/* Children content (forms, buttons, etc.) */}
            <div className="space-y-8">
              {children}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
