"use client";

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import ResetPasswordLayout from '@/components/layout/ResetPasswordLayout';

export default function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  useEffect(() => {
    if (token) {
      // Redirect to the token-specific page
      router.replace(`/auth/reset-password/${token}`);
    }
  }, [token, router]);

  // If no token is provided, show invalid link message
  return (
    <ResetPasswordLayout
      title="Liên kết không hợp lệ"
      subtitle="Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn. Vui lòng yêu cầu đặt lại mật khẩu mới."
      icon="error"
      imageSrc="/assets/images/reset-password.png"
    >
      <div className="space-y-4">
        <Link 
          href="/auth/forgot-password"
          className="w-full flex justify-center py-4 px-4 text-base bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors font-medium shadow-sm hover:shadow-md"
        >
          Yêu cầu đặt lại mật khẩu mới
        </Link>
        <Link 
          href="/auth/signin"
          className="w-full flex justify-center py-4 px-4 text-base border-2 border-orange-500 text-orange-500 rounded-lg hover:bg-orange-500 hover:text-white transition-all duration-200 font-medium shadow-sm hover:shadow-md"
        >
          Quay lại đăng nhập
        </Link>
      </div>
    </ResetPasswordLayout>
  );
}
