// Shared types and helpers for quiz creation flow

export interface QuizCardDraft {
  id: string;
  question: string;
  hint: string;
  explanation: string;
  difficulty: 'easy' | 'medium' | 'hard';
  option1: string;
  option2: string;
  option3: string;
  option4: string;
  answer: number; // 1-4
}

export interface UploadingFile {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

export interface QuizDraftDocument {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  url?: string;
  s3Key?: string;
}

export interface QuizDraftState {
  step: number;
  quizId?: string;
  creationType: 'ai' | 'manual'; // AI generation or manual creation
  documents: QuizDraftDocument[];
  uploading: UploadingFile[];
  meta: {
    title: string;
    overview: string;
    level: 'easy' | 'medium' | 'hard';
    duration: number; // minutes
    userPosition?: string; // For AI generation
    shortPrompt?: string; // For AI generation
  };
  cards: QuizCardDraft[];
}

export const createEmptyQuizDraft = (): QuizDraftState => ({
  step: 1,
  quizId: undefined,
  creationType: 'ai', // Default to AI generation
  documents: [],
  uploading: [],
  meta: {
    title: '',
    overview: '',
    level: 'easy',
    duration: 15,
    userPosition: '',
    shortPrompt: '',
  },
  cards: [],
});

export const createEmptyCard = (): QuizCardDraft => ({
  id: crypto.randomUUID(),
  question: '',
  hint: '',
  explanation: '',
  difficulty: 'easy',
  option1: '',
  option2: '',
  option3: '',
  option4: '',
  answer: 1,
});

// Subscription-based question limits
export const QUIZ_LIMITS = {
  free: 10,
  premium: 50,
  enterprise: Infinity,
} as const;

export type SubscriptionTier = keyof typeof QUIZ_LIMITS;

export const getQuestionLimit = (tier: SubscriptionTier = 'free'): number => {
  return QUIZ_LIMITS[tier];
};
