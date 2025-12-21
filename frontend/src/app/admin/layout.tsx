"use client";
import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { storage } from '@/utils/api';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Skip auth check for login page
    if (pathname === '/admin/login') {
      setLoading(false);
      return;
    }

    // Check if admin token exists
    const token = storage.getAuthToken();
    if (!token) {
      router.push('/admin/login');
      return;
    }

    setIsAuthenticated(true);
    setLoading(false);
  }, [pathname, router]);

  // Show nothing while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Allow login page to render without auth
  if (pathname === '/admin/login') {
    return <>{children}</>;
  }

  // Require authentication for all other admin pages
  if (!isAuthenticated) {
    return null;
  }

  const tabs = [
    { name: 'Dashboard', path: '/admin/dashboard', icon: '📊' },
    { name: 'Users', path: '/admin/users', icon: '👥' },
    { name: 'Courses', path: '/admin/courses', icon: '📚' },
    { name: 'Quizzes', path: '/admin/quizzes', icon: '📝' },
    { name: 'Costs', path: '/admin/costs', icon: '💰' },
    { name: 'Logs', path: '/admin/log', icon: '📋' },
  ];

  const handleLogout = () => {
    storage.clearAuthToken();
    router.push('/admin/login');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 bg-white border-r border-slate-200 flex-col p-4 gap-4 shadow-sm sticky top-0 h-screen">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase text-slate-500">PathLight</p>
            <p className="text-lg font-bold text-slate-900">Admin</p>
          </div>
          <span className="text-xl">🛡️</span>
        </div>
        <nav className="flex-1 space-y-1">
          {tabs.map((tab) => {
            const isActive = pathname === tab.path;
            return (
              <Link
                key={tab.path}
                href={tab.path}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 border border-blue-100 shadow-sm'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <span className="text-lg" aria-hidden>{tab.icon}</span>
                <span>{tab.name}</span>
              </Link>
            );
          })}
        </nav>
        <div className="space-y-2 text-sm text-slate-600">
          <button
            onClick={() => router.push('/')}
            className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-100"
          >
            ← Back to site
          </button>
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-2 rounded-lg text-red-600 hover:bg-red-50"
          >
            Logout
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 min-w-0">
        <header className="bg-white border-b border-slate-200 px-4 sm:px-6 lg:px-8 py-4 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs uppercase text-slate-500">Admin Console</p>
            <h1 className="text-2xl font-bold text-slate-900">{tabs.find(t => t.path === pathname)?.name || 'Dashboard'}</h1>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <span className="hidden sm:inline">👤 Admin</span>
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100"
            >
              Logout
            </button>
          </div>
        </header>
        <main className="px-4 sm:px-6 lg:px-8 py-8">{children}</main>
      </div>
    </div>
  );
}
