"use client";
import Image from 'next/image';
import { CourseDraftState } from '@/fake/courses';

interface SuccessStepProps {
  draft: CourseDraftState;
  onRestart: () => void;
  onGoToCourses: () => void;
}

export function SuccessStep({ draft, onRestart, onGoToCourses }: SuccessStepProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 space-y-8">
      <div className="relative w-64 h-64 mx-auto">
        <Image src="/assets/images/create_course_success.png" alt="Tạo khóa học thành công" fill priority className="object-contain drop-shadow-sm" />
      </div>
      <div className="space-y-4 max-w-xl">
        <h2 className="text-2xl font-semibold text-gray-900">Hoàn Thành</h2>
        <p className="text-gray-600 leading-relaxed text-base">Khóa học <span className="font-semibold text-gray-900">{draft.meta.title || 'mới'}</span> đã được tạo thành công. Bạn có thể bắt đầu thêm nội dung bài học hoặc quay lại để tạo khóa học khác.</p>
      </div>
      <div className="flex flex-wrap gap-4 pt-4">
        <button onClick={onGoToCourses} className="px-8 h-11 rounded-md bg-orange-500 hover:bg-orange-600 text-white font-semibold shadow-sm">Đi đến Khóa Học</button>
        <button onClick={onRestart} className="px-8 h-11 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium">Tạo Khóa Học Khác</button>
      </div>
    </div>
  );
}
