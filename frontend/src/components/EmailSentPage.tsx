'use client';

import Image from 'next/image';
import Link from 'next/link';

interface EmailSentPageProps {
  email?: string;
  onResendEmail?: () => void;
  isResending?: boolean;
}

export default function EmailSentPage({ email, onResendEmail, isResending = false }: EmailSentPageProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-10 flex justify-between items-center p-6">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <Image
            src="/icons/LOGO.svg"
            alt="PathLight Logo"
            width={32}
            height={32}
            className="w-8 h-8"
          />
          <span className="text-xl font-bold text-gray-800">PathLight</span>
        </div>

        {/* Social Media Icons */}
        <div className="flex items-center gap-4">
          <a href="#" className="text-gray-600 hover:text-gray-800 transition-colors">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>
            </svg>
          </a>
          <a href="#" className="text-gray-600 hover:text-gray-800 transition-colors">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
            </svg>
          </a>
          <a href="#" className="text-gray-600 hover:text-gray-800 transition-colors">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
            </svg>
          </a>
          <a href="#" className="text-gray-600 hover:text-gray-800 transition-colors">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.174-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.098.119.112.223.083.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.402.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.357-.629-2.746-1.378l-.748 2.853c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.624 0 11.99-5.367 11.99-11.988C24.007 5.367 18.641.001 12.017.001z"/>
            </svg>
          </a>
        </div>
      </header>

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
            <h1 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-6">
              Đã Gửi Email Thành Công
            </h1>
            
            <div className="space-y-4 text-gray-600 text-lg">
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
                className="inline-flex items-center px-6 py-3 text-white bg-gray-900 hover:bg-gray-800 rounded-lg font-semibold transition-all duration-200 transform hover:scale-[1.02]">
                ← Quay lại đăng nhập
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
