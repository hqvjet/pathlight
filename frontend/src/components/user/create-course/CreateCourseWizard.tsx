"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createEmptyDraft, CourseDraftDocumentMeta, UploadingFile } from '@/types/create-course';
import { Stepper } from './Stepper';
import { UploadStep } from './UploadStep';
import { MetaStep } from './MetaStep';
import { ReviewStep } from './ReviewStep';
import { SuccessStep } from './SuccessStep';
import { v4 as uuid } from 'uuid';
import { showToast } from '@/utils/toast';
import { courseApi } from '@/lib/api/course';
import { agenticApi, AgenticCourseResponse, CreateAgenticCourseRequest } from '@/lib/api/agentic';
import { ApiErrorClass } from '@/lib/api/http';
import { API_CONFIG } from '@/config/env';

export function CreateCourseWizard() {
  const router = useRouter();
  const [draft, setDraft] = useState<CourseDraftState>(createEmptyDraft());
  const [result, setResult] = useState<AgenticCourseResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Real uploading to backend
  const simulateUpload = async (files: FileList | File[] | null) => {
    if (!files) return;
    const fileArr = Array.from(files as File[]);
    const uploading: UploadingFile[] = fileArr.map(f => ({ id: uuid(), file: f, progress: 0, status: 'pending' }));
    setDraft(d => ({ ...d, uploading: [...d.uploading, ...uploading] }));
    // Start progress animation
    uploading.forEach(item => { item.status = 'uploading'; });
    const progressTimer = setInterval(() => {
      setDraft(d => {
        const updated = d.uploading.map(u => ({ ...u, progress: Math.min(u.progress + Math.random()*18 + 5, 95) }));
        return { ...d, uploading: updated };
      });
    }, 300);
    try {
      const resp = await courseApi.uploadFiles(fileArr);
      const uploadedNames = resp.data?.uploaded_file ?? [];
      // Map original files to returned S3 keys by order
      setDraft(d => {
        const newDocs: CourseDraftDocumentMeta[] = uploadedNames.map((key: string, idx: number) => ({
          id: uploading[idx]?.id || uuid(),
          name: fileArr[idx]?.name || key,
          size: fileArr[idx]?.size || 0,
          type: fileArr[idx]?.type || 'application/octet-stream',
          uploadedAt: new Date(),
          url: `${API_CONFIG.COURSE_SERVICE_URL}/s3/${encodeURIComponent(key)}`,
          s3Key: key,
        }));
        return { ...d, documents: [...d.documents, ...newDocs], uploading: d.uploading.filter(u => !uploading.find(x => x.id === u.id)) };
      });
      clearInterval(progressTimer);
    } catch (e: unknown) {
      clearInterval(progressTimer);
      setDraft(d => ({ ...d, uploading: d.uploading.map(u => ({ ...u, status: 'error', progress: 0 })) }));
      showToast.error(e instanceof Error ? e.message : 'Tải tài liệu thất bại');
    }
  };

  const removeDoc = (id: string) => {
    setDraft(d => ({ ...d, documents: d.documents.filter(doc => doc.id !== id) }));
  };

  const retryUpload = (file: File) => {
    simulateUpload([file]);
  };

  const setMeta = (meta: CourseDraftState['meta']) => setDraft(d => ({ ...d, meta }));

  const next = () => setDraft(d => ({ ...d, step: Math.min(d.step + 1, 3) }));
  const back = () => setDraft(d => ({ ...d, step: Math.max(d.step - 1, 1) }));
  const setStep = (step: number) => setDraft(d => ({ ...d, step }));

  const submit = async () => {
    if (isSubmitting) return;
    setResult(null);
    setIsSubmitting(true);
    try {
      const missing: string[] = [];
      if (!draft.meta.userPosition.trim()) missing.push('User position');
      if (!draft.meta.shortPrompt.trim()) missing.push('Short user prompt');
      if (!draft.meta.courseLevel) missing.push('Course level');
      if (!draft.meta.courseConstraint) missing.push('Course constraint');
      if (!draft.meta.durationDays || draft.meta.durationDays < 1) missing.push('Course duration');

      if (missing.length) {
        showToast.error(`Thiếu thông tin: ${missing.join(', ')}`);
        setIsSubmitting(false);
        return;
      }

      const payload: CreateAgenticCourseRequest = {
        user_position: draft.meta.userPosition.trim(),
        short_user_prompt: draft.meta.shortPrompt.trim(),
        course_duration: Math.max(1, draft.meta.durationDays || 1),
        documents:
          draft.documents.length > 0
            ? draft.documents.map((d) => d.s3Key || (d.url ? decodeURIComponent(d.url.split('/s3/').pop() || '') : d.name))
            : undefined,
        course_level: draft.meta.courseLevel,
        course_constraint: draft.meta.courseConstraint,
      };

      const resp = await agenticApi.createCourse(payload);
      if (resp?.data) {
        setResult(resp.data);
        setDraft((d) => ({ ...d, step: 4 }));
        showToast.success('Đã tạo khóa học bằng multi-agent.');
      } else {
        showToast.info('Đã gửi yêu cầu, vui lòng chờ phản hồi.');
        setDraft((d) => ({ ...d, step: 4 }));
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
                onRemove={removeDoc}
                onNext={next}
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
                onNext={next}
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
