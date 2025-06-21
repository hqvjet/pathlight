export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const endpoints = {
  signin: '/api/v1/signin',
  signup: '/api/v1/signup',
  signout: '/api/v1/signout',
  forgotPassword: '/api/v1/forget-password',
  changePassword: '/api/v1/user/change-password',
  adminSignin: '/api/v1/admin/signin',
  verifyEmail: '/api/v1/verify-email',
  resendVerification: '/api/v1/resend-verification',
  oauthSignin: '/api/v1/oauth-signin'
};

export const storage = {
  getToken: () => typeof window !== 'undefined' ? localStorage.getItem('token') : null,
  setToken: (token: string) => typeof window !== 'undefined' && localStorage.setItem('token', token),
  removeToken: () => typeof window !== 'undefined' && localStorage.removeItem('token'),
  getPendingEmail: () => typeof window !== 'undefined' ? localStorage.getItem('pending_email') : null,
  setPendingEmail: (email: string) => typeof window !== 'undefined' && localStorage.setItem('pending_email', email),
  removePendingEmail: () => typeof window !== 'undefined' && localStorage.removeItem('pending_email')
};
