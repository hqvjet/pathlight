'use client';

import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Montserrat } from 'next/font/google';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search } from 'lucide-react';

const montserrat = Montserrat({
  subsets: ['latin', 'vietnamese'],
  display: 'swap',
});

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

  const getBackgroundClass = () => {
    switch (backgroundColor) {
      case 'white':
        return 'backdrop-blur supports-[backdrop-filter]:bg-white/80 border-b border-border';
      case 'gray':
        return 'bg-gray-50/90 backdrop-blur';
      case 'transparent':
      default:
        return 'bg-transparent';
    }
  };

  const socialLinks = [
    { name: 'Facebook', href: '#', icon: 'facebook' },
    { name: 'Twitter', href: '#', icon: 'twitter' },
    { name: 'YouTube', href: '#', icon: 'youtube' },
    { name: 'Instagram', href: '#', icon: 'instagram' },
  ];

  const renderSocialIcon = (id: string) => {
    switch (id) {
      case 'facebook':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
        );
      case 'twitter':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/></svg>
        );
      case 'youtube':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
        );
      case 'instagram':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.174-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.098.119.112.223.083.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.402.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.357-.629-2.746-1.378l-.748 2.853c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.624 0 11.99-5.367 11.99-11.988C24.007 5.367 18.641.001 12.017.001z"/></svg>
        );
    }
  };

  if (variant === 'minimal') {
    return (
      <header className={`absolute top-0 left-0 right-0 z-10 ${getBackgroundClass()}`}>
        <div className="flex justify-center items-center p-6">
          <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <Image src="/assets/icons/logo.png" alt="PathLight Logo" width={48} height={48} className="h-12 w-12" />
            <span className={`text-2xl font-bold text-orange-500 ${montserrat.className}`}>Pathlight</span>
          </Link>
        </div>
      </header>
    );
  }

  return (
    <header className={`absolute top-0 left-0 right-0 z-20 ${getBackgroundClass()}`}>
      <div className="flex justify-between items-center px-6 py-4 max-w-7xl mx-auto">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative">
            <Image src="/assets/icons/logo.png" alt="PathLight Logo" width={48} height={48} className="h-12 w-12 transition-transform group-hover:scale-105" />
          </div>
          <span className={`text-2xl font-bold bg-gradient-to-r from-orange-500 to-emerald-500 bg-clip-text text-transparent ${montserrat.className}`}>Pathlight</span>
        </Link>

        <div className="flex items-center gap-6">
          {variant === 'default' && (
            <nav className="hidden md:flex items-center gap-6 text-sm">
              <Link href="/about" className="text-muted-foreground hover:text-foreground transition-colors font-medium">Về chúng tôi</Link>
              <Link href="/courses" className="text-muted-foreground hover:text-foreground transition-colors font-medium">Khóa học</Link>
              <Link href="/contact" className="text-muted-foreground hover:text-foreground transition-colors font-medium">Liên hệ</Link>
              <Link href="/auth/signin" className="text-muted-foreground hover:text-foreground transition-colors font-medium">Đăng nhập</Link>
            </nav>
          )}

          {variant === 'auth' && authNavigation && (
            <div className="flex items-center gap-3">{authNavigation}</div>
          )}

          <div className="hidden lg:flex items-center gap-2 relative">
            <Search className="absolute left-3 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Tìm kiếm" className="pl-9 w-56" />
          </div>

          {showSocialLinks && (
            <div className="hidden md:flex items-center gap-2">
              {socialLinks.map(s => (
                <Button key={s.name} variant="ghost" size="sm" className="h-8 w-8 p-0" asChild>
                  <a href={s.href} aria-label={s.name} className="flex items-center justify-center">
                    {renderSocialIcon(s.icon)}
                  </a>
                </Button>
              ))}
            </div>
          )}

          {/* Auth buttons only when NOT in auth variant (avoid duplicates) */}
          {variant !== 'auth' && (
            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm" asChild>
                <Link href="/auth/signin">Đăng nhập</Link>
              </Button>
              <Button size="sm" asChild>
                <Link href="/auth/signup">Đăng ký</Link>
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
