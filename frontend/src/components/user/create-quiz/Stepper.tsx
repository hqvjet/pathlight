"use client";
import { QuizDraftState } from '@/types/create-quiz';

interface StepperProps {
  step: number;
  setStep: (step: number) => void;
  draft: QuizDraftState;
}

const getSteps = (creationType: 'ai' | 'manual') => {
  if (creationType === 'ai') {
    return [
      { id: 1, label: 'Loại hình' },
      { id: 2, label: 'Upload file' },
      { id: 3, label: 'Thông tin' },
      { id: 4, label: 'Xem lại' },
      { id: 5, label: 'Hoàn thành' },
    ];
  }
  return [
    { id: 1, label: 'Loại hình' },
    { id: 2, label: 'Thông tin' },
    { id: 3, label: 'Câu hỏi' },
    { id: 4, label: 'Xem lại' },
    { id: 5, label: 'Hoàn thành' },
  ];
};

export function Stepper({ step, setStep, draft }: StepperProps) {
  const steps = getSteps(draft.creationType);

  const canNavigate = (targetStep: number) => {
    if (targetStep > step) return false;
    if (targetStep === steps.length) return false; // Can't manually go to success
    return true;
  };

  return (
    <div className="flex items-center justify-center gap-2 sm:gap-4 px-4 py-6 overflow-x-auto">
      {steps.map((s, idx) => (
        <div key={s.id} className="flex items-center gap-2 sm:gap-4 shrink-0">
          <button
            type="button"
            onClick={() => canNavigate(s.id) && setStep(s.id)}
            disabled={!canNavigate(s.id)}
            className={`flex items-center gap-2 sm:gap-3 px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition whitespace-nowrap ${
              s.id === step
                ? 'bg-sky-500 text-white shadow-sm'
                : s.id < step
                ? 'bg-sky-100 text-sky-700 hover:bg-sky-200 cursor-pointer'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-white/20 text-xs font-bold">
              {s.id}
            </span>
            <span className="hidden sm:inline">{s.label}</span>
          </button>
          {idx < steps.length - 1 && (
            <div className="hidden sm:block w-8 h-px bg-gray-300" />
          )}
        </div>
      ))}
    </div>
  );
}
