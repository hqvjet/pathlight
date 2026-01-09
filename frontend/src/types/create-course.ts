// Shared types and helpers for course creation flow

export interface UploadingFile {
  id: string;
  file: File;
  progress: number; // 0-100
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

export interface CourseDraftDocumentMeta {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  url?: string;
  s3Key?: string;
}

export interface CourseDraftState {
  step: number;
  courseId?: string;
  documents: CourseDraftDocumentMeta[];
  uploading: UploadingFile[];
  meta: {
    userPosition: string;
    shortPrompt: string;
    durationDays: number;
    courseLevel: 'overview' | 'intermediate' | 'advance';
    courseConstraint:
      | 'professional'
      | 'academic'
      | 'friendly'
      | 'humorous';
  };
  modules: Array<{
    id: string;
    title: string;
    lessons: Array<{ id: string; title: string; duration?: number }>;
  }>;
}

export const createEmptyDraft = (): CourseDraftState => ({
  step: 1,
  courseId: undefined,
  documents: [],
  uploading: [],
  meta: {
    userPosition: 'Sinh viên',
    shortPrompt: '',
    durationDays: 7,
    courseLevel: 'overview',
    courseConstraint: 'professional',
  },
  modules: [],
});

let _draft: CourseDraftState = createEmptyDraft();

export function getDraft(): CourseDraftState {
  return _draft;
}

export function updateDraft(patch: Partial<CourseDraftState>) {
  _draft = { ..._draft, ...patch };
}
