"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import ResetPasswordLayout from "@/components/layout/ResetPasswordLayout";

export default function EmailNotFoundContent() {
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";

  return (
    <ResetPasswordLayout
      title="Email không tồn tại"
      subtitle={`Email "${email}" không tồn tại trong hệ thống của chúng tôi. Vui lòng kiểm tra lại địa chỉ email hoặc tạo tài khoản mới.`}
      icon="error"
      imageSrc="/assets/images/error_page.png"
    >
      <div className="space-y-4">
        <div className="bg-white border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-base">
            <span className="font-semibold">Email đã nhập:</span> {email}
          </p>
        </div>
        <div className="space-y-3">
          <Link
            href="/auth/forgot-password"
            className="w-full flex justify-center py-4 px-4 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors font-medium text-base"
          >
            Thử email khác
          </Link>
          <Link
            href="/auth/signup"
            className="w-full flex justify-center py-4 px-4 border border-orange-500 text-orange-500 rounded-lg hover:bg-orange-50 transition-colors font-medium text-base"
          >
            Tạo tài khoản mới
          </Link>
          <Link
            href="/auth/signin"
            className="w-full flex justify-center py-4 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium text-base"
          >
            Quay lại đăng nhập
          </Link>
        </div>
      </div>
    </ResetPasswordLayout>
  );
}
