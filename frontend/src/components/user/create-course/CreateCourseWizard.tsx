"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createEmptyDraft, CourseDraftDocumentMeta, UploadingFile, CourseDraftState } from '@/fake/courses';
import { Stepper } from './Stepper';
import { UploadStep } from './UploadStep';
import { MetaStep } from './MetaStep';
import { ReviewStep } from './ReviewStep';
import { SuccessStep } from './SuccessStep';
import { v4 as uuid } from 'uuid';
import { showToast } from '@/utils/toast';
import { courseApi, CreateCourseRequest } from '@/lib/api/course';
import { ApiErrorClass } from '@/lib/api/http';
import { API_CONFIG } from '@/config/env';

export function CreateCourseWizard() {
  const router = useRouter();
  const [draft, setDraft] = useState<CourseDraftState>(createEmptyDraft());
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Real uploading to backend
  const simulateUpload = async (files: FileList | null) => {
    if (!files) return;
    const fileArr = Array.from(files);
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

  const setMeta = (meta: CourseDraftState['meta']) => setDraft(d => ({ ...d, meta }));

  const next = () => setDraft(d => ({ ...d, step: Math.min(d.step + 1, 3) }));
  const back = () => setDraft(d => ({ ...d, step: Math.max(d.step - 1, 1) }));
  const setStep = (step: number) => setDraft(d => ({ ...d, step }));

  const submit = async () => {
    if (isSubmitting) return; setIsSubmitting(true);
    try {
      const course_id = uuid();
      // Backend expects difficulty (string) and duration (number seconds?). We'll map level and duration.
      const difficulty = draft.meta.level === 'beginner' ? 'easy' : draft.meta.level === 'advanced' ? 'hard' : 'medium';
      const unit = draft.meta.durationUnit; const val = Math.max(1, draft.meta.durationValue || 1);
      const durationMinutes = unit === 'Ngày' ? val * 24 * 60 : unit === 'Tuần' ? val * 7 * 24 * 60 : val * 30 * 24 * 60;
      const payload: CreateCourseRequest = {
        course_id,
        s3_key: draft.documents.map(d => d.s3Key || (d.url ? decodeURIComponent(d.url.split('/s3/').pop() || '') : d.name)),
        difficulty,
        duration: durationMinutes, // let backend interpret as minutes
      };
      const resp = await courseApi.requestCreate(payload);
      if (resp.data?.status === 202) {
        showToast.success('Yêu cầu tạo khóa học đã được gửi');
        setDraft(d => ({ ...d, step: 4, courseId: course_id }));
      } else {
        showToast.info(resp.data?.message || 'Đã gửi yêu cầu');
        setDraft(d => ({ ...d, step: 4, courseId: course_id }));
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
                onRestart={() => setDraft(createEmptyDraft())}
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
