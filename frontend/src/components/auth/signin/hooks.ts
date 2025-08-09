import { useState, useEffect } from 'react';
import { api } from '@/lib/api-client';
import { storage } from '@/utils/api';
import { showToast } from '@/utils/toast';
import { AuthResponse } from '@/utils/types';
import { useRouter } from 'next/navigation';
import { useGoogleOAuth } from '@/hooks/useGoogleOAuth';

function jwtExpired(token: string | null) {
  if (!token) return true;
  const parts = token.split('.');
  if (parts.length !== 3) return false; // treat opaque as not expired
  try { const payload = JSON.parse(atob(parts[1].replace(/-/g,'+').replace(/_/g,'/'))); if (!payload.exp) return false; return payload.exp * 1000 <= Date.now(); } catch { return true; }
}

export function useSignIn() {
  const router = useRouter();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [redirectTarget, setRedirectTarget] = useState<string>('/user/dashboard');

  useEffect(() => { setRememberMe(storage.isRemembered()); }, []);
  useEffect(() => {
    try {
      const token = storage.getToken();
      if (token && !jwtExpired(token)) {
        router.replace(redirectTarget);
      } else if (token && jwtExpired(token)) {
        storage.removeToken();
      }
    } catch {}
  }, [router, redirectTarget]);
  useEffect(() => {
    try {
      const url = new URL(window.location.href);
      const redirect = url.searchParams.get('redirect');
      if (redirect) setRedirectTarget(redirect);
    } catch {}
  }, []);

  const finalizeLogin = () => {
    showToast.authSuccess('Đăng nhập thành công!');
    router.push(redirectTarget);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true);
    try {
      const response = await api.auth.signin(formData);
      if (response.status !== 200) { handleAuthError(response.status, response.error); return; }
      const result = response.data as AuthResponse & { message?: string };
      if (result?.access_token) {
        storage.setToken(result.access_token, rememberMe);
        finalizeLogin();
      } else if (result?.message === 'Email chưa được xác thực') {
        showToast.warning('Email chưa được xác thực. Chuyển đến trang xác thực...'); storage.setPendingEmail(formData.email); setTimeout(()=> router.push('/auth/verify-email'), 1500);
      } else showToast.authError(result?.message || 'Đăng nhập thất bại');
    } catch { showToast.authError('Lỗi kết nối. Vui lòng thử lại.'); }
    finally { setLoading(false); }
  };

  const handleGoogleSuccess = async (googleUser: unknown) => {
    setLoading(true);
    try {
      const response = await api.auth.oauthSignin(googleUser);
      if (response.status !== 200) { handleOAuthError(response.status, response.error); return; }
      const result = response.data as AuthResponse & { message?: string };
      if (result?.access_token) { storage.setToken(result.access_token, rememberMe); finalizeLogin(); }
      else showToast.authError(result?.message || 'Đăng nhập Google thất bại');
    } catch { showToast.authError('Lỗi kết nối. Vui lòng thử lại.'); }
    finally { setLoading(false); }
  };

  const { signInWithPopup } = useGoogleOAuth({ onSuccess: handleGoogleSuccess, onError: () => showToast.authError('Đăng nhập Google thất bại') });

  const handleAuthError = (status: number, error?: string) => {
    let msg = 'Đăng nhập thất bại'; if (error) msg = error; else {
      switch(status){ case 400: msg='Thông tin đăng nhập không hợp lệ'; break; case 401: msg='Email hoặc mật khẩu không đúng'; break; case 404: msg='Tài khoản không tồn tại'; break; case 500: msg='Lỗi server. Vui lòng thử lại sau'; break; default: msg=`Đăng nhập thất bại (Mã lỗi: ${status})`; }
    } showToast.authError(msg);
  };
  const handleOAuthError = (status: number, error?: string) => {
    let msg = 'Đăng nhập Google thất bại'; if (error) msg = error; else {
      switch(status){ case 400: msg='Thông tin Google không hợp lệ'; break; case 401: msg='Xác thực Google thất bại'; break; case 500: msg='Lỗi server. Vui lòng thử lại sau'; break; default: msg=`Đăng nhập Google thất bại (Mã lỗi: ${status})`; }
    } showToast.authError(msg);
  };

  return { formData, setFormData, rememberMe, setRememberMe, loading, handleSubmit, signInWithPopup };
}
