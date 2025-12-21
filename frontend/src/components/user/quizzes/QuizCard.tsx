import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export interface QuizCardData {
  id: string;
  title: string;
  overview: string;
  level: 'easy' | 'medium' | 'hard';
  duration: number; // minutes
  num_questions: number;
  previous_score?: number | null;
  finish: boolean;
  publish: boolean;
  created_at?: string;
  updated_at?: string;
}

interface QuizCardProps {
  quiz: QuizCardData;
  onSelect?: (quiz: QuizCardData) => void;
}

const levelLabels = {
  easy: { label: 'Dễ', color: 'bg-green-100 text-green-700' },
  medium: { label: 'Trung bình', color: 'bg-yellow-100 text-yellow-700' },
  hard: { label: 'Khó', color: 'bg-red-100 text-red-700' },
};

export function QuizCard({ quiz, onSelect }: QuizCardProps) {
  const levelInfo = levelLabels[quiz.level] || levelLabels.easy;

  const handleClick = () => {
    onSelect?.(quiz);
  };

  return (
    <Card
      className="group hover:shadow-lg transition-all duration-200 cursor-pointer border-gray-100 hover:border-sky-200 flex flex-col h-full"
      onClick={handleClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg text-gray-900 line-clamp-2 group-hover:text-sky-600 transition-colors">
              {quiz.title}
            </CardTitle>
            <CardDescription className="text-sm text-gray-600 mt-1 line-clamp-1">
              {quiz.overview}
            </CardDescription>
          </div>
          <Badge className={`shrink-0 ${levelInfo.color} border-none`}>
            {levelInfo.label}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 flex flex-col flex-1">
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1.5">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{quiz.num_questions} câu</span>
          </div>
          <div className="flex items-center gap-1.5">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{quiz.duration} phút</span>
          </div>
        </div>

        {quiz.previous_score !== null && quiz.previous_score !== undefined && (
          <div className="pt-2 border-t border-gray-100">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Điểm cao nhất:</span>
              <span className={`font-semibold ${quiz.previous_score >= 70 ? 'text-green-600' : 'text-orange-600'}`}>
                {quiz.previous_score}%
              </span>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between pt-2 mt-auto border-t border-gray-100">
          <div className="flex items-center gap-2">
            {quiz.finish && (
              <Badge variant="outline" className="border-green-200 text-green-700 bg-green-50 text-xs">
                Hoàn thành
              </Badge>
            )}
            {!quiz.publish && (
              <Badge variant="outline" className="border-gray-300 text-gray-600 text-xs">
                Nháp
              </Badge>
            )}
          </div>
          <Link
            href={`/user/my-quizzes/${quiz.id}`}
            onClick={(e) => e.stopPropagation()}
            className="text-sm font-semibold text-sky-600 hover:text-sky-700"
          >
            Chi tiết →
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
