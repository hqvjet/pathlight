/** Course domain API helpers aligned to Course Service OpenAPI */
import { apiClient } from './http';

export interface CreateCourseRequest {
  type?: 'generate_course' | 'generate_quiz';
  short_prompt: string;
  user_role: string;
  course_duration: number;
  course_level: string;
  course_constraint: string;
  course_id?: string;
  documents?: string[];
  s3_key?: string[]; // legacy optional
}

export interface UpdateVisibilityRequest {
  course_id: string;
  is_public: boolean;
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
  requestCreate: (payload: CreateCourseRequest) =>
    apiClient.post<{ status: number; message?: string; sqs_message_id?: string; course_id?: string }>(`/course/create`, payload),
  getStatus: (course_id: string) => apiClient.get<{ status: number; body?: unknown; message?: string }>(`/course/status?course_id=${encodeURIComponent(course_id)}`),
  getById: (course_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}`),
  getAll: () => apiClient.get(`/course/all`),
  listPublic: (search?: string, ownerId?: string) => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (ownerId) params.append('owner_id', ownerId);
    const qs = params.toString();
    return apiClient.get(`/course/public${qs ? `?${qs}` : ''}`);
  },
  getRecommended: (topk: number = 20) => apiClient.get(`/course/recommend?topk=${topk}`),
  updateVisibility: (payload: UpdateVisibilityRequest) => apiClient.put<{ status: number; course_id: string; publish: boolean }>(`/course/visibility`, payload),
  deleteCourse: (course_id: string) => apiClient.delete<{ status: number; message?: string }>(`/course/delete?course_id=${encodeURIComponent(course_id)}`),
  listMyGenerations: () => apiClient.get<{ status: number; items?: Array<Record<string, unknown>>; message?: string }>(`/course/generations/my`),
  listLessons: (course_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}/lessons`),
  getLessonDetail: (course_id: string, lesson_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}/lessons/${encodeURIComponent(lesson_id)}`),
  listAssessments: (course_id: string, lesson_id: string, opts?: { include_hints?: boolean; include_explanations?: boolean }) => {
    const params = new URLSearchParams();
    if (opts?.include_hints === false) params.append('include_hints', 'false');
    if (opts?.include_explanations === false) params.append('include_explanations', 'false');
    const qs = params.toString();
    return apiClient.get(`/course/${encodeURIComponent(course_id)}/lessons/${encodeURIComponent(lesson_id)}/assessments${qs ? `?${qs}` : ''}`);
  },
  submitAssessments: (
    course_id: string,
    lesson_id: string,
    payload: { answers: Array<{ assessment_id: string; answer: number }> },
  ) => apiClient.post(`/course/${encodeURIComponent(course_id)}/lessons/${encodeURIComponent(lesson_id)}/assessments/submit`, payload),
  getHint: (course_id: string, lesson_id: string, assessment_id: string) =>
    apiClient.get<{ status: number; hint?: string; exp_penalty?: number; message?: string }>(
      `/course/${encodeURIComponent(course_id)}/lessons/${encodeURIComponent(lesson_id)}/assessments/${encodeURIComponent(assessment_id)}/hint`
    ),
  getQuiz: (course_id: string) => apiClient.get(`/course/${encodeURIComponent(course_id)}/quiz`),
  submitQuiz: (
    course_id: string,
    payload: { answers: Array<{ qa_id: string; answer: number }> },
  ) => apiClient.post(`/course/${encodeURIComponent(course_id)}/quiz/submit`, payload),
  finishLesson: (course_id: string, lesson_id: string) => apiClient.put(`/course/${encodeURIComponent(course_id)}/lessons/${encodeURIComponent(lesson_id)}/finish`),
};
