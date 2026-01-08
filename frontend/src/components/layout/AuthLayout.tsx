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
    <div className={`min-h-screen bg-white flex flex-col overflow-hidden ${montserrat.className}`}>
      {/* Header */}
      <Header 
        variant={headerVariant} 
        showSocialLinks={showSocialLinks}
        backgroundColor="white"
      />

      {/* Main Content */}
      <div className="flex-1 flex justify-center items-start px-4 sm:px-6 lg:px-10 pb-8 pt-2 sm:pt-8 lg:pt-20">
        <div className="w-full max-w-6xl flex flex-col lg:flex-row items-start lg:items-center gap-4 sm:gap-6 lg:gap-12">
          {/* Left side - Image */}
          <div className="hidden lg:flex lg:w-[48%] items-center justify-center bg-gray-50 rounded-2xl p-4 xl:p-6">
            <div className="w-full max-w-2xl">
              <Image
                src={imageSrc}
                alt={imageAlt}
                width={720}
                height={560}
                className="w-full h-auto max-h-[520px] object-contain"
                priority
              />
            </div>
          </div>

          {/* Right side - Content */}
          <div className="w-full lg:w-[52%] flex items-start lg:items-center justify-center">
            <div className="w-full max-w-lg space-y-4 sm:space-y-6">
              {/* Title and Subtitle */}
            <div className="text-center space-y-1.5 sm:space-y-2">
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 leading-tight">
                {title}
              </h1>
              <p className="text-gray-600 text-sm sm:text-base lg:text-lg leading-relaxed">
                {subtitle}
              </p>
            </div>

              {/* Children content (forms, buttons, etc.) */}
              <div className="space-y-6 sm:space-y-8">
                {children}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
