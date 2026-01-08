'use client';

import { use, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { quizApi } from '@/lib/api/quiz';
import { showToast } from '@/utils/toast';
import { Badge } from '@/components/ui/badge';
import { PlayCircle, Eye, EyeOff, Trash2, Clock, Award, Target } from 'lucide-react';
import QuizSettingsModal, { AnswerDisplayMode } from '@/components/user/quizzes/QuizSettingsModal';

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
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!quizId) return;
      setLoading(true);
      setError(null);
      try {
        const resp = await quizApi.getById(quizId, { include_hints: true, include_explanations: true });
        if (cancelled) return;

        // Backend returns { status, quiz: { quiz_id, ..., cards: [...] } }
        const responseData = resp?.data as { status?: number; quiz?: QuizDetail };
        const data = responseData?.quiz;
        
        if (!data || !data.cards) {
          throw new Error('Quiz không tồn tại hoặc chưa có câu hỏi');
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
    setShowSettings(true);
  };

  const handleStartQuiz = (mode: AnswerDisplayMode) => {
    router.push(`/user/my-quizzes/${quizId}/play?mode=${mode}`);
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
    easy: { label: 'Dễ', color: 'bg-emerald-100 text-emerald-800 border-emerald-200', icon: '😊' },
    medium: { label: 'Trung bình', color: 'bg-amber-100 text-amber-800 border-amber-200', icon: '🤔' },
    hard: { label: 'Khó', color: 'bg-rose-100 text-rose-800 border-rose-200', icon: '😰' },
  };

  const levelInfo = levelLabels[quiz.level as keyof typeof levelLabels] || levelLabels.easy;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Breadcrumb */}
        <Link href="/user/my-quizzes" className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-sky-600 font-medium mb-4 transition">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Quay lại danh sách
        </Link>

        {/* Main Card - More Compact */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {/* Compact Header */}
          <div className="bg-gradient-to-r from-sky-500 to-blue-600 px-6 py-5 relative">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h1 className="text-2xl font-bold text-white mb-1 line-clamp-2">{quiz.title}</h1>
                <p className="text-sky-100 text-sm line-clamp-1">{quiz.overview}</p>
              </div>
              <Badge className={`${levelInfo.color} border shrink-0 text-sm px-3 py-1`}>
                {levelInfo.icon} {levelInfo.label}
              </Badge>
            </div>
          </div>

          {/* Compact Stats - Single Row */}
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 bg-sky-100 rounded-lg">
                  <Target className="w-4 h-4 text-sky-600" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-gray-500">Số câu</p>
                  <p className="text-lg font-bold text-gray-900">{quiz.num_questions}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 bg-orange-100 rounded-lg">
                  <Clock className="w-4 h-4 text-orange-600" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-gray-500">Thời lượng</p>
                  <p className="text-lg font-bold text-gray-900">{quiz.duration} <span className="text-xs font-normal">phút</span></p>
                </div>
              </div>
              
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 bg-emerald-100 rounded-lg">
                  <Award className="w-4 h-4 text-emerald-600" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-gray-500">Điểm cao</p>
                  <p className={`text-lg font-bold ${
                    quiz.previous_score !== null && quiz.previous_score !== undefined
                      ? quiz.previous_score >= 70 ? 'text-emerald-600' : 'text-orange-600'
                      : 'text-gray-400'
                  }`}>
                    {quiz.previous_score !== null && quiz.previous_score !== undefined ? `${quiz.previous_score}%` : '--'}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 bg-gray-100 rounded-lg">
                  {quiz.publish ? <Eye className="w-4 h-4 text-gray-600" /> : <EyeOff className="w-4 h-4 text-gray-600" />}
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-gray-500">Trạng thái</p>
                  <p className="text-sm font-semibold text-gray-900">
                    {quiz.publish ? 'Công khai' : 'Riêng tư'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Compact Action Buttons */}
          <div className="px-6 py-4 bg-white flex flex-wrap items-center gap-2.5">
            <button
              onClick={handlePlay}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 text-white font-semibold hover:from-sky-600 hover:to-blue-700 shadow-md hover:shadow-lg transition-all text-sm"
            >
              <PlayCircle className="w-4 h-4" />
              Bắt đầu làm quiz
            </button>
            <button
              onClick={handleToggleVisibility}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 hover:border-gray-400 transition-all text-sm"
            >
              {quiz.publish ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              {quiz.publish ? 'Riêng tư' : 'Công khai'}
            </button>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-rose-300 text-rose-600 font-medium hover:bg-rose-50 hover:border-rose-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
            >
              <Trash2 className="w-4 h-4" />
              Xóa quiz
            </button>
          </div>
        </div>

        {/* Additional Info Cards */}
        <div className="grid sm:grid-cols-2 gap-4 mt-4">
          {/* Quick Stats */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4 text-sky-600" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Thống kê nhanh
            </h3>
            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Điểm trung bình mỗi câu</span>
                <span className="font-semibold text-gray-900">
                  {quiz.previous_score ? Math.round(quiz.previous_score / quiz.num_questions) : 0} điểm
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Thời gian/câu</span>
                <span className="font-semibold text-gray-900">
                  {Math.round((quiz.duration * 60) / quiz.num_questions)} giây
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Tình trạng</span>
                <span className={`font-semibold ${quiz.finish ? 'text-emerald-600' : 'text-gray-400'}`}>
                  {quiz.finish ? 'Đã hoàn thành' : 'Chưa hoàn thành'}
                </span>
              </div>
            </div>
          </div>

          {/* Tips */}
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg border border-amber-200 p-5">
            <h3 className="text-sm font-semibold text-amber-900 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              Mẹo làm bài
            </h3>
            <ul className="space-y-2 text-sm text-amber-900">
              <li className="flex items-start gap-2">
                <span className="text-amber-500 mt-0.5">•</span>
                <span>Đọc kỹ câu hỏi trước khi chọn đáp án</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-500 mt-0.5">•</span>
                <span>Sử dụng items hỗ trợ khi gặp khó khăn</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-500 mt-0.5">•</span>
                <span>Điểm số cao hơn khi trả lời nhanh</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Quiz Settings Modal */}
      <QuizSettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        onStart={handleStartQuiz}
        quizTitle={quiz.title}
      />
    </div>
  );
}
