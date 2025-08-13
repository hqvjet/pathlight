"use client";
import { CourseDraftState } from '@/fake/courses';

interface ReviewStepProps {
  draft: CourseDraftState;
  onBack: () => void;
  onSubmit: () => void;
}

export function ReviewStep({ draft, onBack, onSubmit }: ReviewStepProps) {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h2 className="text-lg font-semibold text-gray-800">Tạo Khóa Học</h2>
        <p className="text-sm text-gray-500">Xem lại thông tin trước khi hoàn tất.</p>
      </div>
      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">Tài liệu ({draft.documents.length})</h3>
          <ul className="divide-y divide-gray-100">
            {draft.documents.map(d => (
              <li key={d.id} className="py-2 flex justify-between text-sm">
                <span className="truncate pr-4" title={d.name}>{d.name}</span>
                <span className="text-gray-500">{(d.size/1024/1024).toFixed(2)} MB</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">Thông tin khóa học</h3>
          <dl className="grid sm:grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">Tiêu đề</dt>
              <dd className="font-medium text-gray-800">{draft.meta.title || '—'}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Danh mục</dt>
              <dd className="font-medium text-gray-800">{draft.meta.category || '—'}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Ngôn ngữ</dt>
              <dd className="font-medium text-gray-800">{draft.meta.language || '—'}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Trình độ</dt>
              <dd className="font-medium text-gray-800">{draft.meta.level || '—'}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Thời lượng</dt>
              <dd className="font-medium text-gray-800">{draft.meta.durationValue} {draft.meta.durationUnit}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-gray-500">Mô tả</dt>
              <dd className="font-medium text-gray-800 whitespace-pre-line mt-1">{draft.meta.description || '—'}</dd>
            </div>
          </dl>
        </div>
      </div>
      <div className="flex justify-end gap-3 pt-2">
        <button onClick={onBack} className="px-6 py-2 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium">Quay Lại</button>
        <button onClick={onSubmit} className="px-6 py-2 rounded-md text-white font-semibold shadow-sm bg-orange-500 hover:bg-orange-600">Hoàn Tất</button>
      </div>
    </div>
  );
}
