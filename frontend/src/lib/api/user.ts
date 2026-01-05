/** User domain API helpers */
import { apiClient } from './http';

export const userApi = {
  getInfo: () => apiClient.get('/user/info'),
  getDashboard: () => apiClient.get('/user/dashboard'),
  updateProfile: (data: unknown) => apiClient.put('/user/change-info', data),
  updateAvatar: (file: File) => apiClient.uploadFile('/user/avatar', file, { method: 'PUT' }, 'avatar_file'),
  getAvatar: (userId: string) => apiClient.get(`/user/avatar?user-id=${encodeURIComponent(userId)}`),
  setNotifyTime: (data: unknown) => apiClient.put('/user/notify-time', data),
  addExperience: (data: { exp: number }) => apiClient.post('/user/experience/add', data),
  logActivity: (event: string) => apiClient.post('/user/activity', { event }),
  getActivity: (days = 365) => apiClient.get(`/user/activity?days=${days}`),
  getAllUsers: () => apiClient.get('/user/admin/users'),
  batchUsers: (userIds: string[]) => apiClient.post('/user/users/batch', userIds),
};

/** Course domain API helpers - microservice */
export const courseApi = {
  getStats: () => apiClient.get('/course/stats'),
  getAll: () => apiClient.get('/course/all'),
};

/** Quiz domain API helpers - microservice */
export const quizApi = {
  getStats: () => apiClient.get('/quiz/stats'),
  getAll: () => apiClient.get('/quiz/all'),
};
