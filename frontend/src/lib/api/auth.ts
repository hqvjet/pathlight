/** Auth domain API helpers */
import { apiClient } from './http';

export const authApi = {
  signin: (data: unknown) => apiClient.post('/signin', data),
  signup: (data: unknown) => apiClient.post('/signup', data),
  signout: () => apiClient.post('/signout'),
  verifyEmail: (token: string) => apiClient.get(`/verify-email?token=${token}`),
  resendVerification: (email: string) => apiClient.post('/resend-verification', { email }),
  forgotPassword: (email: string) => apiClient.post('/forget-password', { email }),
  validateResetToken: (token: string) => apiClient.get(`/validate-reset-token/${token}`),
  resetPassword: (token: string, data: unknown) => apiClient.post(`/reset-password/${token}`, data),
  changePassword: (data: unknown) => apiClient.post('/change-password', data),
  oauthSignin: (data: unknown) => apiClient.post('/oauth-signin', data),
  refresh: (refreshToken: string) => apiClient.post('/refresh', { refresh_token: refreshToken }),
};
