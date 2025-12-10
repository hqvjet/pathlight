/** User domain API helpers */
import { apiClient } from './http';

export const userApi = {
  getInfo: () => apiClient.get('/user/info'),
  // Spec: GET /user/info (optional id handled via query param externally)
  getDashboard: () => apiClient.get('/user/dashboard'),
  updateProfile: (data: unknown) => apiClient.put('/user/change-info', data),
  updateAvatar: (file: File) => apiClient.uploadFile('/user/avatar', file, { method: 'PUT' }, 'avatar_file'),
  getAvatar: (userId: string) => apiClient.get(`/user/avatar?user-id=${encodeURIComponent(userId)}`),
  setNotifyTime: (data: unknown) => apiClient.put('/user/notify-time', data),
  saveActivity: () => apiClient.post('/user/activity'),
  getAllUsers: () => apiClient.get('/user/all'),
};
