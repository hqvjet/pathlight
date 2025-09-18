"use client";
import Image from 'next/image';
import { useEffect, useMemo, useRef, useState } from 'react';
import { CourseDraftState } from '@/fake/courses';
import { courseApi } from '@/lib/api/course';

interface SuccessStepProps {
  draft: CourseDraftState;
  onRestart: () => void;
  onGoToCourses: () => void;
}

type StatusPhase = 'initializing' | 'queued' | 'processing' | 'generating' | 'finalizing' | 'completed' | 'failed';

export function SuccessStep({ draft, onRestart, onGoToCourses }: SuccessStepProps) {
  const [phase, setPhase] = useState<StatusPhase>('queued');
  const [message, setMessage] = useState<string>('Đang xếp hàng...');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const courseId = draft.courseId;

  const checkpoints = useMemo(() => (
    [
      // We map 'initializing' to the first checkpoint visually (same as 'queued')
      { key: 'queued', label: 'Đã nhận yêu cầu' },
      { key: 'processing', label: 'Phân tích tài liệu' },
      { key: 'generating', label: 'Tạo nội dung khóa học' },
      { key: 'finalizing', label: 'Hoàn thiện cấu trúc' },
      { key: 'completed', label: 'Hoàn tất' }
    ] as Array<{ key: StatusPhase; label: string }>
  ), []);

  useEffect(() => {
    if (!courseId) return;
    const poll = async () => {
      try {
        const resp = await courseApi.getStatus(courseId);
        // If backend returns HTTP 200 but semantic status indicates not found yet,
        // treat as initializing to handle DynamoDB eventual consistency.
        const semantic = (resp?.data as { status?: number; message?: string } | undefined);
        if (
          semantic?.status === 404 ||
          semantic?.status === 501 ||
          (typeof semantic?.message === 'string' && /không\s*tìm\s*thấy\s*khóa\s*học/i.test(semantic.message))
        ) {
          setPhase('queued');
          setMessage('Đang khởi tạo... Hệ thống đang thiết lập khóa học.');
          setLastUpdated(new Date());
          return;
        }
        // Possible shapes:
        // - { body: { phase?: string; message?: string } }
        // - { body: { status?: boolean; vectorized?: boolean; generated_plan?: boolean; generated_lessons?: boolean; generated_final_test?: boolean; progress?: string } }
        interface StatusBody {
          phase?: string;
          message?: string;
          status?: boolean;
          vectorized?: boolean;
          generated_plan?: boolean;
          generated_lessons?: boolean;
          generated_final_test?: boolean;
          progress?: string;
          updated_at?: string;
        }
        const body = resp.data?.body as StatusBody | undefined;

        // Phase priority from explicit phase or derived from booleans.
        let derivedPhase: StatusPhase = 'processing';
        if (typeof body?.phase === 'string') {
          const p = body.phase.toLowerCase();
          // Normalize known terminal/near-terminal strings
          const completedSynonyms = ['completed', 'complete', 'done', 'final_ready', 'ready'];
          if (completedSynonyms.includes(p)) {
            derivedPhase = 'completed';
          } else if (['queued','processing','generating','finalizing','failed'].includes(p)) {
            derivedPhase = p as StatusPhase;
          }
        }

        if (body) {
          // Completion conditions
          const progressText = (body.progress || '').toString().toLowerCase();
          const isCompleted = body.status === true || /final_ready|complete|completed|done|success/.test(progressText);
          if (isCompleted) {
            derivedPhase = 'completed';
          } else {
            // Ignore 'vectorized' flag entirely per requirements.
            if (body.generated_final_test) {
              derivedPhase = 'finalizing';
            } else if (body.generated_lessons || body.generated_plan) {
              derivedPhase = 'generating';
            } else if (!derivedPhase || derivedPhase === 'processing') {
              derivedPhase = 'processing';
            }
          }
        }

        setPhase(derivedPhase);

        if (body?.message || resp.data?.message) {
          setMessage(body?.message || (resp.data?.message as string));
        } else {
          // Friendly default message by phase
          const defaults: Record<StatusPhase, string> = {
            initializing: 'Đang khởi tạo... Hệ thống đang thiết lập khóa học.',
            queued: 'Đang xếp hàng... ',
            processing: 'Phân tích tài liệu...',
            generating: 'Đang tạo nội dung khóa học...',
            finalizing: 'Đang hoàn thiện cấu trúc...',
            completed: 'Hoàn tất.',
            failed: 'Có lỗi xảy ra. Vui lòng thử lại.'
          };
          setMessage(defaults[derivedPhase]);
        }
        setLastUpdated(new Date());
  // Stop on terminal state
  if (derivedPhase === 'completed' || derivedPhase === 'failed') {
          if (timerRef.current) clearInterval(timerRef.current);
        }
      } catch (err: unknown) {
        // On early 404 (course not yet created in DB), show initializing state and keep polling.
        const maybe: { status?: number } = (err as object) ?? {};
        if (typeof maybe.status === 'number' && maybe.status === 404) {
          setPhase('queued'); // visually map to first step
          setMessage('Đang khởi tạo... Hệ thống đang thiết lập khóa học.');
          setLastUpdated(new Date());
          return;
        }
        // Other network/parse errors: keep polling silently
      }
    };
    // initial call
    poll();
    timerRef.current = setInterval(poll, 3000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [courseId]);

  const activeIndex = checkpoints.findIndex(c => c.key === phase);

  // Dynamic header and description based on phase to avoid premature success copy
  const { titleText, descText } = useMemo(() => {
    const name = draft.meta.title || 'mới';
    switch (phase) {
      case 'completed':
        return {
          titleText: 'Hoàn Thành',
          descText: `Khóa học ${name} đã được tạo thành công. Bạn có thể bắt đầu thêm nội dung bài học hoặc quay lại để tạo khóa học khác.`,
        };
      case 'failed':
        return {
          titleText: 'Không thể tạo khóa học',
          descText: 'Đã xảy ra lỗi trong quá trình tạo khóa học. Vui lòng thử lại hoặc tạo yêu cầu mới.',
        };
      case 'finalizing':
        return {
          titleText: 'Đang hoàn thiện cấu trúc',
          descText: 'Hệ thống đang sắp xếp và hoàn thiện cấu trúc khóa học của bạn. Vui lòng chờ trong giây lát.',
        };
      case 'generating':
        return {
          titleText: 'Đang tạo nội dung khóa học',
          descText: 'Hệ thống đang tạo nội dung bài học dựa trên tài liệu của bạn. Tiến trình sẽ tự động cập nhật.',
        };
      case 'processing':
        return {
          titleText: 'Đang phân tích tài liệu',
          descText: 'Hệ thống đang phân tích tài liệu để lập kế hoạch cho khóa học.',
        };
      case 'queued':
      case 'initializing':
      default:
        return {
          titleText: 'Khởi tạo yêu cầu',
          descText: 'Yêu cầu của bạn đã được tiếp nhận và đang xếp hàng xử lý. Vui lòng đợi trong giây lát.',
        };
    }
  }, [phase, draft.meta.title]);

  return (
    <div className="flex flex-col items-center justify-center text-center py-16 space-y-8">
      <div className="relative w-64 h-64 mx-auto">
        <Image src="/assets/images/create_course_success.png" alt="Tạo khóa học thành công" fill priority className="object-contain drop-shadow-sm" />
      </div>
      <div className="space-y-4 max-w-xl">
        <h2 className="text-2xl font-semibold text-gray-900">{titleText}</h2>
        <p className="text-gray-600 leading-relaxed text-base">{descText}</p>
      </div>

      {/* Checkpoints */}
      {courseId && (
        <div className="w-full max-w-2xl mt-4">
          {/* Track lines (base + progress) */}
          <div className="relative">
            <div className="absolute left-0 right-0 top-5 h-0.5 bg-gray-200" aria-hidden="true" />
            <div
              className="absolute left-0 top-5 h-0.5 bg-orange-500 transition-all"
              style={{ width: `${Math.max(0, activeIndex) / Math.max(1, checkpoints.length - 1) * 100}%` }}
              aria-hidden="true"
            />
            {/* Nodes + labels aligned in one grid so titles center under nodes */}
            <div className="grid grid-cols-5 gap-0">
              {checkpoints.map((c, idx) => {
                const isActive = idx === activeIndex;
                const isDone = idx < activeIndex;
                return (
                  <div key={c.key} className="col-span-1 flex flex-col items-center">
                    <div
                      className={
                        `z-10 flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold border-2 ` +
                        (isDone || isActive
                          ? 'bg-orange-500 border-orange-500 text-white shadow-sm'
                          : 'bg-white border-gray-300 text-gray-400') +
                        (isActive ? ' ring-2 ring-orange-300' : '')
                      }
                      aria-current={isActive ? 'step' : undefined}
                    >
                      {idx + 1}
                    </div>
                    <div className={`mt-2 text-center truncate px-1 text-[11px] sm:text-xs ${isActive ? 'text-gray-900 font-medium' : 'text-gray-600'}`}>
                      {c.label}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="mt-4 text-sm">
            {/* Status line emphasis */}
            <div className={
              `inline-flex items-center gap-2 px-3 py-2 rounded-md ` +
              (phase === 'completed' ? 'bg-green-50 text-green-700' : phase === 'failed' ? 'bg-red-50 text-red-600' : 'bg-orange-50 text-orange-700')
            }>
              {phase !== 'completed' && phase !== 'failed' && (
                <span className="inline-block w-2 h-2 rounded-full bg-orange-500 animate-pulse" aria-hidden="true" />
              )}
              <span className="font-semibold">Trạng thái:</span>
              <span>{message}</span>
              {lastUpdated && <span className="opacity-70">• Cập nhật: {lastUpdated.toLocaleTimeString()}</span>}
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-4 pt-4">
        <button
          onClick={onGoToCourses}
          disabled={phase !== 'completed'}
          title={phase !== 'completed' ? 'Chỉ khả dụng sau khi hoàn tất' : undefined}
          className={`px-8 h-11 rounded-md text-white font-semibold shadow-sm ${phase === 'completed' ? 'bg-orange-500 hover:bg-orange-600' : 'bg-orange-300 cursor-not-allowed'}`}
        >
          Đi đến Khóa Học
        </button>
        <button onClick={onRestart} className="px-8 h-11 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium">Tạo Khóa Học Khác</button>
      </div>
    </div>
  );
}
