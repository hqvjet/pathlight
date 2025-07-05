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
    return api.get<User>('/api/v1/user/profile');
  },

  /**
   * Update user profile
   */
  async updateProfile(data: UpdateProfileRequest) {
    return api.put<User>('/api/v1/user/profile', data);
  },

  /**
   * Update user preferences
   */
  async updatePreferences(data: UpdatePreferencesRequest) {
    return api.put<UserPreferences>('/api/v1/user/preferences', data);
  },

  /**
   * Get user preferences
   */
  async getPreferences() {
    return api.get<UserPreferences>('/api/v1/user/preferences');
  },

  /**
   * Upload user avatar
   */
  async uploadAvatar(file: File) {
    return api.uploadFile<{ avatar_url: string }>('/api/v1/user/avatar', file);
  },

  /**
   * Delete user avatar
   */
  async deleteAvatar() {
    return api.delete('/api/v1/user/avatar');
  },

  /**
   * Get user statistics
   */
  async getStats() {
    return api.get<UserStats>('/api/v1/user/stats');
  },

  /**
   * Get user activity history
   */
  async getActivityHistory(page: number = 1, per_page: number = 20) {
    return api.get<{
      activities: Array<{
        id: string;
        type: string;
        description: string;
        created_at: string;
        metadata?: unknown;
      }>;
      total: number;
      page: number;
      per_page: number;
    }>(`/api/v1/user/activity?page=${page}&per_page=${per_page}`);
  },

  /**
   * Delete user account
   */
  async deleteAccount(password: string) {
    return api.delete('/api/v1/user/account', {
      body: JSON.stringify({ password }),
    });
  },

  /**
   * Export user data
   */
  async exportData() {
    return api.get<{ download_url: string }>('/api/v1/user/export');
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

    return api.get<UserListResponse>(`/api/v1/admin/users?${params.toString()}`);
  },

  /**
   * Get user by ID (admin only)
   */
  async getUserById(id: string) {
    return api.get<User>(`/api/v1/admin/users/${id}`);
  },

  /**
   * Update user (admin only)
   */
  async updateUser(id: string, data: Partial<User>) {
    return api.put<User>(`/api/v1/admin/users/${id}`, data);
  },

  /**
   * Delete user (admin only)
   */
  async deleteUser(id: string) {
    return api.delete(`/api/v1/admin/users/${id}`);
  },

  /**
   * Ban/unban user (admin only)
   */
  async toggleUserBan(id: string, banned: boolean) {
    return api.post(`/api/v1/admin/users/${id}/ban`, { banned });
  },

  /**
   * Reset user password (admin only)
   */
  async resetUserPassword(id: string) {
    return api.post<{ temporary_password: string }>(`/api/v1/admin/users/${id}/reset-password`);
  },

  /**
   * Get user statistics (admin only)
   */
  async getUserStats(id: string) {
    return api.get<UserStats>(`/api/v1/admin/users/${id}/stats`);
  },
};

export default userService;
