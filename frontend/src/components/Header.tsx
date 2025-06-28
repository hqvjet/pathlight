'use client';

import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface HeaderProps {
  variant?: 'default' | 'auth' | 'minimal';
  showSocialLinks?: boolean;
  backgroundColor?: 'transparent' | 'white' | 'gray';
  authNavigation?: React.ReactNode;
}

export default function Header({ 
  variant = 'default', 
  showSocialLinks = true,
  backgroundColor = 'transparent',
  authNavigation
}: HeaderProps) {
  const router = useRouter();

  const getBackgroundClass = () => {
    switch (backgroundColor) {
      case 'white':
        return 'bg-white shadow-sm';
      case 'gray':
        return 'bg-gray-50';
      case 'transparent':
      default:
        return 'bg-transparent';
    }
  };

  const socialLinks = [
    {
      name: 'Facebook',
      href: '#',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
      )
    },
    {
      name: 'Twitter',
      href: '#',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
        </svg>
      )
    },
    {
      name: 'YouTube',
      href: '#',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
        </svg>
      )
    },
    {
      name: 'Instagram',
      href: '#',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.174-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.098.119.112.223.083.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.402.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.357-.629-2.746-1.378l-.748 2.853c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.624 0 11.99-5.367 11.99-11.988C24.007 5.367 18.641.001 12.017.001z"/>
        </svg>
      )
    }
  ];

  if (variant === 'minimal') {
    return (
      <header className={`absolute top-0 left-0 right-0 z-10 ${getBackgroundClass()}`}>
        <div className="flex justify-center items-center p-6">
          <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <Image
              src="/assets/icons/LOGO.svg"
              alt="PathLight Logo"
              width={120}
              height={40}
              className="h-8 w-auto"
            />
          </Link>
        </div>
      </header>
    );
  }

  return (
    <header className={`absolute top-0 left-0 right-0 z-10 ${getBackgroundClass()}`}>
      <div className="flex justify-between items-center p-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <Image
            src="/assets/icons/LOGO.svg"
            alt="PathLight Logo"
            width={120}
            height={40}
            className="h-8 w-auto"
          />
        </Link>

        {/* Right section - Navigation và Social Icons */}
        <div className="flex items-center gap-6">
          {/* Navigation Menu for default variant */}
          {variant === 'default' && (
            <nav className="hidden md:flex items-center gap-6">
              <Link href="/about" className="text-gray-700 hover:text-orange-500 transition-colors">
                Về chúng tôi
              </Link>
              <Link href="/courses" className="text-gray-700 hover:text-orange-500 transition-colors">
                Khóa học
              </Link>
              <Link href="/contact" className="text-gray-700 hover:text-orange-500 transition-colors">
                Liên hệ
              </Link>
              <Link href="/auth/signin" className="bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors">
                Đăng nhập
              </Link>
            </nav>
          )}

          {/* Auth Navigation for auth variant */}
          {variant === 'auth' && authNavigation && (
            <div className="flex items-center">
              {authNavigation}
            </div>
          )}

          {/* Social Media Icons - Always at the far right */}
          {showSocialLinks && (
            <div className="flex items-center gap-3">
              {socialLinks.map((social) => (
                <a
                  key={social.name}
                  href={social.href}
                  className="text-gray-600 hover:text-blue-600 transition-colors p-2 rounded-full hover:bg-gray-100"
                  title={social.name}
                >
                  {social.icon}
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
