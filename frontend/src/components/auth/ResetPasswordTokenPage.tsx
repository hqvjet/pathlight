"use client";

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { showToast } from '@/utils/toast';
import { api } from '@/lib/api-client';
import ResetPasswordLayout from '@/components/layout/ResetPasswordLayout';

export default function ResetPasswordTokenPage() {
  const [passwords, setPasswords] = useState({ new: '', confirm: '' });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [tokenValid, setTokenValid] = useState<'pending' | 'valid' | 'invalid'>('pending');
  const params = useParams();
  const token = params.token as string;

  const validateToken = useCallback(async () => {
    try {
      const response = await api.auth.validateResetToken(token);

      if (response.status === 200) {
        setTokenValid('valid');
      } else {
        setTokenValid('invalid');
        showToast.error(response.error || 'Token không hợp lệ hoặc đã hết hạn');
      }
    } catch {
      setTokenValid('invalid');
      showToast.error('Token không hợp lệ hoặc đã hết hạn');
    }
  }, [token]);

  useEffect(() => {
    if (!token) {
      showToast.error('Token không hợp lệ');
      setTokenValid('invalid');
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

  if (success) {
    return (
      <ResetPasswordLayout
        title="Đặt lại mật khẩu thành công"
        subtitle="Bạn có thể đăng nhập bằng mật khẩu mới."
        icon="success"
        imageSrc="/assets/images/email_success.png"
      >
        <div className="space-y-6 text-center">
          <p className="text-base text-gray-600">Tài khoản của bạn đã sẵn sàng để sử dụng.</p>
          <Link
            href="/auth/signin"
            className="w-full flex justify-center py-4 px-4 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors font-medium text-base shadow-sm hover:shadow-md"
          >
            Đăng nhập ngay →
          </Link>
        </div>
      </ResetPasswordLayout>
    );
  }

  if (tokenValid === 'invalid') {
    return (
      <ResetPasswordLayout
        title="Liên kết không hợp lệ"
        subtitle="Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn."
        icon="error"
        imageSrc="/assets/images/error_page.png"
      >
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
      </ResetPasswordLayout>
    );
  }

  if (tokenValid === 'pending') {
    return (
      <ResetPasswordLayout
        title="Đang kiểm tra liên kết"
        subtitle="Vui lòng đợi trong giây lát"
        icon="warning"
        imageSrc="/assets/images/reset-password.png"
      >
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500" aria-label="Đang tải" />
        </div>
      </ResetPasswordLayout>
    );
  }

  return (
    <ResetPasswordLayout
      title="Đặt Lại Mật Khẩu"
      subtitle="Nhập mật khẩu mới cho tài khoản của bạn. Hãy chọn mật khẩu mạnh để bảo vệ tài khoản."
      icon="warning"
      imageSrc="/assets/images/reset-password.png"
    >
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
        <div className="text-center">
          <Link
            href="/auth/signin"
            className="inline-flex items-center justify-center px-6 py-3 border-2 border-orange-500 text-orange-500 rounded-lg hover:bg-orange-500 hover:text-white transition-all duration-200 font-medium text-base shadow-sm hover:shadow-md"
          >
            ← Quay lại đăng nhập
          </Link>
        </div>
      </form>
    </ResetPasswordLayout>
  );
}
