'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Dashboard from '@/components/user/Dashboard';
import { storage } from '@/utils/api';

function isJwtValid(token: string | null) {
  if (!token) return false;
  const parts = token.split('.');
  if (parts.length !== 3) return true; // non-JWT opaque token treat as valid
  try {
    const payload = JSON.parse(
      atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'))
    );
    if (!payload.exp) return true;
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

export default function DashboardPage() {
  const [authChecked, setAuthChecked] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = storage.getToken();
    if (!isJwtValid(token)) {
      // Clear possibly expired tokens
      storage.removeToken();
      const redirectParam = encodeURIComponent('/user/dashboard');
      router.replace(`/auth/signin?redirect=${redirectParam}`);
    } else {
      setAuthChecked(true);
    }
  }, [router, searchParams]);

  const handleLogout = () => {
    storage.removeToken();
    router.replace('/auth/signin');
  };

  if (!authChecked) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Đang tải...</p>
        </div>
      </div>
    );
  }

  return <Dashboard onLogout={handleLogout} />;
}
