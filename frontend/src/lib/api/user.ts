/** User domain API helpers */
import { apiClient } from './http';

export const userApi = {
  getProfile: () => apiClient.get('/api/users/profile'),
  getMe: () => apiClient.get('/api/users/me'),
  getDashboard: () => apiClient.get('/api/users/dashboard'),
  updateProfile: (data: unknown) => apiClient.put('/api/users/profile', data),
  updateAvatar: (file: File) => apiClient.uploadFile('/api/users/avatar', file),
  getAvatar: (userId: string) => apiClient.get(`/api/users/avatar?user_id=${userId}`),
  setNotifyTime: (data: unknown) => apiClient.put('/api/users/notify-time', data),
  saveActivity: () => apiClient.post('/api/users/activity'),
  getAllUsers: () => apiClient.get('/api/users'),
  getActivity: (year?: number) => apiClient.get(year ? `/api/users/activity?year=${year}` : '/api/users/activity'),
  getUsersByIds: (userIds: string[]) => apiClient.post('/api/users/users-by-ids', userIds),
};
