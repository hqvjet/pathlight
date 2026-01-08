import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export interface QuizCardData {
  id?: string;
  quiz_id?: string;  // Backend returns quiz_id
  title: string;
  overview?: string;  // Optional for backward compatibility
  description?: string;  // From recommendation API
  level: 'easy' | 'medium' | 'hard';
  duration: number; // minutes
  num_questions: number;
  previous_score?: number | null;
  finish: boolean;
  publish: boolean;
  created_at?: string;
  updated_at?: string;
  owner_id?: string;
  owner_name?: string; // Fullname of quiz creator
  recommendation_score?: number; // Similarity score from recommendation
}

interface QuizCardProps {
  quiz: QuizCardData;
  onSelect?: (quiz: QuizCardData) => void;
  viewMode?: 'grid' | 'list';
}

const levelLabels = {
  easy: { label: 'Dễ', color: 'bg-green-100 text-green-700 border-green-200' },
  medium: { label: 'Trung bình', color: 'bg-yellow-100 text-yellow-700 border-yellow-200' },
  hard: { label: 'Khó', color: 'bg-red-100 text-red-700 border-red-200' },
};

// Format relative time (e.g., "30 phút trước", "2 giờ trước")
function formatRelativeTime(dateString?: string): string {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  const diffMonths = Math.floor(diffDays / 30);
  const diffYears = Math.floor(diffDays / 365);

  if (diffSecs < 60) return 'Vừa xong';
  if (diffMins < 60) return `${diffMins} phút trước`;
  if (diffHours < 24) return `${diffHours} giờ trước`;
  if (diffDays < 30) return `${diffDays} ngày trước`;
  if (diffMonths < 12) return `${diffMonths} tháng trước`;
  return `${diffYears} năm trước`;
}

