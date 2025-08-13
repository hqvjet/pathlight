"use client";
import { useState } from 'react';
import { createEmptyDraft, CourseDraftDocumentMeta, UploadingFile, CourseDraftState } from '@/fake/courses';
import { Stepper } from './Stepper';
import { UploadStep } from './UploadStep';
import { MetaStep } from './MetaStep';
import { ReviewStep } from './ReviewStep';
import { SuccessStep } from './SuccessStep';
import Layout from '@/components/common/Layout';
import { v4 as uuid } from 'uuid';
import { showToast } from '@/utils/toast';

export function CreateCourseWizard() {
  const [draft, setDraft] = useState<CourseDraftState>(createEmptyDraft());

  // Fake uploading simulation
  const simulateUpload = (files: FileList | null) => {
    if (!files) return;
    const uploading: UploadingFile[] = Array.from(files).map(f => ({ id: uuid(), file: f, progress: 0, status: 'pending' }));
    setDraft(d => ({ ...d, uploading: [...d.uploading, ...uploading] }));
    uploading.forEach(item => {
      item.status = 'uploading';
      const interval = setInterval(() => {
        setDraft(d => {
          const updated = d.uploading.map(u => u.id === item.id ? { ...u, progress: Math.min(u.progress + Math.random()*18 + 5, 100) } : u);
          return { ...d, uploading: updated };
        });
      }, 350);
      const doneTimeout = setTimeout(() => {
        clearInterval(interval);
        setDraft(d => {
          const fileEntry: CourseDraftDocumentMeta = { id: item.id, name: item.file.name, size: item.file.size, type: item.file.type, uploadedAt: new Date(), url: URL.createObjectURL(item.file) };
          return {
            ...d,
            documents: [...d.documents, fileEntry],
            uploading: d.uploading.filter(u => u.id !== item.id)
          };
        });
        clearTimeout(doneTimeout);
      }, 2000 + Math.random()*2000);
    });
  };

  const removeDoc = (id: string) => {
    setDraft(d => ({ ...d, documents: d.documents.filter(doc => doc.id !== id) }));
  };

  const setMeta = (meta: CourseDraftState['meta']) => setDraft(d => ({ ...d, meta }));

  const next = () => setDraft(d => ({ ...d, step: Math.min(d.step + 1, 3) }));
  const back = () => setDraft(d => ({ ...d, step: Math.max(d.step - 1, 1) }));
  const setStep = (step: number) => setDraft(d => ({ ...d, step }));

  const submit = () => {
    showToast.success('Khóa học đã được tạo (demo)');
    setDraft(d => ({ ...d, step: 4 }));
  };

  const mockUser = { name: 'Nguyễn Văn A', email: 'user@example.com', avatar_url: '' };

  return (
    <Layout user={mockUser} title="Tạo Khóa Học">
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
                onCancel={() => setDraft(createEmptyDraft())}
              />
            )}
            {draft.step === 2 && (
              <MetaStep
                meta={draft.meta}
                onChange={setMeta}
                onBack={back}
                onNext={() => draft.meta.title.trim() ? next() : showToast.warning('Vui lòng nhập tiêu đề')} 
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
                onGoToCourses={() => showToast.info('Đi đến danh sách khóa học (demo)')}
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
    </Layout>
  );
}
