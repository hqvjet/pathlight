"use client";
import { CourseDraftState } from '@/fake/courses';

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
        <h2 className="text-2xl font-semibold text-gray-900">Mô Tả Khóa Học</h2>
        <p className="text-sm text-gray-600">Chọn độ sâu (độ khó) và thời lượng. Các thông tin khác sẽ được AI đề xuất.</p>
      </div>

      <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2">
        {/* Difficulty */}
        <div className="sm:col-span-2">
          <label htmlFor="level" className="block text-sm font-medium text-gray-700 mb-1">
            Độ sâu của khóa học
          </label>
          <select
            id="level"
            value={meta.level}
            onChange={e => update({ level: e.target.value })}
            className="w-full h-12 px-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
          >
            <option value="beginner">Cơ bản</option>
            <option value="intermediate">Trung bình</option>
            <option value="advanced">Nâng cao</option>
          </select>
        </div>

        {/* Duration value */}
        <div>
          <label htmlFor="durationValue" className="block text-sm font-medium text-gray-700 mb-1">
            Thời lượng (số lượng)
          </label>
          <input
            id="durationValue"
            type="number"
            min={1}
            value={meta.durationValue}
            onChange={e => update({ durationValue: Number(e.target.value) })}
            className="w-full h-12 px-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
          />
        </div>

        {/* Duration unit */}
        <div>
          <label htmlFor="durationUnit" className="block text-sm font-medium text-gray-700 mb-1">
            Đơn vị thời lượng
          </label>
          <select
            id="durationUnit"
            value={meta.durationUnit}
            onChange={e => update({ durationUnit: e.target.value as CourseDraftState['meta']['durationUnit'] })}
            className="w-full h-12 px-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
          >
            <option value="Ngày">Ngày</option>
            <option value="Tuần">Tuần</option>
            <option value="Tháng">Tháng</option>
          </select>
        </div>
      </div>

      <div className="mt-10 flex items-center justify-between">
        <button onClick={onBack} className="px-6 h-11 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium text-sm">Hủy</button>
        <button onClick={onNext} className="px-8 h-11 rounded-md text-white font-semibold shadow-sm bg-orange-500 hover:bg-orange-600 text-sm">Bước Tiếp</button>
      </div>
    </div>
  );
}
