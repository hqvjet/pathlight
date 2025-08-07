"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import EmailSentPage from '@/components/auth/EmailSentPage';
import { api } from '@/lib/api-client';
import { storage } from '@/utils/api';

export default function EmailSentRoute() {
  const router = useRouter();
  const [email, setEmail] = useState<string>('');
  const [isResending, setIsResending] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  useEffect(() => {
    // Get pending email from localStorage
    const pendingEmail = storage.getPendingEmail();
    if (pendingEmail) {
      setEmail(pendingEmail);
    } else {
      // If no pending email, redirect to signup
      router.push('/auth/signup');
    }
  }, [router]);

  const handleResendEmail = async () => {
    if (!email || isResending) return;

    setIsResending(true);
    setResendMessage('');

    try {
      const response = await api.auth.resendVerification(email);

      if (response.status === 200) {
        setResendMessage('Email xác nhận đã được gửi lại thành công!');
        setTimeout(() => setResendMessage(''), 5000);
      } else {
        setResendMessage(response.error || 'Gửi lại email thất bại. Vui lòng thử lại.');
      }
    } catch (error) {
      console.error('Resend email error:', error);
      setResendMessage('Lỗi kết nối. Vui lòng thử lại.');
    } finally {
      setIsResending(false);
    }
  };

  if (!email) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      {resendMessage && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg ${
          resendMessage.includes('thành công') 
            ? 'bg-green-500 text-white' 
            : 'bg-red-500 text-white'
        }`}>
          {resendMessage}
        </div>
      )}
      <EmailSentPage 
        email={email} 
        onResendEmail={handleResendEmail}
        isResending={isResending}
      />
    </div>
  );
}
