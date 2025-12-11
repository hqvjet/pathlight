"use client";
import { CourseDraftState } from '@/types/create-course';

interface ReviewStepProps {
  draft: CourseDraftState;
  onBack: () => void;
  onSubmit: () => void;
}

export function ReviewStep({ draft, onBack, onSubmit }: ReviewStepProps) {
  const levelLabel: Record<CourseDraftState['meta']['courseLevel'], string> = {
    overview: 'Tổng quan',
    intermediate: 'Trung cấp',
    advance: 'Nâng cao',
  };

  const constraintLabel: Record<CourseDraftState['meta']['courseConstraint'], string> = {
    professional: 'Chuyên nghiệp',
    academic: 'Học thuật',
    friendly: 'Gần gũi',
    humorous: 'Dí dỏm',
  };

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h2 className="text-lg font-semibold text-gray-800">Tạo khóa học</h2>
        <p className="text-sm text-gray-500">Xem lại đúng format đầu vào trước khi gọi multi-agent.</p>
      </div>
      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">Thông tin khóa học</h3>
          <dl className="grid sm:grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">Vị trí người học</dt>
              <dd className="font-medium text-gray-800">{draft.meta.userPosition || '—'}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Trình độ khóa học</dt>
              <dd className="font-medium text-gray-800">{levelLabel[draft.meta.courseLevel]}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Văn phong khóa học</dt>
              <dd className="font-medium text-gray-800">{constraintLabel[draft.meta.courseConstraint]}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Thời lượng (ngày)</dt>
              <dd className="font-medium text-gray-800">{draft.meta.durationDays}</dd>
            </div>
          </dl>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">Prompt ngắn</h3>
          <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">{draft.meta.shortPrompt || '—'}</p>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">Tài liệu ({draft.documents.length})</h3>
          {draft.documents.length === 0 && <p className="text-sm text-gray-500">Không đính kèm (tùy chọn).</p>}
          {draft.documents.length > 0 && (
            <ul className="divide-y divide-gray-100">
              {draft.documents.map((d) => (
                <li key={d.id} className="py-2 flex justify-between text-sm">
                  <span className="truncate pr-4" title={d.name}>{d.name}</span>
                  <span className="text-gray-500">{(d.size / 1024 / 1024).toFixed(2)} MB</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      <div className="flex justify-end gap-3 pt-2">
        <button onClick={onBack} className="px-6 py-2 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium">Quay Lại</button>
        <button onClick={onSubmit} className="px-6 py-2 rounded-md text-white font-semibold shadow-sm bg-orange-500 hover:bg-orange-600">Hoàn Tất</button>
      </div>
    </div>
  );
}
