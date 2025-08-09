'use client';

import Image from 'next/image';
import Link from 'next/link';
import Header from '../layout/Header';
import { Button } from '@/components/ui/button';

interface ErrorPageProps {
  errorCode?: string;
  title?: string;
  subtitle?: string;
  buttonText?: string;
  buttonLink?: string;
  secondaryAction?: { label: string; href: string };
}

export default function ErrorPage({
  errorCode = '404',
  title = 'Ôi không! Bạn đang bị lạc đường',
  subtitle = 'Trang bạn tìm có thể đã bị xóa, đổi tên hoặc tạm thời không khả dụng.',
  buttonText = 'Trở về trang chính',
  buttonLink = '/',
  secondaryAction = { label: 'Liên hệ hỗ trợ', href: '/support' }
}: ErrorPageProps) {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-background to-muted/30 text-foreground">
      {/* Header */}
      <Header variant="auth" showSocialLinks={false} backgroundColor="transparent" />

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-6xl flex flex-col lg:flex-row items-center gap-14">
          {/* Illustration */}
          <div className="order-last lg:order-first flex-1 flex items-center justify-center">
            <div className="relative w-full max-w-md">
              <div className="relative rounded-3xl border bg-card/60 backdrop-blur p-6 shadow-md">
                <div className="aspect-square w-full flex items-center justify-center">
                  <Image
                    src="/assets/images/error_page.png"
                    alt="Error illustration"
                    width={420}
                    height={420}
                    className="w-full h-auto select-none pointer-events-none"
                    priority
                  />
                </div>
                <div className="pointer-events-none select-none">
                  <span className="absolute -top-3 -left-3 text-xl animate-pulse">❓</span>
                  <span className="absolute top-6 -right-5 text-lg animate-pulse [animation-delay:200ms]">🤔</span>
                  <span className="absolute -bottom-4 left-10 text-base animate-pulse [animation-delay:400ms]">💭</span>
                </div>
              </div>
              <div className="absolute inset-0 -z-10 blur-3xl opacity-40 bg-gradient-to-tr from-orange-500/40 via-primary/30 to-amber-400/30" />
            </div>
          </div>

          {/* Text */}
          <div className="flex-1 space-y-6 text-center lg:text-left">
            <div className="space-y-3">
              <p className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-1 text-xs font-medium text-primary tracking-wide uppercase">
                <span>Mã lỗi</span>
                <span className="font-semibold">{errorCode}</span>
              </p>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold leading-tight bg-clip-text text-transparent bg-gradient-to-r from-primary to-orange-500">
                {title}
              </h1>
              {subtitle && (
                <p className="text-muted-foreground max-w-xl mx-auto lg:mx-0">
                  {subtitle}
                </p>
              )}
            </div>
            <div className="flex flex-col sm:flex-row gap-4 sm:justify-center lg:justify-start">
              <Button asChild size="lg" className="font-semibold">
                <Link href={buttonLink}>{buttonText}</Link>
              </Button>
              {secondaryAction && (
                <Button asChild variant="outline" size="lg" className="backdrop-blur">
                  <Link href={secondaryAction.href}>{secondaryAction.label}</Link>
                </Button>
              )}
            </div>
            <p className="text-xs text-muted-foreground/80">
              Nếu bạn nghĩ đây là lỗi của hệ thống, vui lòng báo cho chúng tôi.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-background/60 backdrop-blur supports-[backdrop-filter]:bg-background/40 py-6 text-sm">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap justify-center gap-x-8 gap-y-2 text-muted-foreground">
          <Link href="/faqs" className="hover:text-foreground transition-colors">FAQs</Link>
            <span className="hidden sm:inline text-muted-foreground/40" aria-hidden>•</span>
          <Link href="/privacy" className="hover:text-foreground transition-colors">Privacy</Link>
            <span className="hidden sm:inline text-muted-foreground/40" aria-hidden>•</span>
          <Link href="/terms" className="hover:text-foreground transition-colors">Terms</Link>
        </div>
      </footer>
    </div>
  );
}
