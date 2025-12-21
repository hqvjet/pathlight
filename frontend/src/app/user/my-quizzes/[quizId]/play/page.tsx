'use client';

import { use, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { quizApi } from '@/lib/api/quiz';
import { showToast } from '@/utils/toast';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Lightbulb, RotateCcw, CheckCircle2 } from 'lucide-react';

interface QuizCard {
  card_id: string;
  question: string;
  hint: string | null;
  explanation: string | null;
  difficulty: string;
  option1: string;
  option2: string;
  option3: string;
  option4: string;
  answer?: number; // Only available after quiz is completed
}

interface QuizDetail {
  quiz_id: string;
  title: string;
  overview: string;
  level: string;
  duration: number;
  num_questions: number;
  previous_score: number | null;
  finish: boolean;
  publish: boolean;
  cards: QuizCard[];
}

interface QuizSubmitResponse {
  status: number;
  message?: string;
  score?: number;
  total_questions?: number;
  correct_answers?: number;
  experience?: {
    gained_exp?: number;
    total_exp?: number;
    level?: number;
    rank?: string;
  };
  details?: Array<{
    card_id: string;
    selected_answer: number;
    correct_answer: number;
    is_correct: boolean;
    gained_exp: number;
  }>;
}

type PageProps = { params: Promise<{ quizId: string }> };

