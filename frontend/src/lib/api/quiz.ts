/** Quiz domain API helpers */
import { apiClient } from './http';

export const quizApi = {
  getAll: (params?: Record<string, unknown>) => {
    const queryString = params ? '?' + new URLSearchParams(params as Record<string, string>).toString() : '';
    return apiClient.get(`/quizzes${queryString}`);
  },
  getById: (id: string) => apiClient.get(`/quizzes/${id}`),
  create: (data: unknown) => apiClient.post('/quizzes', data),
  update: (id: string, data: unknown) => apiClient.put(`/quizzes/${id}`, data),
  delete: (id: string) => apiClient.delete(`/quizzes/${id}`),
  submit: (id: string, answers: unknown) => apiClient.post(`/quizzes/${id}/submit`, { answers }),
  getResult: (id: string) => apiClient.get(`/quizzes/${id}/result`),
  getHistory: () => apiClient.get('/quizzes/history'),
};
