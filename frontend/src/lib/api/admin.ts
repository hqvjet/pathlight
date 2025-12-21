/** Admin API for managing all system resources */
import { apiClient } from './http';

export type AdminUser = {
  user_id: string;
  email?: string;
  given_name?: string;
  family_name?: string;
  level?: number;
  current_exp?: number;
  subscription?: number;
  created_at?: string;
};

export type AdminCourse = {
  course_id: string;
  user_id: string;
  title: string;
  overview: string;
  level: string;
  duration: number;
  publish: boolean;
  finish: boolean;
  num_lessons: number;
  created_at: string;
};

export type AdminQuiz = {
  quiz_id: string;
  user_id: string;
  title: string;
  overview: string;
  level: string;
  duration: number;
  publish: boolean;
  finish: boolean;
  num_questions: number;
  creation_type?: string;
  created_at: string;
};

export type CostItem = {
  date: string;
  cost: number;
};

export type LogItem = {
  timestamp: string;
  type: string;
  log: string;
  source: string;
};

export type LogStream = {
  log_group: string;
  log_stream: string;
  last_event_time?: string;
  last_ingestion_time?: string;
  stored_bytes?: number;
};

export const adminApi = {
  // User management
  listUsers: () => apiClient.get<{ status: number; users?: AdminUser[]; message?: string }>('/user/admin/users'),
  
  updateUserEmail: (userId: string, email: string) =>
    apiClient.put<{ status: number; message?: string }>(`/user/admin/user?userid=${userId}`, { email }),
  
  updateUserSubscription: (userId: string, subscription: number) =>
    apiClient.put<{ status: number; message?: string }>(`/user/admin/user/subscription?userid=${userId}`, { subscription }),

  deleteUser: (userId: string) =>
    apiClient.delete<{ status: number; message?: string }>(`/user/admin/user?userid=${userId}`),
  
  createAdmin: (username: string, password: string) =>
    apiClient.post<{ status: number; message?: string }>('/user/admin/create', { username, password }),

  addUserExperience: (userId: string, exp: number) =>
    apiClient.post<{ status: number; message?: string; updated_stats?: Record<string, unknown> }>(`/user/admin/user/experience?userid=${userId}`, { exp }),

  adjustUserExperienceStep: (userId: string, delta: number) =>
    apiClient.post<{ status: number; message?: string; updated_stats?: Record<string, unknown> }>(
      `/user/admin/user/experience/step?userid=${userId}`,
      { delta }
    ),

  listAdmins: () => apiClient.get<{ status: number; admins?: { id: string; username: string; created_at?: string }[]; message?: string }>(`/user/admin/admins`),

  // Course management
  listAllCourses: (params?: { page?: number; limit?: number; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', String(params.page));
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.search) query.append('search', params.search);
    const queryString = query.toString();
    return apiClient.get<{ status: number; courses?: AdminCourse[]; total?: number; message?: string }>(
      `/course/admin/courses${queryString ? `?${queryString}` : ''}`
    );
  },
  
  deleteCourse: (courseId: string) =>
    apiClient.delete<{ status: number; message?: string }>(`/course/admin/courses/${courseId}`),
  
  toggleCourseVisibility: (courseId: string, publish: boolean) =>
    apiClient.put<{ status: number; message?: string }>(`/course/admin/courses/${courseId}/visibility`, { publish }),

  // Quiz management
  listAllQuizzes: (params?: { page?: number; limit?: number; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', String(params.page));
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.search) query.append('search', params.search);
    const queryString = query.toString();
    return apiClient.get<{ status: number; quizzes?: AdminQuiz[]; total?: number; message?: string }>(
      `/quiz/admin/quizzes${queryString ? `?${queryString}` : ''}`
    );
  },
  
  deleteQuiz: (quizId: string) =>
    apiClient.delete<{ status: number; message?: string }>(`/quiz/admin/quizzes/${quizId}`),
  
  toggleQuizVisibility: (quizId: string, publish: boolean) =>
    apiClient.put<{ status: number; message?: string }>(`/quiz/admin/quizzes/${quizId}/visibility`, { publish }),

  // System monitoring
  getCosts: () =>
    apiClient.get<{ status: number; total_cost?: number; costs?: CostItem[]; message?: string }>('/user/admin/cost'),
  
  getLogStreams: (
    filterKey: 'daily' | 'weekly' | 'monthly' | 'hourly' | '30m' | '1m' = 'daily',
    service?: string
  ) => {
    const query = new URLSearchParams();
    query.append('filter_key', filterKey);
    if (service) query.append('service', service);
    return apiClient.get<{ status: number; streams?: LogStream[]; message?: string }>(
      `/user/admin/log/streams?${query.toString()}`
    );
  },

  getLogs: (
    filterKey: 'daily' | 'weekly' | 'monthly' | 'hourly' | '30m' | '1m' = 'daily',
    service?: string,
    logStream?: string
  ) => {
    const query = new URLSearchParams();
    query.append('filter_key', filterKey);
    if (service) query.append('service', service);
    if (logStream) query.append('log_stream', logStream);
    return apiClient.get<{ status: number; logs?: LogItem[]; message?: string }>(
      `/user/admin/log?${query.toString()}`
    );
  },
};
