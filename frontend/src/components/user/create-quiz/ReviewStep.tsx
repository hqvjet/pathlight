"use client";
import { QuizDraftState } from '@/types/create-quiz';
import { FileText, Clock, BarChart3, FileUp, PenTool } from 'lucide-react';

interface ReviewStepProps {
  draft: QuizDraftState;
  onBack: () => void;
  onSubmit: () => void;
  isSubmitting: boolean;
}

export function ReviewStep({ draft, onBack, onSubmit, isSubmitting }: ReviewStepProps) {
  const isAI = draft.creationType === 'ai';

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100 space-y-6">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">Xem lại thông tin</h2>
          <p className="text-sm text-gray-600">Kiểm tra lại thông tin trước khi tạo quiz</p>
        </div>

        {/* Creation Type Badge */}
        <div className="flex items-center gap-3 pb-4 border-b border-gray-200">
          {isAI ? (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 text-green-700 rounded-lg text-sm font-semibold">
              <FileUp className="w-4 h-4" />
              <span>Tạo bằng AI</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-orange-50 text-orange-700 rounded-lg text-sm font-semibold">
              <PenTool className="w-4 h-4" />
              <span>Tự tạo</span>
            </div>
          )}
          {!isAI && (
            <span className="text-xs text-gray-500">Không tính EXP</span>
          )}
        </div>

        {isAI ? (
          /* AI Mode Review */
          <div className="space-y-4">
            {draft.documents.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Tài liệu đã tải lên
                </h3>
                <ul className="space-y-1.5">
                  {draft.documents.map((doc) => (
                    <li key={doc.id} className="text-sm text-gray-600 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                      <span className="truncate">{doc.name}</span>
                      <span className="text-xs text-gray-400">({(doc.size / 1024).toFixed(1)} KB)</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Prompt cho AI</h3>
              <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3 border border-gray-200">
                {draft.meta.shortPrompt || '(Không có)'}
              </p>
            </div>

            {draft.meta.userPosition && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Vị trí</h3>
                <p className="text-sm text-gray-600">{draft.meta.userPosition}</p>
              </div>
            )}

            <div className="grid sm:grid-cols-3 gap-4 pt-2">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Độ khó</p>
                  <p className="text-sm font-semibold text-gray-700">
                    {draft.meta.level === 'easy' ? 'Dễ' : draft.meta.level === 'medium' ? 'Trung bình' : 'Khó'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Thời lượng</p>
                  <p className="text-sm font-semibold text-gray-700">{draft.meta.duration} phút</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Manual Mode Review */
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Tên quiz</h3>
              <p className="text-sm text-gray-600">{draft.meta.title || '(Chưa có)'}</p>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Mô tả</h3>
              <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3 border border-gray-200">
                {draft.meta.overview || '(Chưa có)'}
              </p>
            </div>

            <div className="grid sm:grid-cols-3 gap-4">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Độ khó</p>
                  <p className="text-sm font-semibold text-gray-700">
                    {draft.meta.level === 'easy' ? 'Dễ' : draft.meta.level === 'medium' ? 'Trung bình' : 'Khó'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Thời lượng</p>
                  <p className="text-sm font-semibold text-gray-700">{draft.meta.duration} phút</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Số câu hỏi</p>
                  <p className="text-sm font-semibold text-gray-700">{draft.cards.length}</p>
                </div>
              </div>
            </div>

            {draft.cards.length > 0 && (
              <div className="border-t pt-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Câu hỏi đã tạo</h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {draft.cards.map((card, idx) => (
                    <div key={card.id} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <p className="text-sm text-gray-900 font-medium">
                          <span className="text-gray-500">Câu {idx + 1}:</span> {card.question || '(Chưa có câu hỏi)'}
                        </p>
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold shrink-0 ${
                          card.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                          card.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {card.difficulty === 'easy' ? 'Dễ' : card.difficulty === 'medium' ? 'TB' : 'Khó'}
                        </span>
                      </div>
                      <div className="space-y-0.5 text-xs text-gray-600">
                        {[1, 2, 3, 4].map((num) => (
                          <p key={num} className={card.answer === num ? 'font-semibold text-green-600' : ''}>
                            {num}. {card[`option${num}` as 'option1' | 'option2' | 'option3' | 'option4']}
                            {card.answer === num && ' ✓'}
                          </p>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between gap-4">
        <button
          type="button"
          onClick={onBack}
          disabled={isSubmitting}
          className="px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Quay lại
        </button>
        <button
          type="button"
          onClick={onSubmit}
          disabled={isSubmitting}
          className={`px-6 py-2.5 rounded-lg text-white font-semibold shadow-sm text-sm disabled:opacity-50 disabled:cursor-not-allowed ${
            isAI ? 'bg-green-500 hover:bg-green-600' : 'bg-orange-500 hover:bg-orange-600'
          }`}
        >
          {isSubmitting ? (
            <span className="inline-flex items-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
              Đang xử lý...
            </span>
          ) : (
            isAI ? 'Gửi yêu cầu tạo Quiz' : 'Tạo Quiz'
          )}
        </button>
      </div>
    </div>
  );
}
