"use client";
import { CourseDraftState } from '@/fake/courses';

interface MetaStepProps {
  meta: CourseDraftState['meta'];
  onChange: (meta: CourseDraftState['meta']) => void;
  onBack: () => void;
  onNext: () => void;
}

export function MetaStep({ meta, onChange, onBack, onNext }: MetaStepProps) {
  const titleLimit = 80;
  const descLimit = 120;
  const update = (patch: Partial<typeof meta>) => onChange({ ...meta, ...patch });

  return (
    <div className="space-y-10">
      <div className="text-center space-y-2">
        <h2 className="text-lg font-semibold text-gray-800">Mô Tả Khóa Học</h2>
      </div>
      <div className="space-y-8">
        {/* Title */}
        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-gray-700">Tiêu Đề</label>
          <div className="relative">
            <input
              value={meta.title}
              maxLength={titleLimit}
              onChange={e => update({ title: e.target.value })}
              placeholder="Nhập tiêu đề"
              className="w-full h-11 px-3 rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
            />
            <span className="absolute top-1/2 -translate-y-1/2 right-3 text-xs text-gray-400">{meta.title.length}/{titleLimit}</span>
          </div>
        </div>
        {/* Description */}
        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-gray-700">Mô Tả Khóa Học</label>
          <div className="relative">
            <input
              value={meta.description}
              maxLength={descLimit}
              onChange={e => update({ description: e.target.value })}
              placeholder="Nhập mô tả khóa học"
              className="w-full h-11 px-3 rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
            />
            <span className="absolute top-1/2 -translate-y-1/2 right-3 text-xs text-gray-400">{meta.description.length}/{descLimit}</span>
          </div>
        </div>
        {/* Depth + Duration */}
        <div className="grid gap-6 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-gray-700">Độ sâu của khóa học</label>
            <select
              value={meta.level}
              onChange={e => update({ level: e.target.value })}
              className="w-full h-11 px-3 rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
            >
              <option value="beginner">Cơ bản</option>
              <option value="intermediate">Trung bình</option>
              <option value="advanced">Nâng cao</option>
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-gray-700">Thời lượng khóa học</label>
            <div className="flex gap-2">
              <input
                type="number"
                min={1}
                value={meta.durationValue}
                onChange={e => update({ durationValue: Number(e.target.value) })}
                className="w-32 h-11 px-3 rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
              />
              <select
                value={meta.durationUnit}
                onChange={e => update({ durationUnit: e.target.value as CourseDraftState['meta']['durationUnit'] })}
                className="h-11 px-3 rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/60 text-sm"
              >
                <option value="Ngày">Ngày</option>
                <option value="Tuần">Tuần</option>
                <option value="Tháng">Tháng</option>
              </select>
            </div>
          </div>
        </div>
      </div>
      <div className="flex justify-between pt-4">
        <button onClick={onBack} className="px-6 h-11 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium text-sm">Hủy</button>
        <button onClick={onNext} className="px-8 h-11 rounded-md text-white font-semibold shadow-sm bg-orange-500 hover:bg-orange-600 text-sm">Bước Tiếp</button>
      </div>
    </div>
  );
}
