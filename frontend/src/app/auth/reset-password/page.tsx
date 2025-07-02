'use client';

import { Suspense } from 'react';
import ResetPasswordContent from '@/components/auth/ResetPasswordContent';

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
