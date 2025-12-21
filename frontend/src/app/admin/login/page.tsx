"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { showToast } from '@/utils/toast';
import authService from '@/services/auth.service';
import { storage } from '@/utils/api';

export default function AdminLoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username || !password) {
      showToast.error('Please enter both username and password');
      return;
    }

    setLoading(true);
    try {
      const response = await authService.adminSignIn({ username, password });

      if (response?.data?.access_token) {
        // Store admin token
        storage.setAuthToken(response.data.access_token);
        showToast.success('Welcome back, Admin!');
        router.push('/admin/dashboard');
      } else {
        showToast.error('Invalid admin credentials');
      }
    } catch (error: unknown) {
      console.error('Admin login error:', error);
      if (typeof error === 'object' && error && 'response' in error) {
        const errResponse = (error as { response?: { data?: { detail?: string } } }).response;
        showToast.error(errResponse?.data?.detail || 'Login failed. Please check your credentials.');
      } else {
        showToast.error('Login failed. Please check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-rose-50 to-amber-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-orange-500 to-rose-500 rounded-2xl mb-4 shadow-lg">
            <span className="text-4xl">🎓</span>
          </div>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">PathLight Admin</h1>
          <p className="text-gray-600">Welcome back! Please sign in to continue</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username Field */}
            <div>
              <label htmlFor="username" className="block text-sm font-semibold text-gray-700 mb-2">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
                disabled={loading}
                autoComplete="username"
                autoFocus
              />
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent pr-12 transition-all"
                  disabled={loading}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 text-xl transition-colors"
                  disabled={loading}
                  tabIndex={-1}
                >
                  {showPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-orange-500 to-rose-500 text-white font-semibold py-3.5 px-4 rounded-xl hover:from-orange-600 hover:to-rose-600 focus:outline-none focus:ring-4 focus:ring-orange-300 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Security Notice */}
          <div className="mt-6 p-4 bg-orange-50 border-2 border-orange-200 rounded-xl">
            <div className="flex items-start">
              <span className="text-orange-600 mr-2 text-lg">🔒</span>
              <div>
                <p className="text-xs font-semibold text-orange-900">Secure Admin Access</p>
                <p className="text-xs text-orange-700 mt-1">
                  This area is for authorized administrators only. All activities are monitored.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Back to Home Link */}
        <div className="text-center mt-6">
          <button
            onClick={() => router.push('/')}
            className="text-gray-500 hover:text-orange-600 text-sm font-medium transition-colors inline-flex items-center gap-1"
          >
            <span>←</span> Back to Home
          </button>
        </div>
      </div>
    </div>
  );
}