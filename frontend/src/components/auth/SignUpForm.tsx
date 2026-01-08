'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { showToast } from '@/utils/toast';
import { api } from '@/lib/api-client';
import { storage } from '@/utils/api';
import { AuthResponse } from '@/utils/types';
import { useGoogleOAuth } from '@/hooks/useGoogleOAuth';
import AuthLayout from '@/components/layout/AuthLayout';
import GoogleAuthButton from './GoogleAuthButton';

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

  useEffect(() => {
    try {
      const token = storage.getToken();
      if (token) {
        router.replace('/user/dashboard');
      }
    } catch {
      // ignore
    }
  }, [router]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault(); // prevent default form submit
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
    <AuthLayout
      title="Tạo Tài Khoản Mới"
      subtitle="Tham gia Pathlight để bắt đầu học tập cùng chúng tôi"
      imageSrc="/assets/images/signup.png"
      imageAlt="Signup illustration"
      headerVariant="auth"
    >
      <form className="space-y-3 sm:space-y-4" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email" className="block text-sm sm:text-base font-medium text-gray-700 mb-2 sm:mb-3">
            Email
          </label>
          <input
            type="email"
            id="email"
            required
            className="w-full border-b-2 border-gray-200 py-2.5 sm:py-3 bg-transparent focus:outline-none focus:border-[#F97316] transition-colors text-gray-900 placeholder-gray-400 text-sm sm:text-base"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="Nhập Email"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5">
          <div>
            <label htmlFor="password" className="block text-base font-medium text-gray-700 mb-3">
              Mật Khẩu
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
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
                type={showConfirmPassword ? 'text' : 'password'}
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

        <GoogleAuthButton onClick={signInWithPopup} loading={loading} />
      </form>
    </AuthLayout>
  );
}
