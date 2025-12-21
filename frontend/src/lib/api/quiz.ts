/** Quiz domain API helpers aligned to quiz-service contract */
import { apiClient } from './http';

// For agentic quiz generation
export type CreateQuizRequest = {
  type?: 'generate_quiz' | 'generate_course';
  short_prompt: string;
  user_role?: string;
  course_duration: number;
  course_level: string;
  course_constraint: string;
  documents?: string[];
};

// For manual quiz creation
export type ManualQuizCard = {
  question: string;
  hint?: string;
  explanation?: string;
  difficulty: 'easy' | 'medium' | 'hard';
  option1: string;
  option2: string;
  option3: string;
  option4: string;
  answer: number;
};

export type ManualQuizRequest = {
  title: string;
  overview: string;
  level: 'easy' | 'medium' | 'hard';
  duration: number;
  cards: ManualQuizCard[];
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

  /** Create quiz (agentic generation) */
  /** Create quiz (agentic generation) */
  create: (data: CreateQuizRequest) => apiClient.post('/quiz/create', data),

  /** Create quiz (manual) - no EXP reward */
  createManual: (data: ManualQuizRequest) => apiClient.post('/quiz/create/manual', data),

  /** Get generation status for a quiz */
  getStatus: (quiz_id: string) => apiClient.get<{ status: number; body?: unknown; message?: string }>(`/quiz/status?quiz_id=${encodeURIComponent(quiz_id)}`),

  /** List my quiz generations (tracking) */
  listMyGenerations: () => apiClient.get<{ status: number; items?: Array<Record<string, unknown>>; message?: string }>(`/quiz/generations/my`),

  /** Start quiz (logs activity) */
  start: (id: string) => apiClient.post(`/quiz/${id}/start`, { quiz_id: id }),

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
