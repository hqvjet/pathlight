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
  url?: string; // local object URL for preview if needed
  s3Key?: string; // backend-returned S3 key for this file
}

export interface CourseDraftState {
  step: number;
  courseId?: string; // server-side identifier for tracking status
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
      | 'humorous'
      | 'chuyen-nghiep'
      | 'hoc-thuat'
      | 'gan-gui'
      | 'di-dom';
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
    userPosition: '',
    shortPrompt: '',
    durationDays: 7,
    courseLevel: 'overview',
    courseConstraint: 'professional',
  },
  modules: [],
});

// In-memory ephemeral store (simple, replace with context/store later)
let _draft: CourseDraftState = createEmptyDraft();

export function getDraft(): CourseDraftState {
  return _draft;
}

export function updateDraft(patch: Partial<CourseDraftState>) {
  _draft = { ..._draft, ...patch };
}
