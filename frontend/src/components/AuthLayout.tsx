'use client';

import Image from 'next/image';
import { ReactNode } from 'react';
import Header from './Header';

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
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <Header 
        variant={headerVariant} 
        showSocialLinks={showSocialLinks}
        backgroundColor="transparent"
      />

      {/* Main Content */}
      <div className="flex-1 flex pt-20">
        {/* Left side - Image */}
        <div className="hidden lg:flex flex-1 items-center justify-center p-8 bg-gradient-to-br from-orange-50 to-orange-100">
          <div className="max-w-lg w-full">
            <Image
              src={imageSrc}
              alt={imageAlt}
              width={500}
              height={400}
              className="w-full h-auto object-contain drop-shadow-lg"
              priority
            />
          </div>
        </div>

        {/* Right side - Content */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="max-w-md w-full space-y-6">
            {/* Title and Subtitle */}
            <div className="text-center space-y-2">
              <h1 className="text-3xl font-bold text-gray-900">
                {title}
              </h1>
              <p className="text-gray-600 text-lg">
                {subtitle}
              </p>
            </div>

            {/* Children content (forms, buttons, etc.) */}
            <div className="space-y-6">
              {children}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
