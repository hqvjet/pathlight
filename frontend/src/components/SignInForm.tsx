'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { showToast } from '@/utils/toast';
import { API_BASE, endpoints, storage } from '@/utils/api';
import { useGoogleOAuth } from '@/hooks/useGoogleOAuth';
import { Montserrat } from 'next/font/google';

const montserrat = Montserrat({
  subsets: ['latin', 'vietnamese'],
  display: 'swap',
});

export default function SignInForm() {
  const router = useRouter();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}${endpoints.signin}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      // Kiểm tra nếu response không ok (status >= 400)
      if (!res.ok) {
        // Xử lý các lỗi HTTP khác nhau
        let errorMessage = 'Đăng nhập thất bại';
        
        try {
          const errorResult = await res.json();
          if (errorResult.message) {
            errorMessage = errorResult.message;
          } else if (errorResult.detail) {
            errorMessage = errorResult.detail;
          }
        } catch {
          // Nếu không parse được JSON, dùng message mặc định dựa trên status
          switch (res.status) {
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
              errorMessage = `Đăng nhập thất bại (Mã lỗi: ${res.status})`;
          }
        }
        
        showToast.authError(errorMessage);
        return;
      }

      const result = await res.json();

      if (result.access_token) {
        storage.setToken(result.access_token);
        showToast.authSuccess('Đăng nhập thành công!');
        router.push('/dashboard');
      } else if (result.message === 'Email chưa được xác thực') {
        showToast.warning('Email chưa được xác thực. Chuyển đến trang xác thực...');
        storage.setPendingEmail(formData.email);
        setTimeout(() => {
          router.push('/auth/verify-email');
        }, 2000);
      } else {
        showToast.authError(result.message || 'Đăng nhập thất bại');
      }
    } catch (error) {
      console.error('Login error:', error);
      showToast.authError('Lỗi kết nối. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (googleUser: any) => {
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}${endpoints.oauthSignin}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(googleUser),
      });

      // Kiểm tra nếu response không ok
      if (!res.ok) {
        let errorMessage = 'Đăng nhập Google thất bại';
        
        try {
          const errorResult = await res.json();
          if (errorResult.message) {
            errorMessage = errorResult.message;
          } else if (errorResult.detail) {
            errorMessage = errorResult.detail;
          }
        } catch {
          switch (res.status) {
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
              errorMessage = `Đăng nhập Google thất bại (Mã lỗi: ${res.status})`;
          }
        }
        
        showToast.authError(errorMessage);
        return;
      }

      const result = await res.json();

      if (result.access_token) {
        storage.setToken(result.access_token);
        showToast.authSuccess('Đăng nhập Google thành công!');
        router.push('/dashboard');
      } else {
        showToast.authError(result.message || 'Đăng nhập Google thất bại');
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
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="flex bg-white justify-between items-center px-8 md:px-24 py-6">
        <div className="flex items-center">
          <Image
            src="/icons/LOGO.svg"
            alt="PathLive Logo"
            width={120}
            height={40}
            className="w-auto h-10"
          />
        </div>
        <div className="text-sm flex items-center">
          <span className="text-gray-500 mr-4">Chưa có tài khoản?</span>
          <Link
            href="/auth/signup"
            className="bg-[#FFF7ED] text-[#F97316] font-semibold px-4 py-2 rounded-lg hover:bg-orange-200 transition-colors"
          >
            Đăng Ký Ngay
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex min-h-[calc(100vh-80px)]">
        {/* Left: Image */}
        <div className="w-1/2 bg-[#FEF7F0] flex items-center justify-center p-8">
          <div className="max-w-lg">
            <Image
              src="/assets/images/login.png"
              alt="Login illustration"
              width={500}
              height={500}
              className="object-contain w-full h-auto"
            />
          </div>
        </div>

        {/* Right side form */}
        <div className="w-1/2 flex items-center justify-center bg-white px-8">
          <div className="w-full max-w-md">
            <h2 className={`text-3xl font-bold text-center text-red-900 mb-8 ${montserrat.className}`}>
              Chào Mừng Trở Lại
            </h2>

            <form className="space-y-6" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  required
                  className="w-full border-b-2 border-gray-200 py-3 bg-transparent focus:outline-none focus:border-[#F97316] transition-colors text-gray-900 placeholder-gray-400"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="Nhập email"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  Mật Khẩu
                </label>
                <input
                  type="password"
                  id="password"
                  required
                  className="w-full border-b-2 border-gray-200 py-3 bg-transparent focus:outline-none focus:border-[#F97316] transition-colors text-gray-900 placeholder-gray-400"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Nhập mật khẩu"
                />
              </div>

              <div className="flex justify-between items-center text-sm">
                <label className="flex items-center text-gray-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="mr-2 h-4 w-4 text-[#F97316] border-gray-300 rounded focus:ring-[#F97316] focus:ring-2"
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
                className="w-full flex items-center justify-center py-4 px-6 text-white bg-gray-900 hover:bg-gray-800 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02]"
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
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-white text-gray-500">Đăng Nhập Với</span>
                </div>
              </div>

              <button
                type="button"
                onClick={signInWithPopup}
                disabled={loading}
                className="w-full flex items-center justify-center py-4 px-6 border-2 border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 text-gray-700 font-medium"
              >
                <Image
                  src="/icons/google.svg"
                  alt="Google"
                  width={20}
                  height={20}
                  className="mr-3"
                />
                <span>Google</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
