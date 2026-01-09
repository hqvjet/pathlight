"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createEmptyDraft, CourseDraftState, UploadingFile } from '@/types/create-course';
import { Stepper } from './Stepper';
import { UploadStep } from './UploadStep';
import { MetaStep } from './MetaStep';
import { ReviewStep } from './ReviewStep';
import { SuccessStep } from './SuccessStep';
import { v4 as uuid } from 'uuid';
import { showToast } from '@/utils/toast';
import { courseApi, PresignUploadResponseItem } from '@/lib/api/course';
import {
  agenticApi,
  AgenticCourseResponse,
  AgenticCreateCourseResponse,
  AgenticQueuedCreateResponse,
  CreateAgenticCourseRequest,
} from '@/lib/api/agentic';
import { ApiErrorClass } from '@/lib/api/http';
import { API_CONFIG } from '@/config/env';
import { useAuthContext } from '@/context/AuthContext';

export function CreateCourseWizard() {
  const router = useRouter();
  const { user } = useAuthContext();
  const [draft, setDraft] = useState<CourseDraftState>(createEmptyDraft());
  const [result, setResult] = useState<AgenticCreateCourseResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isQueuedCreateResponse = (data: unknown): data is AgenticQueuedCreateResponse => {
    return Boolean(data && typeof data === 'object' && ('course_id' in data || 'sqs_message_id' in data || 'status' in data || 'message' in data));
  };

  const isCourseResponse = (data: unknown): data is AgenticCourseResponse => {
    return Boolean(data && typeof data === 'object' && 'course_title' in data && 'course_overview' in data);
  };

  // Direct-to-S3 via presigned PUT (single-part) to avoid API Gateway 10MB limit
  const uploadWithPresigned = (url: string, file: File, headers?: Record<string, string>, onProgress?: (p: number) => void) => {
    return new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('PUT', url, true);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          const percent = Math.min(99, Math.round((e.loaded / e.total) * 100));
          onProgress(percent);
        }
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          if (onProgress) onProgress(100);
          resolve();
        } else {
          reject(new Error(`Upload failed (${xhr.status})`));
        }
      };
      xhr.onerror = () => reject(new Error('Network error during upload'));
      xhr.onabort = () => reject(new Error('Upload aborted'));
      if (headers) {
        Object.entries(headers).forEach(([k, v]) => xhr.setRequestHeader(k, v));
      }
      if (!headers || !headers['Content-Type']) xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
      xhr.send(file);
    });
  };

  const simulateUpload = async (files: FileList | File[] | null) => {
    if (!files) return;
    if (!user?.id) {
      showToast.error('Không xác định được người dùng, vui lòng đăng nhập lại.');
      return;
    }
    const fileArr = Array.from(files as File[]);
    const uploading: UploadingFile[] = fileArr.map(f => ({ id: uuid(), file: f, progress: 0, status: 'uploading' }));
    setDraft(d => ({ ...d, uploading: [...d.uploading, ...uploading] }));

    try {
      const presignResp = await courseApi.presignUploads(
        fileArr.map((f) => ({ filename: f.name, content_type: f.type || 'application/octet-stream', size: f.size })),
        user.id,
      );
      const items = presignResp?.data?.items || [];
      if (items.length !== fileArr.length) {
        throw new Error('Không lấy được đủ URL tải lên');
      }

      for (let i = 0; i < fileArr.length; i += 1) {
        const file = fileArr[i];
        const meta: PresignUploadResponseItem = items[i];
        const targetId = uploading[i]?.id;
        const updateProgress = (progress: number) => {
          if (!targetId) return;
          setDraft(d => ({
            ...d,
            uploading: d.uploading.map(u => u.id === targetId ? { ...u, progress } : u),
          }));
        };

        try {
          await uploadWithPresigned(meta.upload_url, file, meta.headers, updateProgress);
          setDraft(d => ({
            ...d,
            uploading: d.uploading.filter(u => u.id !== targetId),
            documents: [
              ...d.documents,
              {
                id: targetId || uuid(),
                name: file.name,
                size: file.size,
                type: file.type || 'application/octet-stream',
                uploadedAt: new Date(),
                url: `${API_CONFIG.COURSE_SERVICE_URL}/s3/${encodeURIComponent(meta.key)}`,
                s3Key: meta.key,
              },
            ],
          }));
        } catch (err) {
          setDraft(d => ({
            ...d,
            uploading: d.uploading.map(u => u.id === targetId ? { ...u, status: 'error', progress: 0, error: (err as Error).message } : u),
          }));
          showToast.error((err as Error).message || 'Tải tài liệu thất bại');
        }
      }
    } catch (e: unknown) {
      setDraft(d => ({
        ...d,
        uploading: d.uploading.map(u => uploading.find(x => x.id === u.id) ? { ...u, status: 'error', progress: 0 } : u),
      }));
      showToast.error(e instanceof Error ? e.message : 'Không thể khởi tạo URL tải lên');
    }
  };

  const removeDoc = (id: string) => {
    setDraft(d => ({ ...d, documents: d.documents.filter(doc => doc.id !== id) }));
  };

  const retryUpload = (file: File, id?: string) => {
    if (id) {
      setDraft(d => ({ ...d, uploading: d.uploading.filter(u => u.id !== id) }));
    }
    simulateUpload([file]);
  };

  const removeUploading = (id: string) => {
    setDraft(d => ({ ...d, uploading: d.uploading.filter(u => u.id !== id) }));
  };

  const setMeta = (meta: CourseDraftState['meta']) => setDraft(d => ({ ...d, meta }));

  const validateMeta = (meta: CourseDraftState['meta']) => {
    const missing: string[] = [];
    if (!meta.userPosition.trim()) missing.push('Vị trí người học');
    if (!meta.courseLevel) missing.push('Trình độ khóa học');
    if (!meta.courseConstraint) missing.push('Văn phong khóa học');
    if (!meta.durationDays || meta.durationDays < 1) missing.push('Thời lượng (ngày)');

    if (missing.length) {
      showToast.error(`Thiếu thông tin: ${missing.join(', ')}`);
      return false;
    }

    return true;
  };

  const validateFiles = () => {
    if (draft.documents.length === 0) {
      showToast.error('Vui lòng tải lên ít nhất 1 tài liệu');
      return false;
    }
    return true;
  };

  const next = () => setDraft(d => ({ ...d, step: Math.min(d.step + 1, 3) }));
  const back = () => setDraft(d => ({ ...d, step: Math.max(d.step - 1, 1) }));
  const setStep = (step: number) => setDraft(d => ({ ...d, step }));

  const nextFromUpload = () => {
    if (validateFiles()) next();
  };

  const nextFromMeta = () => {
    if (validateMeta(draft.meta)) next();
  };

  const submit = async () => {
    if (isSubmitting) return;
    setResult(null);
    setIsSubmitting(true);
    try {
      if (!validateFiles()) {
        setIsSubmitting(false);
        return;
      }

      if (!validateMeta(draft.meta)) {
        setIsSubmitting(false);
        return;
      }

      const payload: CreateAgenticCourseRequest = {
        type: 'GENERATE_COURSE_WITH_VECTORIZE',
        id: `course-${uuid()}`,
        s3_keys: draft.documents.map((d) => d.s3Key || (d.url ? decodeURIComponent(d.url.split('/s3/').pop() || '') : d.name)),
        difficulty: draft.meta.courseLevel === 'overview' ? 'easy' : draft.meta.courseLevel === 'intermediate' ? 'medium' : 'hard',
        duration: Math.max(1, draft.meta.durationDays || 1) * 24 * 60,
        user_id: user?.id,
      };

      const resp = await agenticApi.createCourse(payload);
      const data = resp?.data;

      if (resp?.status === 202 && isQueuedCreateResponse(data)) {
        const courseId = data.course_id || payload.id;

        showToast.success('Đã gửi yêu cầu tạo khóa học thành công!');
        setDraft((d) => ({ ...d, step: 4, courseId }));
      } else if (data && isCourseResponse(data)) {
        setResult(data);
        setDraft((d) => ({ ...d, step: 4, courseId: payload.id }));
        showToast.success('Đã tạo khóa học thành công!');
      } else if (data && isQueuedCreateResponse(data)) {
        setResult(data);
        setDraft((d) => ({ ...d, step: 4, courseId: data.course_id || payload.id }));
        showToast.success(data.message || 'Đã tạo khóa học thành công!');
      } else {
        showToast.warning('Đã gửi yêu cầu nhưng không nhận được xác nhận.');
        setDraft((d) => ({ ...d, step: 4, courseId: payload.id }));
      }
    } catch (e: unknown) {
      if (e instanceof ApiErrorClass && e.status === 401) {
        showToast.error('Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.');
      } else {
        showToast.error(e instanceof Error ? e.message : 'Tạo khóa học thất bại');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 pt-6">
        <div className="bg-white rounded-xl shadow-sm overflow-hidden mt-2">
          <Stepper current={draft.step > 3 ? 3 : draft.step} onStepChange={setStep} />
          <div className="p-8">
            {draft.step === 1 && (
              <UploadStep
                documents={draft.documents}
                uploading={draft.uploading}
                onFiles={simulateUpload}
                onRetry={retryUpload}
                onRemoveUploading={removeUploading}
                onRemove={removeDoc}
                onNext={nextFromUpload}
                onCancel={() => {
                  // Navigate to My Courses when cancelling upload step
                  router.push('/user/my-courses');
                }}
              />
            )}
            {draft.step === 2 && (
              <MetaStep
                meta={draft.meta}
                onChange={setMeta}
                onBack={back}
                onNext={nextFromMeta}
              />
            )}
            {draft.step === 3 && (
              <ReviewStep
                draft={draft}
                onBack={back}
                onSubmit={submit}
              />
            )}
            {draft.step === 4 && (
              <SuccessStep
                draft={draft}
                result={result}
                onRestart={() => { setDraft(createEmptyDraft()); setResult(null); }}
                onGoToCourses={() => router.push('/user/my-courses')}
              />
            )}
          </div>
        </div>
        <footer className="mt-10 text-xs text-gray-400 flex flex-wrap gap-4 justify-center">
          <span>FAQs</span>
            <span>Privacy Policy</span>
            <span>Terms & Condition</span>
        </footer>
  </div>
  );
}
