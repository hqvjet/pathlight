'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { API_BASE, endpoints } from '@/utils/api';
import Image from 'next/image';
import { Montserrat } from 'next/font/google';

const montserrat = Montserrat({
  subsets: ['latin', 'vietnamese'],
  display: 'swap',
});

interface EmailVerificationResultProps {
  onLoginRedirect: () => void;
}

export default function EmailVerificationResult({ onLoginRedirect }: EmailVerificationResultProps) {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const [countdown, setCountdown] = useState(10);

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setStatus('error');
      setMessage('Token xác thực không hợp lệ');
      return;
    }

    const verifyEmail = async () => {
      try {
        const res = await fetch(`${API_BASE}${endpoints.verifyEmail}?token=${token}`, {
          method: 'GET'
        });

        const result = await res.json();

        if (res.ok) {
          setStatus('success');
          setMessage('Email đã được xác thực thành công!');
        } else {
          setStatus('error');
          // Hiển thị thông báo lỗi cụ thể từ backend
          if (result.message) {
            setMessage(result.message);
          } else if (result.detail) {
            setMessage(result.detail);
          } else if (res.status === 401) {
            setMessage('Token đã hết hạn hoặc không hợp lệ. Vui lòng đăng ký lại.');
          } else if (res.status === 404) {
            setMessage('Token không tồn tại. Vui lòng kiểm tra lại email của bạn.');
          } else {
            setMessage('Xác thực email thất bại. Vui lòng thử lại.');
          }
        }
      } catch (err) {
        setStatus('error');
        setMessage('Lỗi kết nối. Vui lòng kiểm tra internet và thử lại.');
      }
    };

    verifyEmail();
  }, [searchParams, onLoginRedirect]);

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="flex justify-between items-center px-8 md:px-24 py-6">
          <div className="flex items-center">
            <Image
              src="/assets/icons/LOGO.svg"
              alt="PathLight Logo"
              width={120}
              height={40}
              className="h-10 w-auto"
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-8 bg-gray-50">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-12 w-full max-w-2xl">
          
          {status === 'loading' && (
            <div className="text-center">
              <div className="mb-8">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-100 rounded-full">
                  <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
              </div>
              
              <h1 className={`text-3xl font-bold text-gray-800 mb-4 ${montserrat.className}`}>
                Đang xác thực email
              </h1>
              
              <p className="text-gray-600">
                Vui lòng đợi trong giây lát...
              </p>
            </div>
          )}

          {status === 'success' && (
            <div className="text-center max-w-md mx-auto">
              {/* Success Illustration */}
              <div className="mb-8">
                <Image
                  src="/assets/images/signup_success.png"
                  alt="Đăng ký thành công"
                  width={350}
                  height={280}
                  className="mx-auto drop-shadow-lg"
                  priority
                />
              </div>

              <h1 className={`text-3xl font-bold text-gray-800 mb-6 ${montserrat.className}`}>
                Đăng Ký Thành Công
              </h1>
              
              <div className="mb-8">
                <p className="text-lg text-gray-600 leading-relaxed px-4">
                  Email của bạn đã được xác thực thành công. Bây giờ bạn có thể đăng nhập và bắt đầu hành trình học tập thú vị cùng PathLight.
                </p>
              </div>

              <div className="space-y-4">
                <button
                  onClick={onLoginRedirect}
                  className="w-full py-4 px-8 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold text-lg rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 hover:scale-[1.02]"
                >
                  Đăng Nhập Ngay
                </button>
              </div>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center">
              {/* Error Icon */}
              <div className="mb-8">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-red-100 rounded-full">
                  <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
              </div>
              
              <h1 className={`text-3xl font-bold text-gray-800 mb-6 ${montserrat.className}`}>
                Xác Thực Thất Bại
              </h1>
              
              <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
                <p className="text-red-700 text-lg">{message}</p>
              </div>

              <div className="space-y-4">
                <button
                  onClick={onLoginRedirect}
                  className="w-full py-4 px-8 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold text-lg rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
                >
                  Quay Lại Đăng Nhập
                </button>
                
                <div className="text-center">
                  <p className="text-gray-500 text-sm">
                    Cần hỗ trợ? Liên hệ với chúng tôi để được giúp đỡ
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}