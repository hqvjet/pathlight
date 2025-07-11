"use client";

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { showToast } from '@/utils/toast';
import { api } from '@/utils/api';
import { Montserrat } from 'next/font/google';
import Header from '@/components/layout/Header';

const montserrat = Montserrat({
  subsets: ['latin', 'vietnamese'],
  display: 'swap',
});

export default function ResetPasswordTokenPage() {
  const [passwords, setPasswords] = useState({ new: '', confirm: '' });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);
  const params = useParams();
  const token = params.token as string;

  const validateToken = useCallback(async () => {
    try {
      const response = await api.auth.validateResetToken(token);

      if (response.status === 200) {
        setTokenValid(true);
      } else {
        setTokenValid(false);
        showToast.error(response.error || 'Token không hợp lệ hoặc đã hết hạn');
      }
    } catch {
      setTokenValid(false);
      showToast.error('Token không hợp lệ hoặc đã hết hạn');
    }
  }, [token]);

  useEffect(() => {
    if (!token) {
      showToast.error('Token không hợp lệ');
      setTokenValid(false);
      return;
    }
    validateToken();
  }, [token, validateToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Validation
    if (!passwords.new || !passwords.confirm) {
      showToast.error('Vui lòng nhập đầy đủ thông tin');
      return;
    }
    if (passwords.new !== passwords.confirm) {
      showToast.error('Mật khẩu xác nhận không khớp');
      return;
    }
    if (passwords.new.length < 6) {
      showToast.error('Mật khẩu phải có ít nhất 6 ký tự');
      return;
    }
    if (!/(?=.*[a-zA-Z])/.test(passwords.new)) {
      showToast.error('Mật khẩu phải chứa ít nhất 1 chữ cái');
      return;
    }
    setLoading(true);
    try {
      const response = await api.auth.resetPassword(token, {
        new_password: passwords.new
      });
      
      if (response.status === 200) {
        setSuccess(true);
        showToast.success('Đặt lại mật khẩu thành công!');
      } else {
        const errorMessage = response.error || response.message || 'Có lỗi xảy ra';
        if (response.status === 400) {
          if (errorMessage.includes('token')) {
            showToast.error('Token không hợp lệ hoặc đã hết hạn');
          } else if (errorMessage.includes('password')) {
            showToast.error('Mật khẩu không đáp ứng yêu cầu bảo mật');
          } else {
            showToast.error(errorMessage);
          }
        } else if (response.status === 404) {
          showToast.error('Token không tồn tại hoặc đã được sử dụng');
        } else {
          showToast.error(errorMessage);
        }
      }
    } catch (error: unknown) {
      console.error('Reset password error:', error);
      showToast.error('Lỗi kết nối. Vui lòng kiểm tra internet và thử lại.');
    } finally {
      setLoading(false);
    }
  };

  // Success state
  if (success) {
    return (
      <div className={`h-screen bg-white flex flex-col overflow-hidden ${montserrat.className}`}>
        {/* Header */}
        <Header 
          variant="minimal" 
          showSocialLinks={true}
          backgroundColor="white"
          authNavigation={
            <div className="text-base flex items-center">
              <span className="text-gray-500 mr-4">Đã có tài khoản?</span>
              <Link
                href="/auth/signin"
                className="text-orange-500 hover:text-orange-600 font-medium"
              >
                Đăng Nhập Ngay
              </Link>
            </div>
          }
        />
        {/* Main Content */}
        <div className="flex flex-1 h-[calc(100vh-80px)]">
          {/* Left: Image */}
          <div className="hidden lg:flex lg:w-1/2 items-center justify-center p-4 xl:p-6 bg-gray-50">
            <div className="w-full max-w-4xl">
              <Image
                src="/assets/images/email_success.png"
                alt="Password reset success illustration"
                width={900}
                height={750}
                className="w-full h-auto object-contain"
                priority
              />
            </div>
          </div>
          {/* Right side content */}
          <div className="w-full lg:w-1/2 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-4 bg-white">
            <div className="w-full max-w-lg space-y-8">
              <div className="text-center space-y-4">
                <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
                  Đặt lại mật khẩu thành công
                </h1>
                <p className="text-gray-600 text-lg sm:text-xl">
                  Mật khẩu của bạn đã được đặt lại thành công. Bạn có thể đăng nhập bằng mật khẩu mới.
                </p>
              </div>
              <div className="space-y-8">
                <div className="text-center">
                  <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
                    <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <p className="text-base text-gray-600">
                    Tài khoản của bạn đã sẵn sàng để sử dụng
                  </p>
                </div>
                <Link 
                  href="/auth/signin"
                  className="w-full flex justify-center py-4 px-4 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors font-medium text-base shadow-sm hover:shadow-md"
                >
                  Đăng nhập ngay →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  if (tokenValid === false) {
    return (
      <div className={`h-screen bg-white flex flex-col overflow-hidden ${montserrat.className}`}>
        {/* Header */}
        <Header 
          variant="auth" 
          showSocialLinks={true}
          backgroundColor="white"
          authNavigation={
            <div className="text-base flex items-center">
              <span className="text-gray-500 mr-4">Đã có tài khoản?</span>
              <Link
                href="/auth/signin"
                className="text-orange-500 hover:text-orange-600 font-medium"
              >
                Đăng Nhập Ngay
              </Link>
            </div>
          }
        />
        {/* Main Content */}
        <div className="flex flex-1 h-[calc(100vh-80px)]">
          {/* Left: Image */}
          <div className="hidden lg:flex lg:w-1/2 items-center justify-center p-4 xl:p-6 bg-gray-50">
            <div className="w-full max-w-4xl">
              <Image
                src="/assets/images/error_page.png"
                alt="Invalid link illustration"
                width={900}
                height={750}
                className="w-full h-auto object-contain"
                priority
              />
            </div>
          </div>
          {/* Right side content */}
          <div className="w-full lg:w-1/2 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-4 bg-white">
            <div className="w-full max-w-lg space-y-8">
              <div className="text-center space-y-4">
                <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
                  Liên kết không hợp lệ
                </h1>
                <p className="text-gray-600 text-lg sm:text-xl">
                  Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn. Vui lòng yêu cầu một liên kết mới.
                </p>
              </div>
              <div className="space-y-8">
                <div className="text-center">
                  <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 mb-4">
                    <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </div>
                  <p className="text-base text-gray-600">
                    Thời gian hiệu lực của liên kết đã hết
                  </p>
                </div>
                <div className="space-y-4">
                  <Link 
                    href="/auth/forgot-password"
                    className="w-full flex justify-center py-4 px-4 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors font-medium text-base shadow-sm hover:shadow-md"
                  >
                    Yêu cầu đặt lại mật khẩu mới →
                  </Link>
                  <Link 
                    href="/auth/signin"
                    className="w-full flex justify-center py-4 px-4 border-2 border-orange-500 text-orange-500 rounded-lg hover:bg-orange-500 hover:text-white transition-all duration-200 font-medium text-base shadow-sm hover:shadow-md"
                  >
                    ← Quay lại đăng nhập
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  if (tokenValid === null) {
    return (
      <div className={`h-screen bg-white flex flex-col overflow-hidden ${montserrat.className}`}>
        {/* Header */}
        <Header 
          variant="auth" 
          showSocialLinks={true}
          backgroundColor="white"
          authNavigation={
            <div className="text-base flex items-center">
              <span className="text-gray-500 mr-4">Đã có tài khoản?</span>
              <Link
                href="/auth/signin"
                className="text-orange-500 hover:text-orange-600 font-medium"
              >
                Đăng Nhập Ngay
              </Link>
            </div>
          }
        />
        {/* Main Content */}
        <div className="flex flex-1 h-[calc(100vh-80px)] items-center justify-center">
          <div className="text-center">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Đang kiểm tra liên kết...
            </h2>
            <div className="flex justify-center mb-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
            </div>
            <p className="text-base text-gray-600">
              Vui lòng đợi trong giây lát
            </p>
          </div>
        </div>
      </div>
    );
  }
  // Reset password form
  return (
    <div className={`h-screen bg-white flex flex-col overflow-hidden ${montserrat.className}`}>
      {/* Header */}
      <Header 
        variant="auth" 
        showSocialLinks={true}
        backgroundColor="white"
        authNavigation={
          <div className="text-base flex items-center">
            <span className="text-gray-500 mr-4">Đã có tài khoản?</span>
            <Link
              href="/auth/signin"
              className="text-orange-500 hover:text-orange-600 font-medium"
            >
              Đăng Nhập Ngay
            </Link>
          </div>
        }
      />
      {/* Main Content */}
      <div className="flex flex-1 h-[calc(100vh-80px)]">
        {/* Left: Image */}
        <div className="hidden lg:flex lg:w-1/2 items-center justify-center p-4 xl:p-6 bg-gray-50">
          <div className="w-full max-w-4xl">
            <Image
              src="/assets/images/reset-password.png"
              alt="Reset password illustration"
              width={900}
              height={750}
              className="w-full h-auto object-contain"
              priority
            />
          </div>
        </div>
        {/* Right side form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-4 bg-white">
          <div className="w-full max-w-lg space-y-8">
            <div className="text-center space-y-4">
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
                Đặt Lại Mật Khẩu
              </h1>
              <p className="text-gray-600 text-lg sm:text-xl">
                Nhập mật khẩu mới cho tài khoản của bạn. Hãy chọn mật khẩu mạnh để bảo vệ tài khoản.
              </p>
            </div>
            <div className="space-y-8">
              <form className="space-y-6" onSubmit={handleSubmit}>
                <div>
                  <label htmlFor="newPassword" className="block text-base font-medium text-gray-700 mb-3">
                    Mật khẩu mới
                  </label>
                  <input
                    id="newPassword"
                    type="password"
                    required
                    value={passwords.new}
                    onChange={(e) => setPasswords(prev => ({ ...prev, new: e.target.value }))}
                    className="w-full px-4 py-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors text-base"
                    placeholder="Nhập mật khẩu mới (tối thiểu 6 ký tự)"
                  />
                  <p className="text-sm text-gray-500 mt-2">
                    Mật khẩu phải có ít nhất 6 ký tự và chứa ít nhất 1 chữ cái
                  </p>
                </div>
                <div>
                  <label htmlFor="confirmPassword" className="block text-base font-medium text-gray-700 mb-3">
                    Xác nhận mật khẩu mới
                  </label>
                  <input
                    id="confirmPassword"
                    type="password"
                    required
                    value={passwords.confirm}
                    onChange={(e) => setPasswords(prev => ({ ...prev, confirm: e.target.value }))}
                    className={`w-full px-4 py-4 border rounded-lg focus:ring-2 transition-colors text-base ${
                      passwords.confirm && passwords.new !== passwords.confirm 
                        ? 'border-red-300 focus:ring-red-500 focus:border-red-500' 
                        : 'border-gray-300 focus:ring-orange-500 focus:border-orange-500'
                    }`}
                    placeholder="Nhập lại mật khẩu mới"
                  />
                  {passwords.confirm && passwords.new !== passwords.confirm && (
                    <p className="text-sm text-red-500 mt-2">
                      Mật khẩu xác nhận không khớp
                    </p>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-4 px-4 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-base shadow-sm hover:shadow-md"
                >
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Đang đặt lại...
                    </div>
                  ) : (
                    'Đặt Lại Mật Khẩu →'
                  )}
                </button>
              </form>
              <div className="text-center">
                <Link 
                  href="/auth/signin" 
                  className="inline-flex items-center justify-center px-6 py-3 border-2 border-orange-500 text-orange-500 rounded-lg hover:bg-orange-500 hover:text-white transition-all duration-200 font-medium text-base shadow-sm hover:shadow-md"
                >
                  ← Quay lại đăng nhập
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
