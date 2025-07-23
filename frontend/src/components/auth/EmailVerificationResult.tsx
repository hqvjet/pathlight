'use client';

import { useEffect, useState, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { showToast } from '@/utils/toast';
import { api, storage } from '@/utils/api';
import { AuthResponse } from '@/utils/types';
import AuthLayout from '@/components/layout/AuthLayout';

interface EmailVerificationResultProps {
  onSetupRedirect?: () => void;
}

export default function EmailVerificationResult({ onSetupRedirect }: EmailVerificationResultProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const isVerifyingRef = useRef(false);
  const tokenRef = useRef<string | null>(null); 

  useEffect(() => {
    if (!tokenRef.current) {
      tokenRef.current = searchParams.get('token');
    }
    
    const token = tokenRef.current;
    
    if (!token) {
      setStatus('error');
      setMessage('Token xác thực không hợp lệ');
      return;
    }

    if (isVerifyingRef.current) {
      return;
    }

    const verifiedTokens = sessionStorage.getItem('verified_tokens');
    if (verifiedTokens && verifiedTokens.includes(token)) {
      setStatus('success');
      setMessage('Email đã được xác thực thành công!');
      return;
    }

    const verifyEmail = async () => {
      try {
        isVerifyingRef.current = true;
        const response = await api.auth.verifyEmail(token);

        if (response.status === 200) {
          setStatus('success');
          setMessage('Email đã được xác thực thành công!');
          
          const verifiedTokens = sessionStorage.getItem('verified_tokens') || '';
          sessionStorage.setItem('verified_tokens', verifiedTokens + ',' + token);
          
          const authData = response.data as AuthResponse;
          if (authData?.access_token) {
            storage.setToken(authData.access_token);
          }
          
          showToast.authSuccess('Email đã được xác thực thành công!');
        } else {
          setStatus('error');
          let errorMessage = '';
          if (response.error) {
            errorMessage = response.error;
          } else if (response.message) {
            errorMessage = response.message;
          } else if (response.status === 401) {
            errorMessage = 'Token đã hết hạn hoặc không hợp lệ. Vui lòng đăng ký lại.';
          } else if (response.status === 404) {
            errorMessage = 'Token không tồn tại. Vui lòng kiểm tra lại email của bạn.';
          } else {
            errorMessage = 'Xác thực email thất bại. Vui lòng thử lại.';
          }
          setMessage(errorMessage);
          showToast.authError(errorMessage);
        }
      } catch {
        setStatus('error');
        const errorMessage = 'Lỗi kết nối. Vui lòng kiểm tra internet và thử lại.';
        setMessage(errorMessage);
        showToast.authError(errorMessage);
      }
    };

    verifyEmail();
  }, []);

  return (
    <>
      {status === 'loading' && (
        <AuthLayout
          title="Đang xác thực email"
          subtitle="Vui lòng đợi trong giây lát..."
          imageSrc="/assets/images/email_verification.png"
          imageAlt="Email verification"
          headerVariant="auth"
        >
          <div className="text-center">
            <div className="flex justify-center mb-6">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
            </div>
            <p className="text-base text-gray-600">
              Đang kiểm tra token xác thực...
            </p>
          </div>
        </AuthLayout>
      )}

      {status === 'success' && (
        <AuthLayout
          title="Đăng Ký Thành Công"
          subtitle="Email của bạn đã được xác thực thành công. Bây giờ bạn có thể đăng nhập để bắt đầu sử dụng hệ thống."
          imageSrc="/assets/images/signup_success.png"
          imageAlt="Đăng ký thành công"
          headerVariant="auth"
        >
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-6">
              <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-base text-gray-600 mb-6">
              Tài khoản của bạn đã sẵn sàng để sử dụng
            </p>
            <button
              onClick={() => router.push('/auth/signin')}
              className="w-full py-4 px-4 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors font-medium text-base shadow-sm hover:shadow-md"
            >
              Quay Lại Đăng Nhập
            </button>
          </div>
        </AuthLayout>
      )}

      {status === 'error' && (
        <AuthLayout
          title="Xác Thực Thất Bại"
          subtitle="Có lỗi xảy ra trong quá trình xác thực email. Vui lòng thử lại hoặc liên hệ hỗ trợ."
          imageSrc="/assets/images/error_page.png"
          imageAlt="Xác thực thất bại"
          headerVariant="auth"
        >
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 mb-6">
              <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            
            <div className="bg-white border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-base text-red-700">{message}</p>
            </div>

            <div className="space-y-4">
              <button
                onClick={() => window.location.href = '/auth/signin'}
                className="w-full py-4 px-4 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors font-medium text-base shadow-sm hover:shadow-md"
              >
                Đăng Nhập
              </button>
              
              <div className="text-center">
                <p className="text-base text-gray-500">
                  Cần hỗ trợ? Liên hệ với chúng tôi để được giúp đỡ
                </p>
              </div>
            </div>
          </div>
        </AuthLayout>
      )}
    </>
  );
}