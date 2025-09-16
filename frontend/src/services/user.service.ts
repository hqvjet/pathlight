/**
 * =============================================================================
 * 👤 PATHLIGHT FRONTEND - USER SERVICES
 * =============================================================================
 * User management API services
 */

import { api } from '../lib/api-client';

// =============================================================================
// 🔧 TYPES & INTERFACES
// =============================================================================

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar_url?: string;
  is_verified: boolean;
  role: string;
  created_at: string;
  updated_at: string;
  last_login?: string;
  preferences?: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  notifications: {
    email: boolean;
    push: boolean;
    course_updates: boolean;
    quiz_reminders: boolean;
  };
  privacy: {
    profile_visibility: 'public' | 'private';
    show_progress: boolean;
  };
}

export interface UpdateProfileRequest {
  first_name?: string;
  last_name?: string;
  avatar_url?: string;
}

export interface UpdatePreferencesRequest {
  preferences: Partial<UserPreferences>;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface UserStats {
  total_courses: number;
  completed_courses: number;
  total_quizzes: number;
  completed_quizzes: number;
  average_score: number;
  study_streak: number;
  total_study_time: number; // in minutes
}

// =============================================================================
// 👤 USER SERVICES
// =============================================================================

export const userService = {
  /**
   * Get current user profile
   */
  // Spec uses GET /user/info for retrieval and PUT /user/change-info for updates
  async getInfo() { return api.get('/user/info'); },

  /**
   * Get user information (with optional id parameter)
   */
  // Deprecated getUserInfo alias removed

  /**
   * Update user profile (change-info endpoint)
   */
  async updateProfile(data: UpdateProfileRequest) { return api.put('/user/change-info', data); },

  /**
   * Get current user basic info
   */
  // Removed unsupported /user/me

  /**
   * Get user dashboard data
   */
  async getDashboard() {
  return api.get('/user/dashboard');
  },

  /**
   * Upload user avatar
   */
  async uploadAvatar(file: File) {
  return api.uploadFile('/user/avatar', file);
  },

  /**
   * Get user avatar by user ID
   */
  async getAvatar() {
  return api.get('/user/avatar');
  },

  /**
   * Set notification time for daily reminders
   */
  async setNotifyTime(data: { remind_time: string }) {
  return api.put('/user/notify-time', data);
  },

  /**
   * Save user activity milestone
   */
  async saveActivity() {
  return api.post('/user/activity');
  },

  /**
   * Get user activity data
   */
  async getActivity() {
  return api.get('/user/activity');
  },

  /**
   * Get users by IDs (for leaderboard avatars, etc.)
   */
  // Removed unsupported users-by-ids endpoint

  // =============================================================================
  // 👥 ADMIN USER MANAGEMENT
  // =============================================================================

  /**
   * Get all users (admin only)
   */
  async getAllUsers(page: number = 1, per_page: number = 20, search?: string) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: per_page.toString(),
    });
    
    if (search) {
      params.append('search', search);
    }

  return api.get(`/user/all?${params.toString()}`);
  },

  /**
   * Get user by ID (admin only)
   */
  // Removed admin-specific endpoints not present in spec (getUserById, updateUser, deleteUser, toggleUserBan, resetUserPassword, getUserStats)

  /**
   * Update user (admin only)
   */
};

export default userService;
