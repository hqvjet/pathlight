'use client';

import Image from 'next/image';
import { ReactNode } from 'react';
import Header from './Header';

interface ResetPasswordLayoutProps {
  title: string;
  subtitle: string;
  icon: 'error' | 'success' | 'warning';
  children: ReactNode;
  imageSrc?: string;
}

export default function ResetPasswordLayout({ 
  title, 
  subtitle, 
  icon, 
  children,
  imageSrc = '/assets/images/error_page.png'
}: ResetPasswordLayoutProps) {
  const getIconElement = () => {
    switch (icon) {
      case 'error':
        return (
          <div className="w-20 h-20 flex items-center justify-center">
            <svg className="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5l-6.928-12c-.77-.833-2.834-.833-3.604 0l-6.928 12c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
        );
      case 'success':
        return (
          <div className="w-20 h-20 flex items-center justify-center">
            <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        );
      case 'warning':
        return (
          <div className="w-20 h-20 flex items-center justify-center">
            <svg className="w-10 h-10 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5l-6.928-12c-.77-.833-2.834-.833-3.604 0l-6.928 12c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <Header 
        variant="auth" 
        showSocialLinks={true}
        backgroundColor="transparent"
      />

      {/* Main Content */}
      <div className="flex-1 flex pt-20">
        {/* Left side - Image */}
        <div className="hidden lg:flex flex-1 items-center justify-center p-8">
          <div className="max-w-lg w-full">
            <Image
              src={imageSrc}
              alt="Reset password illustration"
              width={500}
              height={400}
              className="w-full h-auto object-contain"
              priority
            />
          </div>
        </div>

        {/* Right side - Content */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="max-w-md w-full space-y-8">
            {/* Icon */}
            <div className="flex justify-center">
              {getIconElement()}
            </div>

            {/* Title and Subtitle */}
            <div className="text-center space-y-3">
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
                {title}
              </h1>
              <p className="text-gray-600 text-lg sm:text-xl leading-relaxed">
                {subtitle}
              </p>
            </div>

            {/* Children content (buttons, forms, etc.) */}
            <div className="space-y-4">
              {children}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
