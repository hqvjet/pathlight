"use client";
import Link from 'next/link';
import { CheckCircle2, TrendingUp } from 'lucide-react';

interface SuccessStepProps {
  quizId: string;
  quizTitle?: string;
  isAI?: boolean;
}

export function SuccessStep({ quizId, quizTitle, isAI = false }: SuccessStepProps) {
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-12 text-center">
      <div className="bg-white rounded-xl p-8 sm:p-12 shadow-sm border border-gray-100 space-y-6">
        <div className="flex justify-center">
          <CheckCircle2 className={`w-16 h-16 ${isAI ? 'text-green-500' : 'text-orange-500'}`} />
        </div>
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
            {isAI ? 'Đã gửi yêu cầu tạo Quiz!' : 'Tạo quiz thành công!'}
          </h2>
          <p className="text-gray-600">
            {isAI ? (
              <>
                AI đang xử lý yêu cầu của bạn. Quá trình tạo quiz có thể mất vài phút.
                <br />
                Bạn có thể theo dõi tiến trình ở trang{' '}
                <Link href="/user/quiz-tracking" className="text-green-600 font-semibold hover:underline">
                  Theo dõi tiến trình
                </Link>
              </>
            ) : quizTitle ? (
              <>
                Quiz <span className="font-semibold text-gray-900">&quot;{quizTitle}&quot;</span> đã được tạo
              </>
            ) : (
              'Quiz của bạn đã được tạo thành công'
            )}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-6">
          {isAI ? (
            <>
              <Link
                href="/user/quiz-tracking"
                className="w-full sm:w-auto px-6 py-3 rounded-lg bg-green-500 text-white font-semibold hover:bg-green-600 shadow-sm text-center inline-flex items-center justify-center gap-2"
              >
                <TrendingUp className="w-4 h-4" />
                Xem tiến trình
              </Link>
              <Link
                href="/user/my-quizzes"
                className="w-full sm:w-auto px-6 py-3 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 text-center"
              >
                Quay về danh sách
              </Link>
            </>
          ) : (
            <>
              <Link
                href={`/user/my-quizzes/${quizId}`}
                className="w-full sm:w-auto px-6 py-3 rounded-lg bg-orange-500 text-white font-semibold hover:bg-orange-600 shadow-sm text-center"
              >
                Xem quiz
              </Link>
              <Link
                href="/user/my-quizzes"
                className="w-full sm:w-auto px-6 py-3 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 text-center"
              >
                Quay về danh sách
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
