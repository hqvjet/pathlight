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
          if (['queued','processing','generating','finalizing','completed','failed'].includes(p)) {
            derivedPhase = p as StatusPhase;
          }
        } else if (body) {
          // Ignore 'vectorized' flag entirely per requirements.
          if (body.generated_final_test) derivedPhase = 'finalizing';
          if (body.generated_lessons) derivedPhase = 'generating';
          if (body.generated_plan) derivedPhase = 'generating';
          // If none of the above booleans true yet, we keep 'processing'.
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

  return (
    <div className="flex flex-col items-center justify-center text-center py-16 space-y-8">
      <div className="relative w-64 h-64 mx-auto">
        <Image src="/assets/images/create_course_success.png" alt="Tạo khóa học thành công" fill priority className="object-contain drop-shadow-sm" />
      </div>
      <div className="space-y-4 max-w-xl">
        <h2 className="text-2xl font-semibold text-gray-900">Hoàn Thành</h2>
        <p className="text-gray-600 leading-relaxed text-base">Khóa học <span className="font-semibold text-gray-900">{draft.meta.title || 'mới'}</span> đã được tạo thành công. Bạn có thể bắt đầu thêm nội dung bài học hoặc quay lại để tạo khóa học khác.</p>
      </div>

      {/* Checkpoints */}
      {courseId && (
        <div className="w-full max-w-2xl mt-4">
          <div className="flex items-center justify-between">
            {checkpoints.map((c, idx) => (
              <div key={c.key} className="flex-1 flex items-center">
                <div className={`flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold border-2 ${idx <= activeIndex ? 'bg-orange-500 border-orange-500 text-white' : 'bg-white border-gray-300 text-gray-400'}`}>
                  {idx + 1}
                </div>
                {idx < checkpoints.length - 1 && (
                  <div className={`h-0.5 flex-1 mx-2 ${idx < activeIndex ? 'bg-orange-500' : 'bg-gray-200'}`} />
                )}
              </div>
            ))}
          </div>
          <div className="mt-3 grid grid-cols-5 text-[11px] sm:text-xs text-gray-600">
            {checkpoints.map(c => (
              <div key={c.key} className="text-center truncate px-1">
                {c.label}
              </div>
            ))}
          </div>
          <div className="mt-4 text-sm text-gray-500">
            <span className="font-medium text-gray-700">Trạng thái:</span> {message}
            {lastUpdated && <span className="ml-2">• Cập nhật: {lastUpdated.toLocaleTimeString()}</span>}
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-4 pt-4">
        <button onClick={onGoToCourses} className="px-8 h-11 rounded-md bg-orange-500 hover:bg-orange-600 text-white font-semibold shadow-sm">Đi đến Khóa Học</button>
        <button onClick={onRestart} className="px-8 h-11 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium">Tạo Khóa Học Khác</button>
      </div>
    </div>
  );
}
