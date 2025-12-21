'use client';

import { use, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { quizApi } from '@/lib/api/quiz';
import { showToast } from '@/utils/toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PlayCircle, Eye, EyeOff, Trash2 } from 'lucide-react';

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
  answer?: number;
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
  created_at?: string;
  updated_at?: string;
}

type PageProps = { params: Promise<{ quizId: string }> };

export default function QuizDetailPage({ params }: PageProps) {
  const { quizId } = use(params);
  const router = useRouter();
  const [quiz, setQuiz] = useState<QuizDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!quizId) return;
      setLoading(true);
      setError(null);
      try {
        const resp = await quizApi.getById(quizId, { include_hints: true, include_explanations: true });
        if (cancelled) return;

        const data = resp?.data as QuizDetail;
        if (!data) {
          throw new Error('Quiz không tồn tại');
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

  const handlePlay = () => {
    router.push(`/user/my-quizzes/${quizId}/play`);
  };

  const handleToggleVisibility = async () => {
    if (!quiz) return;
    try {
      await quizApi.updateVisibility(quizId, !quiz.publish);
      setQuiz({ ...quiz, publish: !quiz.publish });
      showToast.success(quiz.publish ? 'Đã chuyển sang riêng tư' : 'Đã công khai quiz');
    } catch (e: unknown) {
      showToast.error(e instanceof Error ? e.message : 'Không thể cập nhật');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Bạn có chắc muốn xóa quiz này?')) return;
    setDeleting(true);
    try {
      await quizApi.delete(quizId);
      showToast.success('Đã xóa quiz');
      router.push('/user/my-quizzes');
    } catch (e: unknown) {
      showToast.error(e instanceof Error ? e.message : 'Không thể xóa quiz');
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-white rounded-xl p-10 text-center border border-gray-100 shadow-sm">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-sky-500 mx-auto" />
          <p className="mt-4 text-gray-600">Đang tải quiz...</p>
        </div>
      </div>
    );
  }

  if (error || !quiz) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-red-50 text-red-700 rounded-xl p-4 border border-red-200 text-sm">
          {error || 'Không tìm thấy quiz'}
        </div>
        <Link href="/user/my-quizzes" className="inline-block mt-4 text-sky-600 font-semibold hover:text-sky-700">
          ← Quay lại danh sách
        </Link>
      </div>
    );
  }

  const levelLabels = {
    easy: { label: 'Dễ', color: 'bg-green-100 text-green-700' },
    medium: { label: 'Trung bình', color: 'bg-yellow-100 text-yellow-700' },
    hard: { label: 'Khó', color: 'bg-red-100 text-red-700' },
  };

  const levelInfo = levelLabels[quiz.level as keyof typeof levelLabels] || levelLabels.easy;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-3 text-sm text-gray-600">
        <Link href="/user/my-quizzes" className="text-sky-600 font-semibold hover:text-sky-700">
          ← Quay lại danh sách
        </Link>
        <span className="text-gray-400">/</span>
        <span className="font-semibold text-gray-800">{quiz.title}</span>
      </div>

      {/* Hero */}
      <Card className="shadow-lg border-gray-200">
        <CardHeader>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex-1">
              <CardTitle className="text-2xl sm:text-3xl text-gray-900 mb-2">{quiz.title}</CardTitle>
              <p className="text-gray-600 leading-relaxed">{quiz.overview}</p>
            </div>
            <Badge className={`${levelInfo.color} border-none shrink-0 text-sm px-3 py-1`}>
              {levelInfo.label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid sm:grid-cols-4 gap-4 text-sm">
            <div className="bg-sky-50 rounded-lg p-3">
              <p className="text-gray-600 mb-1">Số câu hỏi</p>
              <p className="text-xl font-bold text-sky-600">{quiz.num_questions}</p>
            </div>
            <div className="bg-orange-50 rounded-lg p-3">
              <p className="text-gray-600 mb-1">Thời lượng</p>
              <p className="text-xl font-bold text-orange-600">{quiz.duration} phút</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <p className="text-gray-600 mb-1">Điểm cao nhất</p>
              <p className={`text-xl font-bold ${
                quiz.previous_score !== null && quiz.previous_score !== undefined
                  ? quiz.previous_score >= 70 ? 'text-green-600' : 'text-orange-600'
                  : 'text-gray-400'
              }`}>
                {quiz.previous_score !== null && quiz.previous_score !== undefined ? `${quiz.previous_score}%` : '--'}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-gray-600 mb-1">Trạng thái</p>
              <div className="flex flex-wrap gap-1.5">
                {quiz.finish && (
                  <Badge variant="outline" className="border-green-200 text-green-700 bg-green-50 text-xs">
                    Hoàn thành
                  </Badge>
                )}
                {quiz.publish ? (
                  <Badge variant="outline" className="border-blue-200 text-blue-700 bg-blue-50 text-xs">
                    Công khai
                  </Badge>
                ) : (
                  <Badge variant="outline" className="border-gray-300 text-gray-600 text-xs">
                    Riêng tư
                  </Badge>
                )}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-4 border-t">
            <button
              onClick={handlePlay}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-sky-500 text-white font-semibold hover:bg-sky-600 shadow-sm"
            >
              <PlayCircle className="w-5 h-5" />
              Bắt đầu làm quiz
            </button>
            <button
              onClick={handleToggleVisibility}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50"
            >
              {quiz.publish ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              {quiz.publish ? 'Đặt riêng tư' : 'Công khai'}
            </button>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-red-200 text-red-600 font-semibold hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Trash2 className="w-4 h-4" />
              {deleting ? 'Đang xóa...' : 'Xóa quiz'}
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Quiz Cards List */}
      <Card className="shadow-sm border-gray-200">
        <CardHeader>
          <CardTitle className="text-lg text-gray-900">Danh sách câu hỏi</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {quiz.cards.map((card, idx) => (
              <div key={card.card_id} className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <p className="text-sm font-semibold text-gray-900 flex-1">
                    Câu {idx + 1}: {card.question}
                  </p>
                  <Badge className={`shrink-0 ${
                    card.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                    card.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  } border-none text-xs`}>
                    {card.difficulty === 'easy' ? 'Dễ' : card.difficulty === 'medium' ? 'TB' : 'Khó'}
                  </Badge>
                </div>
                <div className="space-y-1 text-xs text-gray-600">
                  {[1, 2, 3, 4].map((num) => {
                    const option = card[`option${num}` as 'option1' | 'option2' | 'option3' | 'option4'];
                    const isCorrect = card.answer === num;
                    return (
                      <p key={num} className={isCorrect ? 'font-semibold text-green-600' : ''}>
                        {num}. {option} {isCorrect && '✓'}
                      </p>
                    );
                  })}
                </div>
                {(card.hint || card.explanation) && (
                  <div className="mt-2 pt-2 border-t border-gray-300 text-xs text-gray-500">
                    {card.hint && <p>💡 Gợi ý: {card.hint}</p>}
                    {card.explanation && <p className="mt-1">📖 Giải thích: {card.explanation}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
