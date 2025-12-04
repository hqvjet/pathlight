'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import AuthLayout from '@/components/layout/AuthLayout';
import GoogleAuthButton from './GoogleAuthButton';
import { useSignIn } from './signin/hooks';

export default function SignInForm() {
  const { formData, setFormData, rememberMe, setRememberMe, loading, handleSubmit, signInWithPopup } = useSignIn();

  return (
    <AuthLayout
      title="Chào Mừng Trở Lại"
      subtitle="Đăng nhập để tiếp tục"
      imageSrc="/assets/images/login.png"
      imageAlt="Login illustration"
      headerVariant="auth"
    >
      <form className="space-y-5 sm:space-y-6" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
          <input
            id="email"
            type="email"
            required
            placeholder="Nhập email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-red-500 focus:border-red-500 sm:text-sm"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">Mật Khẩu</label>
          <input
            id="password"
            type="password"
            required
            placeholder="Nhập mật khẩu"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-red-500 focus:border-red-500 sm:text-sm"
          />
        </div>

        <div className="flex justify-between items-center text-sm">
          <label className="flex items-center gap-2 text-muted-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
            />
            <span>Ghi nhớ đăng nhập</span>
          </label>
          <Link href="/auth/forgot-password" className="text-muted-foreground hover:text-primary transition-colors">Quên mật khẩu?</Link>
        </div>

        <Button type="submit" disabled={loading} className="w-full bg-gray-900 hover:bg-gray-800 text-white" size="lg">
          {loading ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Đang đăng nhập...
            </div>
          ) : 'Đăng Nhập →'}
        </Button>

        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-200" /></div>
          <div className="relative flex justify-center text-sm"><span className="px-6 bg-white text-muted-foreground">Đăng Nhập Với</span></div>
        </div>

        <GoogleAuthButton onClick={signInWithPopup} loading={loading} />
      </form>
    </AuthLayout>
  );
}
