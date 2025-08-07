'use client';

import { useState } from 'react';
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

export default function SignUpForm() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      showToast.authError('Mật khẩu xác nhận không khớp');
      setLoading(false);
      return;
    }

    // Validate terms agreement
    if (!agreeToTerms) {
      showToast.authError('Vui lòng đồng ý với điều khoản sử dụng');
      setLoading(false);
      return;
    }

    try {
      const response = await api.auth.signup({
        email: formData.email,
        password: formData.password,
      });

      if (response.status === 200) {
        // Success - email verification sent
        storage.setPendingEmail(formData.email);
        showToast.authSuccess('Đăng ký thành công! Vui lòng kiểm tra email để xác thực tài khoản.');
        router.push('/auth/email-sent');
      } else {
        // Get error message from response - backend may use 'detail' or 'message'
        const errorMessage = response.error || response.message || 'Đăng ký thất bại. Vui lòng thử lại.';
        
        // Handle different error cases
        if (response.status === 400 && errorMessage.includes('đã được sử dụng và đã được xác thực')) {
          // User already verified - should login instead
          showToast.authError(errorMessage);
        } else if (response.status === 409 || errorMessage.includes('already exists') || errorMessage.includes('đã tồn tại')) {
          showToast.authError('Email này đã được đăng ký. Vui lòng sử dụng email khác hoặc đăng nhập.');
        } else if (errorMessage.includes('Invalid email') || errorMessage.includes('email không hợp lệ')) {
          showToast.authError('Định dạng email không hợp lệ. Vui lòng kiểm tra lại.');
        } else if (errorMessage.includes('Password') || errorMessage.includes('mật khẩu')) {
          showToast.authError('Mật khẩu không đáp ứng yêu cầu. Vui lòng chọn mật khẩu mạnh hơn.');
        } else {
          // Use the exact error message from backend
          showToast.authError(errorMessage);
        }
      }
    } catch (error) {
      console.error('Signup error:', error);
      showToast.authError('Lỗi kết nối. Vui lòng kiểm tra internet và thử lại.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (googleUser: unknown) => {
    setLoading(true);

    try {
      const response = await api.auth.oauthSignin(googleUser);
      const authData = response.data as AuthResponse;

      if (response.status === 200 && authData?.access_token) {
        storage.setToken(authData.access_token);
        showToast.authSuccess('Đăng nhập Google thành công!');
        router.push('/user/dashboard');
      } else {
        showToast.authError(response.error || 'Đăng ký Google thất bại');
      }
    } catch {
      showToast.authError('Lỗi kết nối. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  const { signInWithPopup } = useGoogleOAuth({
    onSuccess: handleGoogleSuccess,
    onError: () => showToast.authError('Đăng ký Google thất bại'),
  });

  return (
    <div className={`h-screen bg-white flex flex-col overflow-hidden ${montserrat.className}`}>
      {/* Header */}
      <Header 
        variant="auth" 
        showSocialLinks={false}
        backgroundColor="white"
        authNavigation={
          <div className="flex items-center gap-2 sm:gap-3">
            <span className="text-gray-500 text-sm hidden sm:inline">Đã có tài khoản?</span>
            <Link
              href="/auth/signin"
              className="bg-orange-500 text-white font-medium px-3 py-2 sm:px-4 sm:py-2 rounded-lg hover:bg-orange-600 transition-colors text-sm"
            >
              Đăng Nhập Ngay
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
              src="/assets/images/signup.png"
              alt="Signup illustration"
              width={700}
              height={700}
              className="object-contain w-full h-auto"
            />
          </div>
        </div>

        {/* Right side form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center bg-white px-4 sm:px-6 lg:px-8 py-4">
          <div className="w-full max-w-lg">
            <h2 className="text-3xl sm:text-4xl font-bold text-center text-gray-900 mb-6 sm:mb-8">
              Tạo Tài Khoản Mới
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
                  placeholder="Nhập Email"
                />
              </div>

              <div className="grid grid-cols-2 gap-5">
                <div>
                  <label htmlFor="password" className="block text-base font-medium text-gray-700 mb-3">
                    Mật Khẩu
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      id="password"
                      required
                      className="w-full border-b-2 border-gray-200 py-3 bg-transparent focus:outline-none focus:border-[#F97316] transition-colors text-gray-900 placeholder-gray-400 pr-10 text-base"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      placeholder="Nhập mật khẩu"
                    />
                    <button
                      type="button"
                      className="absolute right-0 top-2 p-2 text-gray-500 hover:text-gray-700 transition-colors"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                        {showPassword ? (
                          <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 11-4.243-4.243m4.242 4.242L9.88 9.88" />
                        ) : (
                          <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.639 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.639 0-8.573-3.007-9.963-7.178z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        )}
                      </svg>
                    </button>
                  </div>
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-base font-medium text-gray-700 mb-3">
                    Xác Nhận Mật Khẩu
                  </label>
                  <div className="relative">
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      id="confirmPassword"
                      required
                      className="w-full border-b-2 border-gray-200 py-3 bg-transparent focus:outline-none focus:border-[#F97316] transition-colors text-gray-900 placeholder-gray-400 pr-10 text-base"
                      value={formData.confirmPassword}
                      onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                      placeholder="Nhập lại mật khẩu"
                    />
                    <button
                      type="button"
                      className="absolute right-0 top-2 p-2 text-gray-500 hover:text-gray-700 transition-colors"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                        {showConfirmPassword ? (
                          <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 11-4.243-4.243m4.242 4.242L9.88 9.88" />
                        ) : (
                          <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.639 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.639 0-8.573-3.007-9.963-7.178z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        )}
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              <div className="text-sm">
                <label className="flex items-start text-gray-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={agreeToTerms}
                    onChange={(e) => setAgreeToTerms(e.target.checked)}
                    className="mr-3 mt-1 h-4 w-4 text-[#F97316] border-gray-300 rounded focus:ring-[#F97316] focus:ring-2"
                  />
                  <span>
                    Tôi đồng ý với{' '}
                    <Link href="/terms" className="text-[#F97316] hover:underline">
                      Điều khoản
                    </Link>
                    {' '}và{' '}
                    <Link href="/privacy" className="text-[#F97316] hover:underline">
                      Điều kiện
                    </Link>
                  </span>
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center py-4 sm:py-5 px-6 text-white bg-gray-900 hover:bg-gray-800 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] text-base"
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Đang tạo tài khoản...
                  </div>
                ) : (
                  'Đăng Ký →'
                )}
              </button>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-base">
                  <span className="px-6 bg-white text-gray-500">Đăng Ký Với</span>
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
