'use client';

import { Suspense } from 'react';
import EmailNotFoundContent from '@/components/auth/EmailNotFoundContent';

export default function EmailNotFoundPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <EmailNotFoundContent />
    </Suspense>
  );
}
