"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { API_BASE, endpoints } from '@/utils/api';
import AuthLayout from '@/components/layout/AuthLayout';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Vui lòng nhập địa chỉ email hợp lệ');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE}${endpoints.forgotPassword}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const result = await response.json();

      if (response.ok) {
        setSuccess(true);
      } else {
        const errorMessage = result.message || result.detail || 'Có lỗi xảy ra';
        
        // Handle specific error cases
        if (response.status === 404) {
          // Redirect to email not found page
          router.push(`/auth/email-not-found?email=${encodeURIComponent(email)}`);
          return;
        } else if (response.status === 400 && errorMessage.includes('Google')) {
          setError('Tài khoản này đăng nhập bằng Google. Vui lòng đăng nhập bằng Google thay vì đặt lại mật khẩu.');
        } else if (response.status === 403) {
          setError('Tài khoản đã bị vô hiệu hóa. Vui lòng liên hệ hỗ trợ.');
        } else {
          setError(errorMessage);
        }
      }
    } catch (error: unknown) {
      console.error('Forgot password error:', error);
      setError('Lỗi kết nối. Vui lòng kiểm tra internet và thử lại.');
    } finally {
      setLoading(false);
    }
  };

  // Success state
  if (success) {
    return (
      <AuthLayout
        title="Email đã được gửi"
        subtitle={`Vui lòng kiểm tra hộp thư của bạn và làm theo hướng dẫn để đặt lại mật khẩu.`}
        imageSrc="/assets/images/email_success.png"
        imageAlt="Email sent successfully"
        headerVariant="auth"
      >
        <div className="bg-white rounded-lg p-4 mb-6">
          <p className="text-blue-800 text-sm">
            <span className="font-semibold">Email đã được gửi đến:</span> {email}
          </p>
        </div>
        
        <div className="space-y-4">
          <p className="text-gray-600 text-sm text-center">
            Không thấy email? Kiểm tra thư mục spam/junk hoặc thử gửi lại sau vài phút.
          </p>
          
          <div className="space-y-3">
            <button
              onClick={() => {
                setSuccess(false);
                setEmail('');
              }}
              className="w-full bg-orange-500 text-white py-3 px-4 rounded-lg hover:bg-orange-600 transition-colors font-medium"
            >
              Gửi lại email
            </button>
            
            <Link
              href="/auth/signin"
              className="w-full block text-center py-3 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium text-gray-700"
            >
              Quay lại đăng nhập
            </Link>
          </div>
        </div>
      </AuthLayout>
    );
  }

  // Main form
  return (
    <AuthLayout
      title="Quên mật khẩu?"
      subtitle="Nhập email của bạn và chúng tôi sẽ gửi link đặt lại mật khẩu"
      imageSrc="/assets/images/forgot_password.png"
      imageAlt="Forgot password illustration"
      headerVariant="auth"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Nhập địa chỉ email của bạn"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors"
            required
            disabled={loading}
          />
        </div>

        {error && (
          <div className="bg-white border border-red-200 rounded-lg p-3">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-orange-500 text-white py-3 px-4 rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {loading ? 'Đang gửi...' : 'Gửi link đặt lại mật khẩu'}
        </button>
      </form>

      <div className="text-center pt-4">
        <p className="text-gray-600 text-sm">
          Nhớ mật khẩu?{' '}
          <Link href="/auth/signin" className="text-orange-500 hover:text-orange-600 font-medium">
            Quay lại đăng nhập
          </Link>
        </p>
      </div>
    </AuthLayout>
  );
}
