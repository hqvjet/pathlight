"use client";
import { CourseDraftState } from '@/types/create-course';

interface MetaStepProps {
  meta: CourseDraftState['meta'];
  onChange: (meta: CourseDraftState['meta']) => void;
  onBack: () => void;
  onNext: () => void;
}

export function MetaStep({ meta, onChange, onBack, onNext }: MetaStepProps) {
  const update = (patch: Partial<typeof meta>) => onChange({ ...meta, ...patch });

  return (
    <div className="mx-auto max-w-3xl">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-semibold text-gray-900">Thông tin bắt buộc cho multi-agent</h2>
        <p className="text-sm text-gray-600">Nhập đúng các trường trong đặc tả: User position, Short prompt, Course duration (ngày), Course level, Course constraint.</p>
      </div>

      <div className="mt-10 space-y-6">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div className="sm:col-span-1">
            <label htmlFor="userPosition" className="block text-sm font-medium text-gray-700 mb-1">
              User position <span className="text-red-500">*</span>
            </label>
            <input
              id="userPosition"
              value={meta.userPosition}
              onChange={(e) => update({ userPosition: e.target.value })}
              placeholder="Học sinh, sinh viên, coder..."
              className="w-full h-12 px-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
            />
          </div>

          <div className="sm:col-span-1">
            <label htmlFor="courseLevel" className="block text-sm font-medium text-gray-700 mb-1">
              Course level <span className="text-red-500">*</span>
            </label>
            <select
              id="courseLevel"
              value={meta.courseLevel}
              onChange={(e) => update({ courseLevel: e.target.value as CourseDraftState['meta']['courseLevel'] })}
              className="w-full h-12 px-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
            >
              <option value="overview">Overview</option>
              <option value="intermediate">Intermediate</option>
              <option value="advance">Advance</option>
            </select>
          </div>

          <div className="sm:col-span-1">
            <label htmlFor="courseConstraint" className="block text-sm font-medium text-gray-700 mb-1">
              Course constraint (văn phong) <span className="text-red-500">*</span>
            </label>
            <select
              id="courseConstraint"
              value={meta.courseConstraint}
              onChange={(e) => update({ courseConstraint: e.target.value as CourseDraftState['meta']['courseConstraint'] })}
              className="w-full h-12 px-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
            >
              <option value="professional">Chuyên nghiệp</option>
              <option value="academic">Học thuật</option>
              <option value="friendly">Gần gũi</option>
              <option value="humorous">Dí dỏm</option>
            </select>
          </div>

          <div className="sm:col-span-1">
            <label htmlFor="durationDays" className="block text-sm font-medium text-gray-700 mb-1">
              Course duration (ngày) <span className="text-red-500">*</span>
            </label>
            <input
              id="durationDays"
              type="number"
              min={1}
              value={meta.durationDays}
              onChange={(e) => update({ durationDays: Math.max(1, Number(e.target.value) || 1) })}
              className="w-full h-12 px-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
            />
          </div>
        </div>

        <div className="sm:col-span-2">
          <label htmlFor="shortPrompt" className="block text-sm font-medium text-gray-700 mb-1">
            Short user prompt <span className="text-red-500">*</span>
          </label>
          <textarea
            id="shortPrompt"
            rows={5}
            value={meta.shortPrompt}
            onChange={(e) => update({ shortPrompt: e.target.value })}
            placeholder="Ví dụ: Hãy tạo khóa học về Docker cho người bắt đầu..."
            className="w-full px-3 py-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm resize-none"
          />
          <p className="text-xs text-gray-500 mt-1">Prompt có thể thay thế hoàn toàn tài liệu đính kèm nếu bạn không có file.</p>
        </div>
      </div>

      <div className="mt-10 flex items-center justify-between">
        <button onClick={onBack} className="px-6 h-11 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium text-sm">Quay lại</button>
        <button onClick={onNext} className="px-8 h-11 rounded-md text-white font-semibold shadow-sm bg-orange-500 hover:bg-orange-600 text-sm">Bước tiếp</button>
      </div>
    </div>
  );
}
