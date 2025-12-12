/** Course domain API helpers aligned to Course Service OpenAPI */
import { apiClient } from './http';

export interface CreateCourseRequest {
  course_id: string;
  s3_key: string[];
  difficulty?: string; // default medium
  duration?: number; // default 1200
}

export interface PresignUploadRequestItem {
  filename: string;
  content_type: string;
  size: number;
}

export interface PresignUploadRequest {
  user_id?: string;
  items: PresignUploadRequestItem[];
}

export interface PresignUploadResponseItem {
  key: string;
  upload_url: string;
  headers?: Record<string, string>;
}

export interface PresignUploadResponse {
  status: number;
  items?: PresignUploadResponseItem[];
  message?: string;
}

export const courseApi = {
  // Course Service endpoints
  uploadFiles: (files: File[]) => apiClient.uploadFiles<{ status: number; uploaded_file: string[] }>(`/course/upload/file`, files),
  presignUploads: (items: PresignUploadRequestItem[], userId?: string) =>
    apiClient.post<PresignUploadResponse>(`/course/upload/presign`, { user_id: userId, items }),
  requestCreate: (payload: CreateCourseRequest) => apiClient.post<{ status: number; message?: string; sqs_message_id?: string }>(`/course/create`, payload),
  getStatus: (course_id: string) => apiClient.get<{ status: number; body?: unknown; message?: string }>(`/course/status?course_id=${encodeURIComponent(course_id)}`),
  getById: (course_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}`),
  getAll: () => apiClient.get(`/course/all`),
  listMyGenerations: () => apiClient.get<{ status: number; items?: Array<Record<string, unknown>>; message?: string }>(`/course/generations/my`),
  listLessons: (course_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}/lessons`),
  getLessonDetail: (course_id: string, lesson_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}/lessons/${encodeURIComponent(lesson_id)}`),
  getLessonTest: (course_id: string, lesson_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}/lessons/${encodeURIComponent(lesson_id)}/test`),
  submitLessonTest: (
    course_id: string,
    lesson_id: string,
    payload: { answers: Array<{ qa_id: string; answer: string }> },
  ) => apiClient.post(`/course/${encodeURIComponent(course_id)}/lessons/${encodeURIComponent(lesson_id)}/test/submit`, payload),
  getFinalTest: (course_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}/final-test`),
  finishLesson: (course_id: string, lesson_id: string) => apiClient.put(`/course/${encodeURIComponent(course_id)}/lessons/${encodeURIComponent(lesson_id)}/finish`),
};
