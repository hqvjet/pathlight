/**
 * =============================================================================
 * 🔐 PATHLIGHT FRONTEND - AUTHENTICATION SERVICES
 * =============================================================================
 * Authentication related API services using the new API client
 */

import { api } from '../lib/api-client';
import { endpoints } from '../utils/api';

// =============================================================================
// 🔧 TYPES & INTERFACES
// =============================================================================

export interface SignInRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface SignUpRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  confirm_password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    avatar_url?: string;
    is_verified: boolean;
    role: string;
  };
}

export interface GoogleAuthRequest {
  credential: string;
  email: string;
  google_id: string;
  given_name: string;
  family_name: string;
  avatar_id?: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  confirm_password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface VerifyEmailRequest {
  token: string;
}

export interface ResendVerificationRequest {
  email: string;
}

// =============================================================================
// 🔐 AUTHENTICATION SERVICES
// =============================================================================

export const authService = {
  /**
   * Sign in with email and password
   */
  async signIn(data: SignInRequest) {
    return api.post(endpoints.signin, data);
  },

  /**
   * Sign up with email and password
   */
  async signUp(data: SignUpRequest) {
    return api.post(endpoints.signup, data);
  },

  /**
   * Sign out
   */
  async signOut() {
    return api.post(endpoints.signout);
  },

  /**
   * Google OAuth sign in
   */
  async googleSignIn(data: GoogleAuthRequest) {
    return api.post(endpoints.oauthSignin, data);
  },

  /**
   * Forgot password
   */
  async forgotPassword(data: ForgotPasswordRequest) {
    return api.post(endpoints.forgotPassword, data);
  },

  /**
   * Reset password with token
   */
  async resetPassword(data: ResetPasswordRequest) {
    return api.post('/api/v1/reset-password', data);
  },

  /**
   * Change password (authenticated)
   */
  async changePassword(data: ChangePasswordRequest) {
    return api.post(endpoints.changePassword, data);
  },

  /**
   * Verify email with token
   */
  async verifyEmail(data: VerifyEmailRequest) {
    return api.post(endpoints.verifyEmail, data);
  },

  /**
   * Resend email verification
   */
  async resendVerification(data: ResendVerificationRequest) {
    return api.post(endpoints.resendVerification, data);
  },

  /**
   * Admin sign in
   */
  async adminSignIn(data: SignInRequest) {
    return api.post(endpoints.adminSignin, data);
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string) {
    return api.post(
      '/api/v1/auth/refresh',
      { refresh_token: refreshToken },
      { skipAuth: true }
    );
  },

  /**
   * Get current user profile
   */
  async getCurrentUser() {
    return api.get('/api/v1/auth/me');
  },

  /**
   * Check if user is authenticated
   */
  async isAuthenticated() {
    try {
      const response = await this.getCurrentUser();
      return response.success;
    } catch {
      return false;
    }
  },
};

export default authService;
