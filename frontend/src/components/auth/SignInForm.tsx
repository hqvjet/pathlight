'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { showToast } from '@/utils/toast';
import { api } from '@/lib/api-client';
import { storage } from '@/utils/api';
import { AuthResponse } from '@/utils/types';
import { useGoogleOAuth } from '@/hooks/useGoogleOAuth';
import { Montserrat } from 'next/font/google';
import Header from '../layout/Header';

const montserrat = Montserrat({
  subsets: ['latin', 'vietnamese'],
  display: 'swap',
});

export default function SignInForm() {
  const router = useRouter();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setRememberMe(storage.isRemembered());
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.auth.signin(formData);

      if (response.status !== 200) {
        let errorMessage = 'Đăng nhập thất bại';
        
        if (response.error) {
          errorMessage = response.error;
        } else {
          switch (response.status) {
            case 400:
              errorMessage = 'Thông tin đăng nhập không hợp lệ';
              break;
            case 401:
              errorMessage = 'Email hoặc mật khẩu không đúng';
              break;
            case 404:
              errorMessage = 'Tài khoản không tồn tại';
              break;
            case 500:
              errorMessage = 'Lỗi server. Vui lòng thử lại sau';
              break;
            default:
              errorMessage = `Đăng nhập thất bại (Mã lỗi: ${response.status})`;
          }
        }
        
        showToast.authError(errorMessage);
        return;
      }

      const result = response.data as AuthResponse & { message?: string };

      if (result?.access_token) {
        storage.setToken(result.access_token, rememberMe);
        showToast.authSuccess('Đăng nhập thành công!');
        router.push('/user/dashboard');
      } else if (result?.message === 'Email chưa được xác thực') {
        showToast.warning('Email chưa được xác thực. Chuyển đến trang xác thực...');
        storage.setPendingEmail(formData.email);
        setTimeout(() => {
          router.push('/auth/verify-email');
        }, 2000);
      } else {
        showToast.authError(result?.message || 'Đăng nhập thất bại');
      }
    } catch (error) {
      console.error('Login error:', error);
      showToast.authError('Lỗi kết nối. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (googleUser: unknown) => {
    setLoading(true);

    try {
      const response = await api.auth.oauthSignin(googleUser);

      if (response.status !== 200) {
        let errorMessage = 'Đăng nhập Google thất bại';
        
        if (response.error) {
          errorMessage = response.error;
        } else {
          switch (response.status) {
            case 400:
              errorMessage = 'Thông tin Google không hợp lệ';
              break;
            case 401:
              errorMessage = 'Xác thực Google thất bại';
              break;
            case 500:
              errorMessage = 'Lỗi server. Vui lòng thử lại sau';
              break;
            default:
              errorMessage = `Đăng nhập Google thất bại (Mã lỗi: ${response.status})`;
          }
        }
        
        showToast.authError(errorMessage);
        return;
      }

      const result = response.data as AuthResponse & { message?: string };

      if (result?.access_token) {
        storage.setToken(result.access_token, rememberMe);
        showToast.authSuccess('Đăng nhập Google thành công!');
        router.push('/user/dashboard');
      } else {
        showToast.authError(result?.message || 'Đăng nhập Google thất bại');
      }
    } catch (error) {
      console.error('Google OAuth error:', error);
      showToast.authError('Lỗi kết nối. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  const { signInWithPopup } = useGoogleOAuth({
    onSuccess: handleGoogleSuccess,
    onError: () => showToast.authError('Đăng nhập Google thất bại'),
  });

  return (
    <div className={`h-screen bg-white flex flex-col overflow-hidden ${montserrat.className}`}>
      {/* Header */}
      <Header 
        variant="auth" 
        showSocialLinks={false}
        backgroundColor="white"
        authNavigation={
          <div className="text-sm flex items-center">
            <span className="text-gray-500 mr-4">Chưa có tài khoản?</span>
            <Link
              href="/auth/signup"
              className="bg-[#FFF7ED] text-[#F97316] font-semibold px-4 py-2 rounded-lg hover:bg-orange-200 transition-colors"
            >
              Đăng Ký Ngay
            </Link>
          </div>
        }
      />

      {/* Main Content */}
      <div className="flex flex-1 h-[calc(100vh-80px)]">
        {/* Left: Image - hidden on mobile */}
        <div className="hidden lg:flex lg:w-1/2 items-center justify-center p-4 xl:p-6 bg-gray-50">
          <div className="w-full max-w-2xl">
            <Image
              src="/assets/images/login.png"
              alt="Login illustration"
              width={700}
              height={700}
              className="object-contain w-full h-auto"
            />
          </div>
        </div>

        {/* Right side form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center bg-white px-4 sm:px-6 lg:px-8 py-4">
          <div className="w-full max-w-lg">
            <h2 className="text-3xl sm:text-4xl font-bold text-center text-red-900 mb-6 sm:mb-8">
              Chào Mừng Trở Lại
            </h2>

            <form className="space-y-5 sm:space-y-6" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="email" className="block text-base font-medium text-gray-700 mb-3">
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  required
                  className="w-full border-b-2 border-gray-200 py-3 sm:py-4 bg-transparent focus:outline-none focus:border-[#F97316] transition-colors text-gray-900 placeholder-gray-400 text-base"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="Nhập email"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-base font-medium text-gray-700 mb-3">
                  Mật Khẩu
                </label>
                <input
                  type="password"
                  id="password"
                  required
                  className="w-full border-b-2 border-gray-200 py-3 sm:py-4 bg-transparent focus:outline-none focus:border-[#F97316] transition-colors text-gray-900 placeholder-gray-400 text-base"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Nhập mật khẩu"
                />
              </div>

              <div className="flex justify-between items-center text-base">
                <label className="flex items-center text-gray-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="mr-3 h-5 w-5 text-[#F97316] border-gray-300 rounded focus:ring-[#F97316] focus:ring-2"
                  />
                  Ghi nhớ đăng nhập
                </label>
                <Link
                  href="/auth/forgot-password"
                  className="text-gray-500 hover:text-[#F97316] transition-colors"
                >
                  Quên mật khẩu?
                </Link>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center py-4 sm:py-5 px-6 text-white bg-gray-900 hover:bg-gray-800 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] text-base"
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Đang đăng nhập...
                  </div>
                ) : (
                  'Đăng Nhập →'
                )}
              </button>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-base">
                  <span className="px-6 bg-white text-gray-500">Đăng Nhập Với</span>
                </div>
              </div>

              <button
                type="button"
                onClick={signInWithPopup}
                disabled={loading}
                className="w-full flex items-center justify-center py-4 sm:py-5 px-6 border-2 border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 text-gray-700 font-medium text-base"
              >
                <div className="flex items-center justify-center w-6 h-6 mr-4">
                  <svg viewBox="0 0 24 24" className="w-6 h-6">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                </div>
                <span>Google</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
