/** User domain API helpers */
import { apiClient } from './http';

export const userApi = {
  getProfile: () => apiClient.get('/api/user/profile'),
  getMe: () => apiClient.get('/api/user/me'),
  getDashboard: () => apiClient.get('/api/user/dashboard'),
  updateProfile: (data: unknown) => apiClient.put('/api/user/profile', data),
  updateAvatar: (file: File) => apiClient.uploadFile('/api/user/avatar', file),
  getAvatar: (userId: string) => apiClient.get(`/api/user/avatar?user-id=${encodeURIComponent(userId)}`),
  setNotifyTime: (data: unknown) => apiClient.put('/api/user/notify-time', data),
  saveActivity: () => apiClient.post('/api/user/activity'),
  getAllUsers: () => apiClient.get('/api/user'),
  getActivity: () => apiClient.get('/api/user/activity'),
  getUsersByIds: (userIds: string[]) => apiClient.post('/api/user/users-by-ids', userIds),
};
