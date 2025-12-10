"use client";
import { useMemo, useState } from 'react';
import { CourseDraftState } from '@/types/create-course';

interface MetaStepProps {
  meta: CourseDraftState['meta'];
  onChange: (meta: CourseDraftState['meta']) => void;
  onBack: () => void;
  onNext: () => void;
}

export function MetaStep({ meta, onChange, onBack, onNext }: MetaStepProps) {
  const update = (patch: Partial<typeof meta>) => onChange({ ...meta, ...patch });
  const positionOptions = useMemo(
    () => [
      { value: '', label: 'Chọn vị trí' },
      { value: 'Học sinh', label: 'Học sinh' },
      { value: 'Sinh viên', label: 'Sinh viên' },
      { value: 'Lập trình viên', label: 'Lập trình viên' },
      { value: 'Quản lý', label: 'Quản lý' },
      { value: 'Sales', label: 'Sales' },
      { value: 'Marketing', label: 'Marketing' },
      { value: 'Khác', label: 'Khác (tự nhập)' },
    ],
    [],
  );

  const knownPositions = useMemo(() => positionOptions.map((p) => p.value).filter((v) => v && v !== 'Khác'), [positionOptions]);
  const isCustomPosition = meta.userPosition.trim() !== '' && !knownPositions.includes(meta.userPosition);
  const [customPosition, setCustomPosition] = useState<string>(isCustomPosition ? meta.userPosition : '');
  const selectValue = isCustomPosition ? 'Khác' : meta.userPosition;

  const handlePositionChange = (value: string) => {
    if (value === 'Khác') {
      const nextValue = customPosition || '';
      update({ userPosition: nextValue });
      return;
    }
    setCustomPosition('');
    update({ userPosition: value });
  };

  const handleCustomPosition = (value: string) => {
    setCustomPosition(value);
    update({ userPosition: value });
  };

  const isValid = Boolean(
    meta.userPosition.trim() &&
    meta.shortPrompt.trim() &&
    meta.durationDays >= 1 &&
    meta.courseLevel &&
    meta.courseConstraint
  );

  return (
    <div className="mx-auto max-w-3xl">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-semibold text-gray-900">Thông tin bắt buộc</h2>
        <p className="text-sm text-gray-600">Nhập đủ Vị trí người học, Prompt ngắn, Thời lượng (ngày), Trình độ và Văn phong để multi-agent tạo khóa học chính xác.</p>
      </div>

      <div className="mt-10 space-y-6">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div className="sm:col-span-1">
            <label htmlFor="userPosition" className="block text-sm font-medium text-gray-700 mb-1">
              Vị trí người học <span className="text-red-500">*</span>
            </label>
            <select
              id="userPosition"
              value={selectValue}
              onChange={(e) => handlePositionChange(e.target.value)}
              className="w-full h-12 px-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
            >
              {positionOptions.map((opt) => (
                <option key={opt.value || 'placeholder'} value={opt.value} disabled={opt.value === ''}>
                  {opt.label}
                </option>
              ))}
            </select>
            {selectValue === 'Khác' && (
              <input
                id="customUserPosition"
                value={customPosition}
                onChange={(e) => handleCustomPosition(e.target.value)}
                placeholder="Nhập vị trí khác (bắt buộc)"
                className="mt-3 w-full h-11 px-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
              />
            )}
            <p className="text-xs text-gray-500 mt-1">Chọn vị trí mô tả rõ bạn là ai để nội dung phù hợp.</p>
          </div>

          <div className="sm:col-span-1">
            <label htmlFor="courseLevel" className="block text-sm font-medium text-gray-700 mb-1">
              Trình độ khóa học <span className="text-red-500">*</span>
            </label>
            <select
              id="courseLevel"
              value={meta.courseLevel}
              onChange={(e) => update({ courseLevel: e.target.value as CourseDraftState['meta']['courseLevel'] })}
              className="w-full h-12 px-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
            >
              <option value="overview">Tổng quan</option>
              <option value="intermediate">Trung cấp</option>
              <option value="advance">Nâng cao</option>
            </select>
          </div>

          <div className="sm:col-span-1">
            <label htmlFor="courseConstraint" className="block text-sm font-medium text-gray-700 mb-1">
              Văn phong khóa học <span className="text-red-500">*</span>
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
              Thời lượng (ngày) <span className="text-red-500">*</span>
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
            Prompt ngắn <span className="text-red-500">*</span>
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
        <button
          onClick={onNext}
          disabled={!isValid}
          className="px-8 h-11 rounded-md text-white font-semibold shadow-sm bg-orange-500 hover:bg-orange-600 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Tiếp theo
        </button>
      </div>
    </div>
  );
}
