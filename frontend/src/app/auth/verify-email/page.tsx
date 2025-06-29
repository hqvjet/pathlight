'use client';

import { Suspense, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useRouter } from 'next/navigation';
import EmailVerificationResult from '@/components/EmailVerificationResult';
import { storage } from '@/utils/api';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');
  const [mounted, setMounted] = useState(false);

  // Đảm bảo component đã mount ở client-side
  useEffect(() => {
    setMounted(true);
  }, []);

  const handleBack = () => {
    router.push('/auth/signin');
  };

  const handleVerified = () => {
    router.push('/auth/signin');
  };

  const handleSetupRedirect = () => {
    router.push('/auth/study-time-setup');
  };

  // Nếu chưa mount, hiển thị loading
  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#F97316]"></div>
      </div>
    );
  }

  // Nếu có token trong URL, hiển thị kết quả xác thực
  if (token) {
    return <EmailVerificationResult onSetupRedirect={handleSetupRedirect} />;
  }

  // Nếu không có token, chuyển về signin
  router.push('/auth/signin');
  return null;
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#F97316]"></div>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
