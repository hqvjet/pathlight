'use client';

import Image from 'next/image';
import Link from 'next/link';
import Header from '../layout/Header';
import { Montserrat } from 'next/font/google';

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
    <div className={`min-h-screen bg-white flex flex-col ${montserrat.className}`}>
      {/* Header */}
      <Header 
        variant="auth" 
        showSocialLinks={true}
        backgroundColor="transparent"
      />

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center px-6 py-20">
        <div className="flex flex-col lg:flex-row items-center gap-12 max-w-6xl w-full">
          {/* Thank You Illustration */}
          <div className="flex-shrink-0">
            <div className="relative">
              <Image
                src="/assets/images/email_success.png"
                alt="Thank you illustration"
                width={400}
                height={400}
                className="w-80 h-80 lg:w-96 lg:h-96 object-contain"
              />
            </div>
          </div>

          {/* Text Content */}
          <div className="flex-1 text-center lg:text-left">
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-6">
              Đã Gửi Email Thành Công
            </h1>
            
            <div className="space-y-4 text-gray-600 text-lg sm:text-xl">
              <p>
                Chúng tôi vừa gửi cho bạn một email xác nhận{email ? ` tới ${email}` : ''}
              </p>
              <p>
                Vui lòng kiểm tra hộp thư đến của bạn để tiếp tục.
              </p>
              <p className="text-orange-600 font-medium">
                ⚠️ Link xác nhận sẽ hết hạn sau 10 phút. Vui lòng xác nhận sớm.
              </p>
              <p>
                Nếu chưa nhận được email, vui lòng{' '}
                <button
                  onClick={onResendEmail}
                  disabled={isResending}
                  className="text-blue-600 hover:text-blue-800 underline font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isResending ? (
                    <span className="inline-flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      đang gửi...
                    </span>
                  ) : (
                    'gửi lại'
                  )}
                </button>
                {' '}...!
              </p>
            </div>

            {/* Back to Login Link */}
            <div className="mt-8">
              <Link
                href="/auth/signin"
                className="inline-flex items-center px-6 py-3 text-base text-white bg-gray-900 hover:bg-gray-800 rounded-lg font-semibold transition-all duration-200 transform hover:scale-[1.02]">
                ← Quay lại đăng nhập
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
