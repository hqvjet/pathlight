"use client";
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/context/AuthContext';
import { v4 as uuid } from 'uuid';
import { QuizDraftState, createEmptyQuizDraft, createEmptyCard, SubscriptionTier, UploadingFile } from '@/types/create-quiz';
import { Stepper } from './Stepper';
import { CreationTypeStep } from './CreationTypeStep';
import { UploadStep } from './UploadStep';
import { MetaStep } from './MetaStep';
import { QuestionsStep } from './QuestionsStep';
import { ReviewStep } from './ReviewStep';
import { SuccessStep } from './SuccessStep';
import { showToast } from '@/utils/toast';
import { quizApi } from '@/lib/api/quiz';
import { courseApi, PresignUploadResponseItem } from '@/lib/api/course';
import { userApi } from '@/lib/api/user';
import { API_CONFIG } from '@/config/env';

interface CreateQuizWizardProps {
  userTier?: SubscriptionTier;
}

export function CreateQuizWizard({ userTier = 'free' }: CreateQuizWizardProps) {
  const router = useRouter();
  const { user } = useAuthContext();
  const [draft, setDraft] = useState<QuizDraftState>(createEmptyQuizDraft);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [userSubscription, setUserSubscription] = useState<number>(0); // 0=free, 1=premium, 2=pro

  // Fetch user subscription info
  useEffect(() => {
    const fetchSubscription = async () => {
      try {
        const userInfoResp = await userApi.getInfo();
        const responseData = userInfoResp?.data as { Info?: { subscription?: number }; info?: { subscription?: number } } | undefined;
        const userInfo = responseData?.Info || responseData?.info;
        const subscription = userInfo?.subscription || 0;
        setUserSubscription(subscription);
      } catch (error) {
        console.error('Failed to fetch user subscription:', error);
        setUserSubscription(0); // Default to free
      }
    };
    fetchSubscription();
  }, []);

  const setStep = (step: number) => setDraft((d) => ({ ...d, step }));
  const next = () => setDraft((d) => ({ ...d, step: d.step + 1 }));
  const back = () => setDraft((d) => ({ ...d, step: Math.max(d.step - 1, 1) }));

  const setMeta = (meta: QuizDraftState['meta']) => setDraft((d) => ({ ...d, meta }));
  const setCards = (cards: QuizDraftState['cards']) => setDraft((d) => ({ ...d, cards }));

  const handleSelectType = (type: 'ai' | 'manual') => {
    setDraft((d) => ({ 
      ...d, 
      creationType: type,
      cards: type === 'manual' ? [createEmptyCard()] : [],
      step: 2
    }));
  };

  const handleCancel = () => {
    if (confirm('Bạn có chắc muốn hủy? Dữ liệu sẽ không được lưu.')) {
      router.push('/user/my-quizzes');
    }
  };

  // Upload logic for AI generation (copied from course wizard)
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

  const handleSubmitAI = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      if (draft.documents.length === 0) {
        showToast.error('Vui lòng upload ít nhất một tài liệu');
        setIsSubmitting(false);
        return;
      }

      const payload = {
        type: 'GENERATE_QUIZ_WITH_VECTORIZE' as const,
        duration: Math.max(1, draft.meta.duration || 15),
        difficulty: draft.meta.level || 'easy',
        num_questions: draft.meta.numQuestions || 10,
        s3_keys: draft.documents.map((d) => d.s3Key || (d.url ? decodeURIComponent(d.url.split('/s3/').pop() || '') : d.name)),
      };

      const resp = await quizApi.create(payload);
      const data = resp?.data as { quiz_id?: string };
      if (data?.quiz_id) {
        setDraft((d) => ({ ...d, quizId: data.quiz_id, step: 5 }));
        showToast.success('Đã gửi yêu cầu tạo quiz bằng AI');
      } else {
        showToast.info('Đã gửi yêu cầu, vui lòng chờ phản hồi.');
        setDraft((d) => ({ ...d, step: 5 }));
      }
    } catch (e: unknown) {
      showToast.error(e instanceof Error ? e.message : 'Tạo quiz thất bại');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitManual = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      const payload = {
        title: draft.meta.title,
        overview: draft.meta.overview,
        level: draft.meta.level,
        duration: draft.meta.duration,
        is_manual: true, // Flag to indicate manual creation (no EXP)
        cards: draft.cards.map((card) => ({
          question: card.question,
          hint: card.hint || undefined,
          explanation: card.explanation || undefined,
          difficulty: card.difficulty,
          option1: card.option1,
          option2: card.option2,
          option3: card.option3,
          option4: card.option4,
          answer: card.answer,
        })),
      };

      const resp = await quizApi.createManual(payload);
      const data = resp?.data as { quiz_id?: string };
      if (data?.quiz_id) {
        setDraft((d) => ({ ...d, quizId: data.quiz_id, step: 5 }));
        showToast.success('Tạo quiz thành công!');
      } else {
        throw new Error('Không nhận được quiz_id từ server');
      }
    } catch (e: unknown) {
      showToast.error(e instanceof Error ? e.message : 'Tạo quiz thất bại');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = draft.creationType === 'ai' ? handleSubmitAI : handleSubmitManual;

  return (
    <div className="min-h-screen bg-sky-50 pb-12">
      <Stepper step={draft.step} setStep={setStep} draft={draft} />

      {/* Step 1: Choose creation type */}
      {draft.step === 1 && (
        <CreationTypeStep
          onSelectType={handleSelectType}
          onCancel={handleCancel}
        />
      )}

      {/* AI Flow */}
      {draft.creationType === 'ai' && (
        <>
          {draft.step === 2 && (
            <UploadStep
              documents={draft.documents}
              uploading={draft.uploading}
              onUpload={simulateUpload}
              onRemoveDoc={removeDoc}
              onRemoveUploading={removeUploading}
              onRetry={retryUpload}
              onNext={next}
              onBack={back}
            />
          )}

          {draft.step === 3 && (
            <MetaStep
              meta={draft.meta}
              onChange={setMeta}
              onNext={next}
              onCancel={back}
              isAIMode={true}
              userSubscription={userSubscription}
            />
          )}

          {draft.step === 4 && (
            <ReviewStep
              draft={draft}
              onBack={back}
              onSubmit={handleSubmit}
              isSubmitting={isSubmitting}
            />
          )}
        </>
      )}

      {/* Manual Flow */}
      {draft.creationType === 'manual' && (
        <>
          {draft.step === 2 && (
            <MetaStep
              meta={draft.meta}
              onChange={setMeta}
              onNext={next}
              onCancel={back}
              isAIMode={false}
              userSubscription={userSubscription}
            />
          )}

          {draft.step === 3 && (
            <QuestionsStep
              cards={draft.cards}
              onChange={setCards}
              onNext={next}
              onBack={back}
              userTier={userTier}
            />
          )}

          {draft.step === 4 && (
            <ReviewStep
              draft={draft}
              onBack={back}
              onSubmit={handleSubmit}
              isSubmitting={isSubmitting}
            />
          )}
        </>
      )}

      {/* Success */}
      {draft.step === 5 && draft.quizId && (
        <SuccessStep 
          quizId={draft.quizId} 
          quizTitle={draft.meta.title || draft.meta.overview || 'Quiz mới'} 
          isAI={draft.creationType === 'ai'}
        />
      )}
    </div>
  );
}
