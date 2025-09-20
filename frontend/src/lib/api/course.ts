/** Course domain API helpers aligned to Course Service OpenAPI */
import { apiClient } from './http';

export interface CreateCourseRequest {
  course_id: string;
  s3_key: string[];
  difficulty?: string; // default medium
  duration?: number; // default 1200
}

export const courseApi = {
  // Course Service endpoints
  uploadFiles: (files: File[]) => apiClient.uploadFiles<{ status: number; uploaded_file: string[] }>(`/course/upload/file`, files),
  requestCreate: (payload: CreateCourseRequest) => apiClient.post<{ status: number; message?: string; sqs_message_id?: string }>(`/course/create`, payload),
  getStatus: (course_id: string) => apiClient.get<{ status: number; body?: unknown; message?: string }>(`/course/status?course_id=${encodeURIComponent(course_id)}`),
  getById: (course_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}`),
  getAll: () => apiClient.get(`/course/all`),
  listMyGenerations: () => apiClient.get<{ status: number; items?: Array<Record<string, unknown>>; message?: string }>(`/course/generations/my`),
  listLessons: (course_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}/lessons`),
  getLessonDetail: (course_id: string, lesson_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}/lessons/${encodeURIComponent(lesson_id)}`),
  getLessonTest: (course_id: string, lesson_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}/lessons/${encodeURIComponent(lesson_id)}/test`),
  getFinalTest: (course_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}/final-test`),
};
