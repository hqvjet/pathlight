'use client';

import Image from 'next/image';
import Link from 'next/link';
import Header from '../layout/Header';
import { Montserrat } from 'next/font/google';
import { Button } from '@/components/ui/button';
import { MailCheck, Loader } from 'lucide-react';

const montserrat = Montserrat({
  subsets: ['latin', 'vietnamese'],
  display: 'swap',
});

interface EmailSentPageProps {
  email?: string;
  onResendEmail?: () => void;
  isResending?: boolean;
}

export default function EmailSentPage({ email, onResendEmail, isResending = false }: EmailSentPageProps) {
  return (
    <div className={`min-h-screen flex flex-col bg-gradient-to-br from-orange-50 via-white to-emerald-50 ${montserrat.className}`}>
      {/* Header */}
      <Header 
        variant="auth" 
        showSocialLinks={true}
        backgroundColor="transparent"
      />

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center px-6 py-20">
        <div className="flex flex-col lg:flex-row items-center gap-12 max-w-6xl w-full">
          {/* Illustration */}
          <div className="flex-shrink-0">
            <div className="relative group">
              <div className="absolute -inset-4 rounded-3xl bg-gradient-to-tr from-orange-200/40 via-white to-emerald-200/40 blur-xl opacity-70 group-hover:opacity-90 transition" />
              <Image
                src="/assets/images/email_success.png"
                alt="Email sent illustration"
                width={400}
                height={400}
                className="relative w-80 h-80 lg:w-96 lg:h-96 object-contain drop-shadow-xl animate-fade-in"
              />
            </div>
          </div>

          {/* Text Content */}
          <div className="flex-1 text-center lg:text-left space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-100 text-orange-700 text-sm font-medium">
              <MailCheck className="w-4 h-4" />
              Email xác nhận đã gửi
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-gray-900">
              Đã Gửi Email Thành Công
            </h1>
            <div className="space-y-4 text-gray-600 text-lg sm:text-xl leading-relaxed">
              <p>
                Chúng tôi vừa gửi cho bạn một email xác nhận{email ? ` tới ` : ''}
                {email && (<span className="font-semibold text-gray-900">{email}</span>)}
              </p>
              <p>
                Vui lòng kiểm tra hộp thư đến của bạn để tiếp tục.
              </p>
              <p className="text-orange-600 font-medium bg-orange-50 border border-orange-200 rounded-lg p-3 inline-block">
                ⚠️ Link xác nhận sẽ hết hạn sau 10 phút. Vui lòng xác nhận sớm.
              </p>
              <p>
                Nếu chưa nhận được email, bạn có thể{' '}
                <Button
                  variant="link"
                  type="button"
                  onClick={onResendEmail}
                  disabled={isResending}
                  className="p-0 h-auto align-baseline font-semibold"
                >
                  {isResending ? (
                    <span className="inline-flex items-center gap-1">
                      <Loader className="h-4 w-4 animate-spin" /> đang gửi...
                    </span>
                  ) : 'gửi lại'}
                </Button>
                {' '}ngay bây giờ.
              </p>
            </div>

            {/* Actions */}
            <div className="pt-4 flex flex-col sm:flex-row items-center gap-4">
              <Link href="/auth/signin" className="w-full sm:w-auto">
                <Button variant="secondary" className="w-full sm:w-auto shadow-md hover:shadow-lg transition-shadow">
                  ← Quay lại đăng nhập
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
