'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
// import Dashboard from '@/components/Dashboard';
import { storage } from '@/utils/api';

export default function DashboardPage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = storage.getToken();
    if (token) {
      setIsLoggedIn(true);
    } else {
      router.push('/auth/signin');
    }
    setLoading(false);
  }, [router]);

  const handleLogout = () => {
    setIsLoggedIn(false);
    router.push('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Đang tải...</p>
        </div>
      </div>
    );
  }

  if (!isLoggedIn) {
    return null;
  }

  // return <Dashboard onLogout={handleLogout} />;
}
