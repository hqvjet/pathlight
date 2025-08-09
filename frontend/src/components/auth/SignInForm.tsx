'use client';

import Link from 'next/link';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import { Montserrat } from 'next/font/google';
import Header from '../layout/Header';
import { Button } from '@/components/ui/button';
import { useSignIn } from './signin/hooks';

const montserrat = Montserrat({
  subsets: ['latin', 'vietnamese'],
  display: 'swap',
});

export default function SignInForm() {
  const { formData, setFormData, rememberMe, setRememberMe, loading, handleSubmit, signInWithPopup } = useSignIn();

  return (
    <div className={cn('h-screen bg-background flex flex-col overflow-hidden', montserrat.className)}>
      <Header 
        variant="auth" 
        showSocialLinks={false}
        backgroundColor="white"
        authNavigation={
          <div className="text-sm flex items-center">
            <span className="text-muted-foreground mr-4">Chưa có tài khoản?</span>
            <Button asChild variant="secondary" className="bg-[#FFF7ED] text-[#F97316] hover:opacity-90">
              <Link href="/auth/signup">Đăng Ký Ngay</Link>
            </Button>
          </div>
        }
      />

      <div className="flex flex-1 h-[calc(100vh-80px)]">
        <div className="hidden lg:flex lg:w-1/2 items-center justify-center p-4 xl:p-6 bg-gray-50">
          <div className="w-full max-w-2xl">
            <Image src="/assets/images/login.png" alt="Login illustration" width={700} height={700} className="object-contain w-full h-auto" />
          </div>
        </div>

        <div className="w-full lg:w-1/2 flex items-center justify-center bg-white px-4 sm:px-6 lg:px-8 py-4">
          <div className="w-full max-w-lg">
            <h2 className="text-3xl sm:text-4xl font-bold text-center text-red-900 mb-6 sm:mb-8">Chào Mừng Trở Lại</h2>

            <form className="space-y-5 sm:space-y-6" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
                <div className="mt-1">
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
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">Mật Khẩu</label>
                <div className="mt-1">
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

              <Button type="button" variant="outline" onClick={signInWithPopup} disabled={loading} className="w-full" size="lg">
                <div className="flex items-center justify-center w-6 h-6 mr-4">
                  <svg viewBox="0 0 24 24" className="w-6 h-6"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                </div>
                <span>Google</span>
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
