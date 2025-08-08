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
    return api.get<User>('/api/users/profile');
  },

  /**
   * Get user information (with optional id parameter)
   */
  async getUserInfo(id?: string) {
    const endpoint = id ? `/api/users/info?id=${id}` : '/api/users/info';
    return api.get<User>(endpoint);
  },

  /**
   * Update user profile (change-info endpoint)
   */
  async updateProfile(data: UpdateProfileRequest) {
    return api.put<User>('/api/users/profile', data);
  },

  /**
   * Get current user basic info
   */
  async getMe() {
    return api.get('/api/users/me');
  },

  /**
   * Get user dashboard data
   */
  async getDashboard() {
    return api.get('/api/users/dashboard');
  },

  /**
   * Upload user avatar
   */
  async uploadAvatar(file: File) {
    return api.uploadFile<{ message: string; avatar_url?: string }>('/api/users/avatar', file);
  },

  /**
   * Get user avatar by user ID
   */
  async getAvatar(userId: string) {
    return api.get(`/api/users/avatar?user_id=${userId}`);
  },

  /**
   * Set notification time for daily reminders
   */
  async setNotifyTime(data: { remind_time: string }) {
    return api.put('/api/users/notify-time', data);
  },

  /**
   * Save user activity milestone
   */
  async saveActivity() {
    return api.post('/api/users/activity');
  },

  /**
   * Get user activity data
   */
  async getActivity(year?: number) {
    const endpoint = year ? `/api/users/activity?year=${year}` : '/api/users/activity';
    return api.get(endpoint);
  },

  /**
   * Get users by IDs (for leaderboard avatars, etc.)
   */
  async getUsersByIds(userIds: string[]) {
    return api.post<Record<string, User>>('/api/users/users-by-ids', userIds);
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

    return api.get<UserListResponse>(`/api/users?${params.toString()}`);
  },

  /**
   * Get user by ID (admin only)
   */
  async getUserById(id: string) {
    return api.get<User>(`/api/users/${id}`);
  },

  /**
   * Update user (admin only)
   */
  async updateUser(id: string, data: Partial<User>) {
    return api.put<User>(`/api/users/${id}`, data);
  },

  /**
   * Delete user (admin only)
   */
  async deleteUser(id: string) {
    return api.delete(`/api/users/${id}`);
  },

  /**
   * Ban/unban user (admin only)
   */
  async toggleUserBan(id: string, banned: boolean) {
    return api.post(`/api/users/${id}/ban`, { banned });
  },

  /**
   * Reset user password (admin only)
   */
  async resetUserPassword(id: string) {
    return api.post<{ temporary_password: string }>(`/api/users/${id}/reset-password`);
  },

  /**
   * Get user statistics (admin only)
   */
  async getUserStats(id: string) {
    return api.get<UserStats>(`/api/users/${id}/stats`);
  },
};

export default userService;