export function QuizCard({ quiz, onSelect, viewMode = 'grid' }: QuizCardProps) {
  const router = useRouter();
  const levelInfo = levelLabels[quiz.level] || levelLabels.easy;
  const quizId = quiz.id || quiz.quiz_id;
  const quizDescription = quiz.description || quiz.overview || '';
  const hasRecommendationScore = typeof quiz.recommendation_score === 'number' && quiz.recommendation_score > 0;

  const handleClick = () => {
    if (onSelect) {
      onSelect(quiz);
    } else {
      // Default behavior: navigate to quiz detail page
      router.push(`/user/my-quizzes/${quizId}`);
    }
  };

  if (viewMode === 'list') {
    return (
      <Card
        className="group hover:shadow-lg transition-all duration-200 cursor-pointer border-gray-200 hover:border-sky-400 bg-gradient-to-r from-white to-gray-50/30"
        onClick={handleClick}
      >
        <CardContent className="p-6">
          <div className="flex items-center gap-6">
            {/* Left: Title and meta */}
            <div className="flex-1 min-w-0 space-y-3">
              <div className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-bold text-gray-900 group-hover:text-sky-600 transition-colors truncate">
                      {quiz.title}
                    </h3>
                    <Badge className={`shrink-0 border ${levelInfo.color}`}>
                      {levelInfo.label}
                    </Badge>
                    {hasRecommendationScore && (
                      <Badge className="shrink-0 border-amber-200 text-amber-700 bg-amber-50">
                        <svg className="w-3 h-3 mr-1 inline" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                        {(quiz.recommendation_score * 100).toFixed(0)}% phù hợp
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 line-clamp-2">{quizDescription}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-6 text-sm text-gray-600">
                {quiz.owner_name && (
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-sky-400 to-blue-500 flex items-center justify-center">
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <span className="font-medium">{quiz.owner_name}</span>
                  </div>
                )}
                {quiz.created_at && (
                  <div className="flex items-center gap-2 text-gray-500">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{formatRelativeTime(quiz.created_at)}</span>
                  </div>
                )}
                {quiz.finish && (
                  <Badge className="border-green-200 text-green-700 bg-green-50">
                    <svg className="w-3 h-3 mr-1 inline" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    Hoàn thành
                  </Badge>
                )}
              </div>
            </div>
            
            {/* Right: Stats and actions */}
            <div className="flex items-center gap-5">
              <div className="flex items-center gap-4">
                <div className="text-center px-4 py-3 rounded-lg bg-sky-50 border border-sky-100">
                  <div className="text-2xl font-bold text-sky-700">{quiz.num_questions}</div>
                  <div className="text-xs text-sky-600 font-medium mt-1">câu hỏi</div>
                </div>
                <div className="text-center px-4 py-3 rounded-lg bg-purple-50 border border-purple-100">
                  <div className="text-2xl font-bold text-purple-700">{quiz.duration}</div>
                  <div className="text-xs text-purple-600 font-medium mt-1">phút</div>
                </div>
                {quiz.previous_score !== null && quiz.previous_score !== undefined && (
                  <div className={`text-center px-4 py-3 rounded-lg border ${
                    quiz.previous_score >= 70 
                      ? 'bg-green-50 border-green-200' 
                      : 'bg-amber-50 border-amber-200'
                  }`}>
                    <div className="flex items-center justify-center gap-1 mb-1">
                    </div>
                    <div className={`text-2xl font-bold ${
                      quiz.previous_score >= 70 ? 'text-green-700' : 'text-amber-700'
                    }`}>
                      {quiz.previous_score}
                    </div>
                    <div className={`text-xs font-medium mt-1 ${
                      quiz.previous_score >= 70 ? 'text-green-600' : 'text-amber-600'
                    }`}>
                      điểm cao
                    </div>
                  </div>
                )}
              </div>
              
              <Link
                href={`/user/my-quizzes/${quizId}`}
                onClick={(e) => e.stopPropagation()}
                className="px-6 py-3 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-600 hover:to-blue-700 text-white font-semibold shadow-lg shadow-sky-500/30 transition-all flex items-center gap-2"
              >
                Chi tiết
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Grid view (original design, improved)
  return (
    <Card
      className="group hover:shadow-xl transition-all duration-200 cursor-pointer border-gray-200 hover:border-sky-300 flex flex-col h-full"
      onClick={handleClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg font-bold text-gray-900 truncate group-hover:text-sky-600 transition-colors mb-2">
              {quiz.title}
            </CardTitle>
            <CardDescription className="text-sm text-gray-600 line-clamp-2">
              {quiz.overview}
            </CardDescription>
          </div>
          <Badge className={`shrink-0 border ${levelInfo.color}`}>
            {levelInfo.label}
          </Badge>
        </div>
        
        {/* Creator and Time Info */}
        {(quiz.owner_name || quiz.created_at) && (
          <div className="flex items-center gap-2 text-xs text-gray-500 pt-2 border-t border-gray-100">
            {quiz.owner_name && (
              <div className="flex items-center gap-1">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span>{quiz.owner_name}</span>
              </div>
            )}
            {quiz.owner_name && quiz.created_at && (
              <span>•</span>
            )}
            {quiz.created_at && (
              <span>{formatRelativeTime(quiz.created_at)}</span>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-3 flex flex-col flex-1">
        {/* Stats row */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-sky-50 rounded-lg p-3 border border-sky-100">
            <div className="text-xs text-gray-600 mb-1">Số câu hỏi</div>
            <div className="text-xl font-bold text-sky-700">{quiz.num_questions}</div>
          </div>
          <div className="bg-purple-50 rounded-lg p-3 border border-purple-100">
            <div className="text-xs text-gray-600 mb-1">Thời lượng</div>
            <div className="text-xl font-bold text-purple-700">{quiz.duration} phút</div>
          </div>
        </div>

        {/* High score */}
        {quiz.previous_score !== null && quiz.previous_score !== undefined && (
          <div className={`rounded-lg p-3 border ${
            quiz.previous_score >= 70 
              ? 'bg-green-50 border-green-200' 
              : 'bg-amber-50 border-amber-200'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-700">Điểm cao nhất</span>
              </div>
              <span className={`text-2xl font-bold ${
                quiz.previous_score >= 70 ? 'text-green-700' : 'text-amber-700'
              }`}>
                {quiz.previous_score}
              </span>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 mt-auto border-t border-gray-100">
          <div className="flex items-center gap-2">
            {quiz.finish && (
              <Badge variant="outline" className="border-green-200 text-green-700 bg-green-50 text-xs">
                Hoàn thành
              </Badge>
            )}
          </div>
          <Link
            href={`/user/my-quizzes/${quizId}`}
            onClick={(e) => e.stopPropagation()}
            className="text-sm font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1"
          >
            Chi tiết
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
