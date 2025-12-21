"use client";
import { QuizCardDraft, getQuestionLimit, SubscriptionTier, createEmptyCard } from '@/types/create-quiz';
import { useState } from 'react';
import { Trash2, Plus, ChevronDown, ChevronUp } from 'lucide-react';

interface QuestionsStepProps {
  cards: QuizCardDraft[];
  onChange: (cards: QuizCardDraft[]) => void;
  onNext: () => void;
  onBack: () => void;
  userTier?: SubscriptionTier;
}

export function QuestionsStep({ cards, onChange, onNext, onBack, userTier = 'free' }: QuestionsStepProps) {
  const [expandedId, setExpandedId] = useState<string | null>(cards[0]?.id || null);
  const limit = getQuestionLimit(userTier);

  const addCard = () => {
    if (cards.length >= limit) {
      alert(`Gói ${userTier} chỉ cho phép tối đa ${limit} câu hỏi. Nâng cấp để thêm câu hỏi.`);
      return;
    }
    const newCard = createEmptyCard();
    onChange([...cards, newCard]);
    setExpandedId(newCard.id);
  };

  const removeCard = (id: string) => {
    if (cards.length === 1) {
      alert('Quiz phải có ít nhất 1 câu hỏi');
      return;
    }
    onChange(cards.filter((c) => c.id !== id));
  };

  const updateCard = (id: string, updates: Partial<QuizCardDraft>) => {
    onChange(cards.map((c) => (c.id === id ? { ...c, ...updates } : c)));
  };

  const handleNext = () => {
    if (cards.length === 0) {
      alert('Vui lòng thêm ít nhất 1 câu hỏi');
      return;
    }
    for (const card of cards) {
      if (!card.question.trim()) {
        alert('Vui lòng điền đầy đủ câu hỏi');
        return;
      }
      if (!card.option1.trim() || !card.option2.trim() || !card.option3.trim() || !card.option4.trim()) {
        alert('Mỗi câu hỏi phải có đầy đủ 4 đáp án');
        return;
      }
    }
    onNext();
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Câu hỏi</h2>
            <p className="text-sm text-gray-600 mt-1">
              {cards.length}/{limit} câu hỏi {userTier !== 'free' && `(Gói ${userTier})`}
            </p>
          </div>
          <button
            type="button"
            onClick={addCard}
            disabled={cards.length >= limit}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-500 text-white text-sm font-semibold hover:bg-sky-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Plus className="w-4 h-4" />
            Thêm câu hỏi
          </button>
        </div>

        <div className="space-y-4">
          {cards.map((card, idx) => {
            const isExpanded = expandedId === card.id;
            return (
              <div key={card.id} className="border border-gray-200 rounded-lg overflow-hidden">
                <button
                  type="button"
                  onClick={() => setExpandedId(isExpanded ? null : card.id)}
                  className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 text-left"
                >
                  <span className="font-semibold text-gray-900">
                    Câu {idx + 1}: {card.question.trim() || '(Chưa nhập câu hỏi)'}
                  </span>
                  {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
                </button>

                {isExpanded && (
                  <div className="p-4 sm:p-6 space-y-4 bg-white">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Câu hỏi *</label>
                      <textarea
                        value={card.question}
                        onChange={(e) => updateCard(card.id, { question: e.target.value })}
                        placeholder="Nhập câu hỏi..."
                        rows={2}
                        className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-sky-500 text-sm resize-none"
                      />
                    </div>

                    <div className="grid sm:grid-cols-2 gap-3">
                      {[1, 2, 3, 4].map((num) => (
                        <div key={num} className="flex items-start gap-2">
                          <input
                            type="radio"
                            name={`answer-${card.id}`}
                            checked={card.answer === num}
                            onChange={() => updateCard(card.id, { answer: num })}
                            className="mt-1 w-4 h-4 text-sky-500 focus:ring-sky-500"
                          />
                          <div className="flex-1">
                            <label className="block text-xs font-semibold text-gray-600 mb-1">
                              Đáp án {num} {card.answer === num && '(Đúng)'}
                            </label>
                            <input
                              type="text"
                              value={card[`option${num}` as 'option1' | 'option2' | 'option3' | 'option4']}
                              onChange={(e) => updateCard(card.id, { [`option${num}`]: e.target.value })}
                              placeholder={`Đáp án ${num}`}
                              className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-sky-500 text-sm"
                            />
                          </div>
                        </div>
                      ))}
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Gợi ý (tùy chọn)</label>
                      <input
                        type="text"
                        value={card.hint}
                        onChange={(e) => updateCard(card.id, { hint: e.target.value })}
                        placeholder="Gợi ý để giúp người chơi..."
                        className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-sky-500 text-sm"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Giải thích (tùy chọn)</label>
                      <textarea
                        value={card.explanation}
                        onChange={(e) => updateCard(card.id, { explanation: e.target.value })}
                        placeholder="Giải thích đáp án đúng..."
                        rows={2}
                        className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-sky-500 text-sm resize-none"
                      />
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Độ khó</label>
                        <select
                          value={card.difficulty}
                          onChange={(e) => updateCard(card.id, { difficulty: e.target.value as 'easy' | 'medium' | 'hard' })}
                          className="px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-sky-500 text-sm"
                        >
                          <option value="easy">Dễ</option>
                          <option value="medium">Trung bình</option>
                          <option value="hard">Khó</option>
                        </select>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeCard(card.id)}
                        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 text-sm font-semibold"
                      >
                        <Trash2 className="w-4 h-4" />
                        Xóa
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex items-center justify-between gap-4">
        <button
          type="button"
          onClick={onBack}
          className="px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 text-sm"
        >
          ← Quay lại
        </button>
        <button
          type="button"
          onClick={handleNext}
          className="px-6 py-2.5 rounded-lg bg-sky-500 text-white font-semibold hover:bg-sky-600 shadow-sm text-sm"
        >
          Tiếp theo →
        </button>
      </div>
    </div>
  );
}
