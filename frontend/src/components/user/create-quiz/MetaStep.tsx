"use client";
import { QuizDraftState } from '@/types/create-quiz';

interface MetaStepProps {
  meta: QuizDraftState['meta'];
  onChange: (meta: QuizDraftState['meta']) => void;
  onNext: () => void;
  onCancel: () => void;
  isAIMode?: boolean;
}

export function MetaStep({ meta, onChange, onNext, onCancel, isAIMode = false }: MetaStepProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // AI mode: require shortPrompt
    if (isAIMode) {
      if (!meta.shortPrompt?.trim()) {
        alert('Vui lòng nhập prompt cho AI');
        return;
      }
    } else {
      // Manual mode: require title and overview
      if (!meta.title.trim()) {
        alert('Vui lòng nhập tên quiz');
        return;
      }
      if (!meta.overview.trim()) {
        alert('Vui lòng nhập mô tả');
        return;
      }
    }
    onNext();
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100 space-y-6">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">
            {isAIMode ? 'Thông tin cho AI tạo Quiz' : 'Thông tin Quiz'}
          </h2>
          <p className="text-sm text-gray-600">
            {isAIMode 
              ? 'Cung cấp thông tin để AI tạo quiz phù hợp với nhu cầu của bạn'
              : 'Cung cấp thông tin cơ bản về bộ câu hỏi của bạn'
            }
          </p>
        </div>

        <div className="space-y-4">
          {isAIMode ? (
            <>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Prompt cho AI <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={meta.shortPrompt || ''}
                  onChange={(e) => onChange({ ...meta, shortPrompt: e.target.value })}
                  placeholder="Ví dụ: Tạo quiz về JavaScript ES6 với focus vào arrow functions và promises..."
                  rows={4}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm resize-none"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Vị trí của bạn (tùy chọn)
                </label>
                <select
                  value={meta.userPosition || ''}
                  onChange={(e) => onChange({ ...meta, userPosition: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
                >
                  <option value="">-- Chọn vị trí --</option>
                  <option value="Student">Học sinh / Sinh viên</option>
                  <option value="Junior Developer">Junior Developer</option>
                  <option value="Senior Developer">Senior Developer</option>
                  <option value="Team Lead">Team Lead</option>
                  <option value="Manager">Manager</option>
                  <option value="Teacher">Giáo viên</option>
                  <option value="Researcher">Nhà nghiên cứu</option>
                </select>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Độ khó</label>
                  <select
                    value={meta.level}
                    onChange={(e) => onChange({ ...meta, level: e.target.value as 'easy' | 'medium' | 'hard' })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
                  >
                    <option value="easy">Dễ</option>
                    <option value="medium">Trung bình</option>
                    <option value="hard">Khó</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Thời lượng (phút)
                  </label>
                  <input
                    type="number"
                    value={meta.duration}
                    onChange={(e) => onChange({ ...meta, duration: Math.max(1, parseInt(e.target.value) || 15) })}
                    min="1"
                    max="180"
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
                  />
                </div>
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Tên quiz <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={meta.title}
                  onChange={(e) => onChange({ ...meta, title: e.target.value })}
                  placeholder="Ví dụ: JavaScript Cơ Bản"
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Mô tả <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={meta.overview}
                  onChange={(e) => onChange({ ...meta, overview: e.target.value })}
                  placeholder="Mô tả ngắn gọn về nội dung quiz"
                  rows={4}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-sm resize-none"
                  required
                />
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Độ khó</label>
                  <select
                    value={meta.level}
                    onChange={(e) => onChange({ ...meta, level: e.target.value as 'easy' | 'medium' | 'hard' })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-sm"
                  >
                    <option value="easy">Dễ</option>
                    <option value="medium">Trung bình</option>
                    <option value="hard">Khó</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Thời lượng (phút)
                  </label>
                  <input
                    type="number"
                    value={meta.duration}
                    onChange={(e) => onChange({ ...meta, duration: Math.max(1, parseInt(e.target.value) || 1) })}
                    min="1"
                    max="180"
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-sm"
                  />
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between gap-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 text-sm"
        >
          Quay lại
        </button>
        <button
          type="submit"
          className={`px-6 py-2.5 rounded-lg text-white font-semibold shadow-sm text-sm ${
            isAIMode ? 'bg-green-500 hover:bg-green-600' : 'bg-orange-500 hover:bg-orange-600'
          }`}
        >
          Tiếp theo →
        </button>
      </div>
    </form>
  );
}
