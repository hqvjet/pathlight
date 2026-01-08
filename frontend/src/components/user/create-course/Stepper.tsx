"use client";
import { cn } from '@/lib/utils';

interface StepperProps {
  current: number;
  onStepChange?: (step: number) => void;
}

const steps = [
  { id: 1, label: 'Tải Tài Liệu Lên', icon: 'layers' },
  { id: 2, label: 'Mô Tả Khóa Học', icon: 'doc' },
  { id: 3, label: 'Tạo Khóa Học', icon: 'plus' },
];

function Icon({ name }: { name: string }) {
  const base = 'w-4 h-4 stroke-[1.8]';
  switch (name) {
    case 'layers':
      return <svg className={base} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 7l9 4 9-4M3 7l9-4 9 4M3 7v10l9 4 9-4V7M3 17l9 4 9-4" /></svg>;
    case 'doc':
      return <svg className={base} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 12h6m-6 4h6M6 8h.01M6 12h.01M6 16h.01M14 3H6a2 2 0 00-2 2v14a2 2 0 002 2h12a2 2 0 002-2V9l-6-6z" /></svg>;
    case 'plus':
      return <svg className={base} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" /></svg>;
    default:
      return null;
  }
}

export function Stepper({ current, onStepChange }: StepperProps) {
  const progress = (current - 1) / (steps.length - 1) * 100;
  return (
    <div className="relative">
      <ol className="flex items-center text-xs sm:text-sm font-medium">
        {steps.map((s, i) => {
          const active = current === s.id;
            const complete = current > s.id;
            return (
              <li key={s.id} className={cn('relative flex-1 flex items-center justify-center')}>
                <button
                  type="button"
                  disabled={!complete}
                  onClick={() => complete && onStepChange?.(s.id)}
                  className={cn('flex items-center gap-1.5 sm:gap-2 py-3 sm:py-4 px-2 sm:px-4 transition-colors w-full justify-center select-none', active && 'text-orange-600', complete && 'text-green-600 hover:text-green-700', !complete && !active && 'text-gray-500')}
                  aria-current={active ? 'step' : undefined}
                >
                  <div className={cn('w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center border text-gray-500', active && 'border-orange-500 bg-orange-50 text-orange-600', complete && 'border-green-500 bg-green-50 text-green-600') }>
                    {complete ? (
                      <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                    ) : (
                      <Icon name={s.icon} />
                    )}
                  </div>
                  <span className="hidden sm:inline-block whitespace-nowrap">{s.label}</span>
                </button>
                {i < steps.length - 1 && (
                  <div className="absolute top-1/2 -right-0.5 w-px h-8 -translate-y-1/2 bg-gray-200" />
                )}
              </li>
            );
        })}
      </ol>
      <div className="absolute left-0 right-0 bottom-0 h-0.5 bg-gray-100">
        <div className="h-full bg-orange-500 transition-all" style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}
