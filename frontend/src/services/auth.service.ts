/**
 * =============================================================================
 * 🔐 PATHLIGHT FRONTEND - AUTHENTICATION SERVICES
 * =============================================================================
 * Authentication related API services using the new API client
 */

import { api } from '../lib/api';

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
    return api.auth.signin(data);
  },

  /**
   * Sign up with email and password
   */
  async signUp(data: SignUpRequest) {
    return api.auth.signup(data);
  },

  /**
   * Sign out
   */
  async signOut() {
    return api.auth.signout();
  },

  /**
   * Google OAuth sign in
   */
  async googleSignIn(data: GoogleAuthRequest) {
    return api.auth.oauthSignin(data);
  },

  /**
   * Forgot password
   */
  async forgotPassword(data: ForgotPasswordRequest) {
    return api.auth.forgotPassword(data.email);
  },

  /**
   * Reset password with token
   */
  async resetPassword(data: ResetPasswordRequest) {
    return api.auth.resetPassword(data.token, {
      password: data.password,
      confirm_password: data.confirm_password,
    });
  },

  /**
   * Change password (authenticated)
   */
  async changePassword(data: ChangePasswordRequest) {
    return api.auth.changePassword(data);
  },

  /**
   * Verify email with token
   */
  async verifyEmail(data: VerifyEmailRequest) {
    return api.auth.verifyEmail(data.token);
  },

  /**
   * Resend email verification
   */
  async resendVerification(data: ResendVerificationRequest) {
    return api.auth.resendVerification(data.email);
  },

  /**
   * Admin sign in
   */
  async adminSignIn(data: SignInRequest) {
    return api.auth.adminSignin(data);
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string) {
    return api.auth.refresh(refreshToken);
  },

  /**
   * Get current user profile
   */
  async getCurrentUser() {
    return api.auth.me();
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
