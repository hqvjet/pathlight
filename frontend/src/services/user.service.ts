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
  async getProfile() {
    return api.get('/api/user/profile');
  },

  /**
   * Get user information (with optional id parameter)
   */
  async getUserInfo(id?: string) {
    return api.get('/api/user/info');
  },

  /**
   * Update user profile (change-info endpoint)
   */
  async updateProfile(data: UpdateProfileRequest) {
    return api.put('/api/user/profile', data);
  },

  /**
   * Get current user basic info
   */
  async getMe() {
    return api.get('/api/user/me');
  },

  /**
   * Get user dashboard data
   */
  async getDashboard() {
    return api.get('/api/user/dashboard');
  },

  /**
   * Upload user avatar
   */
  async uploadAvatar(file: File) {
    return api.uploadFile('/api/user/avatar', file);
  },

  /**
   * Get user avatar by user ID
   */
  async getAvatar(userId: string) {
    return api.get('/api/user/avatar');
  },

  /**
   * Set notification time for daily reminders
   */
  async setNotifyTime(data: { remind_time: string }) {
    return api.put('/api/user/notify-time', data);
  },

  /**
   * Save user activity milestone
   */
  async saveActivity() {
    return api.post('/api/user/activity');
  },

  /**
   * Get user activity data
   */
  async getActivity(year?: number) {
    return api.get('/api/user/activity');
  },

  /**
   * Get users by IDs (for leaderboard avatars, etc.)
   */
  async getUsersByIds(userIds: string[]) {
    return api.post('/api/user/users-by-ids', userIds);
  },

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

    return api.get(`/api/user?${params.toString()}`);
  },

  /**
   * Get user by ID (admin only)
   */
  async getUserById(id: string) {
    return api.get(`/api/user/${id}`);
  },

  /**
   * Update user (admin only)
   */
  async updateUser(id: string, data: Partial<User>) {
    return api.put(`/api/user/${id}`, data);
  },

  /**
   * Delete user (admin only)
   */
  async deleteUser(id: string) {
    return api.delete(`/api/user/${id}`);
  },

  /**
   * Ban/unban user (admin only)
   */
  async toggleUserBan(id: string, banned: boolean) {
    return api.post(`/api/user/${id}/ban`, { banned });
  },

  /**
   * Reset user password (admin only)
   */
  async resetUserPassword(id: string) {
    return api.post(`/api/user/${id}/reset-password`);
  },

  /**
   * Get user statistics (admin only)
   */
  async getUserStats(id: string) {
    return api.get(`/api/user/${id}/stats`);
  },
};

export default userService;