export default function QuizPlayPage({ params }: PageProps) {
  const { quizId } = use(params);
  const router = useRouter();
  const [quiz, setQuiz] = useState<QuizDetail | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [flipped, setFlipped] = useState(false);
  const [showHint, setShowHint] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<QuizSubmitResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!quizId) return;
      setLoading(true);
      setError(null);
      try {
        // Call start quiz endpoint
        await quizApi.start(quizId);
        
        // Get quiz details with hints and explanations hidden initially
        const resp = await quizApi.getById(quizId, { include_hints: false, include_explanations: false });
        if (cancelled) return;

        const data = resp?.data as QuizDetail;
        if (!data || !data.cards || data.cards.length === 0) {
          throw new Error('Quiz không có câu hỏi');
        }

        setQuiz(data);
      } catch (e: unknown) {
        if (!cancelled) {
          const msg = e instanceof Error ? e.message : 'Không thể tải quiz';
          setError(msg);
          showToast.error(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [quizId]);

  const currentCard = quiz?.cards[currentIndex];
  const answeredCount = Object.keys(answers).length;
  const progress = quiz ? (answeredCount / quiz.cards.length) * 100 : 0;

  const handleAnswer = (option: number) => {
    if (!currentCard || submitted) return;
    setAnswers((prev) => ({ ...prev, [currentCard.card_id]: option }));
    setFlipped(true);
  };

  const handleNext = () => {
    if (!quiz || currentIndex >= quiz.cards.length - 1) return;
    setCurrentIndex((i) => i + 1);
    setFlipped(false);
    setShowHint(false);
    setShowExplanation(false);
  };

  const handlePrev = () => {
    if (currentIndex <= 0) return;
    setCurrentIndex((i) => i - 1);
    setFlipped(false);
    setShowHint(false);
    setShowExplanation(false);
  };

  const handleSubmit = async () => {
    if (!quiz || submitting) return;
    if (answeredCount < quiz.cards.length) {
      showToast.info(`Vui lòng trả lời hết ${quiz.cards.length} câu hỏi`);
      return;
    }

    setSubmitting(true);
    try {
      const payload = quiz.cards.map((card) => ({
        card_id: card.card_id,
        answer: answers[card.card_id] || 1,
      }));

      const resp = await quizApi.submit(quizId, payload);
      const data = resp?.data as QuizSubmitResponse;
      setResult(data);
      setSubmitted(true);
      
      if (data.score !== undefined && data.score >= 70) {
        showToast.success(`Chúc mừng! Bạn đạt ${data.score}% và nhận được ${data.experience?.gained_exp || 0} EXP`);
      } else {
        showToast.info(`Bạn đạt ${data.score || 0}%. Hãy thử lại để cải thiện!`);
      }
    } catch (e: unknown) {
      showToast.error(e instanceof Error ? e.message : 'Không thể nộp bài');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetry = () => {
    setAnswers({});
    setCurrentIndex(0);
    setFlipped(false);
    setShowHint(false);
    setShowExplanation(false);
    setSubmitted(false);
    setResult(null);
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-white rounded-xl p-10 text-center border border-gray-100 shadow-sm">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-sky-500 mx-auto" />
          <p className="mt-4 text-gray-600">Đang tải quiz...</p>
        </div>
      </div>
    );
  }

  if (error || !quiz || !currentCard) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-red-50 text-red-700 rounded-xl p-4 border border-red-200 text-sm">
          {error || 'Không tìm thấy quiz'}
        </div>
        <Link href="/user/my-quizzes" className="inline-block mt-4 text-sky-600 font-semibold hover:text-sky-700">
          ← Quay lại danh sách
        </Link>
      </div>
    );
  }

  if (submitted && result) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <Card className="shadow-lg border-gray-200">
          <CardContent className="p-8 sm:p-12 text-center space-y-6">
            <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto" />
            <div>
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">Hoàn thành Quiz!</h2>
              <p className="text-gray-600">Kết quả của bạn</p>
            </div>

            <div className="grid sm:grid-cols-3 gap-4 py-6">
              <div className="bg-sky-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Điểm số</p>
                <p className="text-3xl font-bold text-sky-600">{result.score || 0}%</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Đúng</p>
                <p className="text-3xl font-bold text-green-600">
                  {result.correct_answers}/{result.total_questions}
                </p>
              </div>
              <div className="bg-orange-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">EXP nhận</p>
                <p className="text-3xl font-bold text-orange-600">+{result.experience?.gained_exp || 0}</p>
              </div>
            </div>

            {result.experience && (
              <div className="bg-gradient-to-r from-orange-50 to-sky-50 rounded-lg p-4 text-sm">
                <p className="text-gray-700">
                  Cấp độ: <span className="font-semibold">Level {result.experience.level}</span> • 
                  Tổng EXP: <span className="font-semibold">{result.experience.total_exp}</span> • 
                  Hạng: <span className="font-semibold">{result.experience.rank}</span>
                </p>
              </div>
            )}

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-6">
              <button
                onClick={handleRetry}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg border border-sky-500 text-sky-600 font-semibold hover:bg-sky-50"
              >
                <RotateCcw className="w-4 h-4" />
                Làm lại
              </button>
              <Link
                href={`/user/my-quizzes/${quizId}`}
                className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-lg bg-sky-500 text-white font-semibold hover:bg-sky-600 shadow-sm"
              >
                Xem chi tiết
              </Link>
              <Link
                href="/user/my-quizzes"
                className="w-full sm:w-auto px-6 py-3 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 text-center"
              >
                Danh sách quiz
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isAnswered = !!answers[currentCard.card_id];

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 to-white py-6 sm:py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Link href={`/user/my-quizzes/${quizId}`} className="text-sm text-gray-600 hover:text-gray-900 font-medium">
            ← Thoát
          </Link>
          <div className="flex items-center gap-3">
            <Badge className="bg-sky-100 text-sky-700 border-none">
              {currentIndex + 1} / {quiz.cards.length}
            </Badge>
            <span className="text-sm text-gray-600">
              {Math.round(progress)}% hoàn thành
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-sky-500 to-cyan-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Flashcard */}
        <Card className="shadow-xl border-gray-200">
          <CardContent className="p-6 sm:p-10 space-y-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 leading-tight">
                  {currentCard.question}
                </h2>
              </div>
              <Badge className={`shrink-0 ${
                currentCard.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                currentCard.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                'bg-red-100 text-red-700'
              } border-none`}>
                {currentCard.difficulty === 'easy' ? 'Dễ' : currentCard.difficulty === 'medium' ? 'TB' : 'Khó'}
              </Badge>
            </div>

            {/* Options */}
            <div className="grid sm:grid-cols-2 gap-3">
              {[1, 2, 3, 4].map((num) => {
                const option = currentCard[`option${num}` as 'option1' | 'option2' | 'option3' | 'option4'];
                const isSelected = answers[currentCard.card_id] === num;
                
                return (
                  <button
                    key={num}
                    onClick={() => handleAnswer(num)}
                    disabled={submitted}
                    className={`px-4 py-4 rounded-lg border-2 text-left font-medium transition-all ${
                      isSelected
                        ? 'border-sky-500 bg-sky-50 text-sky-900'
                        : 'border-gray-200 bg-white hover:border-sky-300 hover:bg-sky-50/50 text-gray-700'
                    } ${submitted ? 'cursor-not-allowed opacity-75' : 'cursor-pointer'}`}
                  >
                    <span className="flex items-center gap-3">
                      <span className={`flex items-center justify-center w-6 h-6 rounded-full text-sm font-bold ${
                        isSelected ? 'bg-sky-500 text-white' : 'bg-gray-200 text-gray-600'
                      }`}>
                        {num}
                      </span>
                      <span className="flex-1">{option}</span>
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Hint & Explanation */}
            {isAnswered && (
              <div className="space-y-3 pt-4 border-t border-gray-200">
                {currentCard.hint && (
                  <div>
                    <button
                      onClick={() => setShowHint(!showHint)}
                      className="inline-flex items-center gap-2 text-sm font-semibold text-orange-600 hover:text-orange-700"
                    >
                      <Lightbulb className="w-4 h-4" />
                      {showHint ? 'Ẩn gợi ý' : 'Xem gợi ý'}
                    </button>
                    {showHint && (
                      <div className="mt-2 p-3 bg-orange-50 rounded-lg border border-orange-200 text-sm text-orange-800">
                        {currentCard.hint}
                      </div>
                    )}
                  </div>
                )}
                
                {currentCard.explanation && (
                  <div>
                    <button
                      onClick={() => setShowExplanation(!showExplanation)}
                      className="inline-flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                      {showExplanation ? 'Ẩn giải thích' : 'Xem giải thích'}
                    </button>
                    {showExplanation && (
                      <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-200 text-sm text-blue-800 leading-relaxed">
                        {currentCard.explanation}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex items-center justify-between gap-4">
          <button
            onClick={handlePrev}
            disabled={currentIndex === 0}
            className="px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            ← Trước
          </button>

          <div className="flex items-center gap-3">
            {currentIndex < quiz.cards.length - 1 ? (
              <button
                onClick={handleNext}
                disabled={!isAnswered}
                className="px-6 py-2.5 rounded-lg bg-sky-500 text-white font-semibold hover:bg-sky-600 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm text-sm"
              >
                Tiếp →
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={answeredCount < quiz.cards.length || submitting}
                className="px-6 py-2.5 rounded-lg bg-green-500 text-white font-semibold hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm text-sm inline-flex items-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                    Đang nộp...
                  </>
                ) : (
                  <>Nộp bài ({answeredCount}/{quiz.cards.length})</>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
