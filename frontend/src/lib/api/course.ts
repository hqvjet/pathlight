/** Course domain API helpers */
import { apiClient } from './http';

export const courseApi = {
  getAll: (params?: Record<string, unknown>) => {
    const queryString = params ? '?' + new URLSearchParams(params as Record<string, string>).toString() : '';
    return apiClient.get(`/courses${queryString}`);
  },
  getById: (id: string) => apiClient.get(`/courses/${id}`),
  create: (data: unknown) => apiClient.post('/courses', data),
  update: (id: string, data: unknown) => apiClient.put(`/courses/${id}`, data),
  delete: (id: string) => apiClient.delete(`/courses/${id}`),
  enroll: (id: string) => apiClient.post(`/courses/${id}/enroll`),
  unenroll: (id: string) => apiClient.delete(`/courses/${id}/unenroll`),
  getEnrollments: () => apiClient.get('/courses/enrollments'),
};
