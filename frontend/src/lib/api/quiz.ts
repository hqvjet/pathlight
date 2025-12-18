/** Quiz domain API helpers aligned to quiz-service contract */
import { apiClient } from './http';

export type CreateQuizRequest = {
  type?: 'generate_quiz' | 'generate_course';
  short_prompt: string;
  user_role?: string;
  course_duration: number;
  course_level: string;
  course_constraint: string;
  documents?: string[];
};

export type QuizSubmitAnswer = { card_id: string; answer: number };

const buildQueryString = (params?: Record<string, string | number | boolean | undefined | null>) => {
  const query = new URLSearchParams();
  if (!params) return '';
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    query.append(key, String(value));
  });
  const qs = query.toString();
  return qs ? `?${qs}` : '';
};

export const quizApi = {
  /** List current user's quizzes */
  listMine: () => apiClient.get('/quiz/all'),

  /** List public quizzes with optional filters */
  listPublic: (params?: { search?: string; owner_id?: string }) =>
    apiClient.get(`/quiz/public${buildQueryString(params)}`),

  /** Fetch quiz detail with optional hint/explanation gating */
  getById: (
    id: string,
    options?: { include_hints?: boolean; include_explanations?: boolean },
  ) => {
    const query = buildQueryString({
      include_hints: options?.include_hints,
      include_explanations: options?.include_explanations,
    });
    return apiClient.get(`/quiz/${id}${query}`);
  },

  /** Create quiz generation job */
  create: (data: CreateQuizRequest) => apiClient.post('/quiz/create', data),

  /** Submit answers for a quiz */
  submit: (id: string, answers: QuizSubmitAnswer[]) => apiClient.post(`/quiz/${id}/submit`, { answers }),

  /** Update visibility (is_public) */
  updateVisibility: (quizId: string, isPublic: boolean) =>
    apiClient.put('/quiz/visibility', { quiz_id: quizId, is_public: isPublic }),

  /** Mark quiz as finished */
  finish: (quizId: string) => apiClient.put('/quiz/finish', { quiz_id: quizId }),

  /** Delete a quiz */
  delete: (id: string) => apiClient.delete(`/quiz/${id}`),
};
