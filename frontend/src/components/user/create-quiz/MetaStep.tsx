"use client";
import { QuizDraftState } from '@/types/create-quiz';
import { Sparkles, Clock, BarChart3, Crown, Zap } from 'lucide-react';

interface MetaStepProps {
  meta: QuizDraftState['meta'];
  onChange: (meta: QuizDraftState['meta']) => void;
  onNext: () => void;
  onCancel: () => void;
  isAIMode?: boolean;
  userSubscription?: number; // 0=free, 1=premium, 2=pro
}

export function MetaStep({ meta, onChange, onNext, onCancel, isAIMode = false, userSubscription = 0 }: MetaStepProps) {
  // Calculate max questions based on subscription
  // subscription = 0 (free): max 30 questions
  // subscription = 1 (premium): max 45 questions
  // subscription = 2 (pro): max 60 questions
  const maxQuestions = userSubscription === 0 ? 30 : userSubscription === 1 ? 45 : 60;
  
  const subscriptionTiers = [
    { level: 0, name: 'Miễn phí', color: 'gray', maxQ: 30, icon: Sparkles },
    { level: 1, name: 'Premium', color: 'blue', maxQ: 45, icon: Zap },
    { level: 2, name: 'Pro', color: 'purple', maxQ: 60, icon: Crown },
  ];
  
  const currentTier = subscriptionTiers.find(t => t.level === userSubscription) || subscriptionTiers[0];
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Manual mode: require title and overview
    if (!isAIMode) {
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
    <form onSubmit={handleSubmit} className="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-5">
      {isAIMode ? (
        <>
          {/* Header with subscription info */}
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-5 border border-green-200">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div className="flex-1">
                <h2 className="text-xl font-bold text-gray-900 mb-1 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-green-600" />
                  Cài đặt Quiz
                </h2>
                <p className="text-sm text-gray-600">
                  Thiết lập độ khó, số câu hỏi và thời lượng cho quiz
                </p>
              </div>
              
              {/* Subscription badge */}
              <div className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                currentTier.level === 0 ? 'bg-gray-100 text-gray-700' :
                currentTier.level === 1 ? 'bg-blue-100 text-blue-700' :
                'bg-purple-100 text-purple-700'
              }`}>
                <currentTier.icon className="w-4 h-4" />
                <span className="text-sm font-semibold">{currentTier.name}</span>
              </div>
            </div>
            
            {/* Quick stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-white/80 backdrop-blur-sm rounded-lg p-3 border border-green-100">
                <div className="text-xs text-gray-600 mb-1">Giới hạn câu hỏi</div>
                <div className="text-lg font-bold text-green-700">{maxQuestions} câu</div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-lg p-3 border border-green-100">
                <div className="text-xs text-gray-600 mb-1">Thời gian/câu</div>
                <div className="text-lg font-bold text-green-700">
                  {Math.floor((meta.duration * 60) / (meta.numQuestions || 1))}s
                </div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-lg p-3 border border-green-100">
                <div className="text-xs text-gray-600 mb-1">Tổng thời gian</div>
                <div className="text-lg font-bold text-green-700">{meta.duration}m</div>
              </div>
            </div>
          </div>

          {/* Settings card */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 space-y-5">
            {/* Difficulty selector with visual indicators */}
            <div>
              <label className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-gray-600" />
                Độ khó
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: 'easy', label: 'Dễ', color: 'green', desc: 'Phù hợp người mới' },
                  { value: 'medium', label: 'Trung bình', color: 'yellow', desc: 'Kiến thức trung cấp' },
                  { value: 'hard', label: 'Khó', color: 'red', desc: 'Thử thách nâng cao' },
                ].map((level) => (
                  <button
                    key={level.value}
                    type="button"
                    onClick={() => onChange({ ...meta, level: level.value as 'easy' | 'medium' | 'hard' })}
                    className={`p-3 rounded-lg border-2 transition-all text-left ${
                      meta.level === level.value
                        ? `border-${level.color}-500 bg-${level.color}-50 shadow-sm`
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className={`text-sm font-bold mb-1 ${
                      meta.level === level.value ? `text-${level.color}-700` : 'text-gray-700'
                    }`}>
                      {level.label}
                    </div>
                    <div className="text-xs text-gray-500">{level.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-5">
              {/* Number of questions with slider */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Số câu hỏi
                </label>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <input
                      type="number"
                      value={meta.numQuestions}
                      onChange={(e) => onChange({ ...meta, numQuestions: Math.max(1, Math.min(maxQuestions, parseInt(e.target.value) || 10)) })}
                      min="1"
                      max={maxQuestions}
                      className="w-24 px-4 py-2.5 rounded-lg border-2 border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm font-semibold text-center"
                    />
                    <input
                      type="range"
                      value={meta.numQuestions}
                      onChange={(e) => onChange({ ...meta, numQuestions: parseInt(e.target.value) })}
                      min="1"
                      max={maxQuestions}
                      className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-green-500"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">1 câu</span>
                    <span className={`font-semibold ${
                      meta.numQuestions >= maxQuestions ? 'text-amber-600' : 'text-gray-500'
                    }`}>
                      {maxQuestions} câu (Tối đa)
                    </span>
                  </div>
                  
                  {userSubscription === 0 && meta.numQuestions >= maxQuestions && (
                    <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
                      <Crown className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-amber-800">
                        <span className="font-semibold">Nâng cấp Premium</span> để tạo tối đa 45 câu hoặc <span className="font-semibold">Pro</span> cho 60 câu
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Duration with presets */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
                  <Clock className="w-4 h-4 text-gray-600" />
                  Thời lượng (phút)
                </label>
                <div className="space-y-3">
                  <input
                    type="number"
                    value={meta.duration}
                    onChange={(e) => onChange({ ...meta, duration: Math.max(1, parseInt(e.target.value) || 15) })}
                    min="1"
                    max="180"
                    className="w-full px-4 py-2.5 rounded-lg border-2 border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm font-semibold"
                  />
                  
                  <div className="flex gap-2">
                    {[5, 10, 15, 30].map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => onChange({ ...meta, duration: preset })}
                        className={`flex-1 px-2 py-1.5 text-xs font-medium rounded border transition-colors ${
                          meta.duration === preset
                            ? 'bg-green-100 border-green-500 text-green-700'
                            : 'bg-gray-50 border-gray-200 text-gray-600 hover:border-gray-300'
                        }`}
                      >
                        {preset}m
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100 space-y-6">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">Thông tin Quiz</h2>
            <p className="text-sm text-gray-600">
              Cung cấp thông tin cơ bản về bộ câu hỏi của bạn
            </p>
          </div>

          <div className="space-y-4">
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
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex items-center justify-between gap-4 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-6 py-3 rounded-lg border-2 border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 transition-colors"
        >
          Quay lại
        </button>
        <button
          type="submit"
          className={`px-8 py-3 rounded-lg text-white font-semibold shadow-lg hover:shadow-xl transition-all flex items-center gap-2 ${
            isAIMode ? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700' : 'bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600'
          }`}
        >
          Tiếp theo
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </button>
      </div>
    </form>
  );
}
