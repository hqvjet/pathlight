import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { User, Calendar, BookOpen, Clock } from 'lucide-react';

export interface CourseCardData {
  id: string;
  title: string;
  subtitle?: string;
  description: string;
  level?: string;
  durationLabel: string;
  language?: string;
  progress: number;
  completedLessons: number;
  totalLessons: number;
  badge?: string;
  color?: string;
  updatedAt?: string;
  ownerId?: string;
  ownerName?: string;
  isPublic?: boolean;
  recommendation_score?: number; // Similarity score from recommendation
}

interface CourseCardProps {
  course: CourseCardData;
  onSelect?: (course: CourseCardData) => void;
  onOwnerClick?: (ownerId: string) => void;
}

// Format time difference for course creation
function getTimeElapsed(dateStr?: string): string {
  if (!dateStr) return "Không rõ";
  
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return "Vừa tạo";
    if (diffMins < 60) return `${diffMins} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    if (diffDays < 7) return `${diffDays} ngày trước`;
    
    return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return "Không rõ";
  }
}

// Get user display name
function getUserDisplayName(ownerId?: string, ownerName?: string): string {
  if (ownerName) return ownerName;
  if (!ownerId) return "Không rõ";
  
  // Extract email prefix if it's an email-like ID
  if (ownerId.includes('@')) {
    return ownerId.split('@')[0];
  }
  // For UUID format, show first 8 chars
  return ownerId.substring(0, 8) + "...";
}

export function CourseCard({ course, onSelect, onOwnerClick }: CourseCardProps) {
  const timeElapsed = getTimeElapsed(course.updatedAt);
  const creatorName = getUserDisplayName(course.ownerId, course.ownerName);
  const hasRecommendationScore = typeof course.recommendation_score === 'number' && course.recommendation_score > 0;
  
  return (
    <Card
      className="group h-full border-gray-200 shadow-sm hover:shadow-xl transition-all duration-300 bg-white cursor-pointer hover:border-orange-300"
      role={onSelect ? 'button' : undefined}
      tabIndex={onSelect ? 0 : undefined}
      onClick={() => onSelect?.(course)}
      onKeyDown={(e) => { if (onSelect && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onSelect(course); } }}
    >
      <CardHeader className="pb-3 p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row items-start justify-between mb-3 gap-2">
          <div className="flex-1 w-full">
            <CardTitle className="text-lg sm:text-xl font-bold text-gray-900 group-hover:text-orange-600 transition-colors leading-tight mb-1 line-clamp-1">
              {course.title}
            </CardTitle>
            {course.subtitle && (
              <p className="text-xs sm:text-sm text-gray-600 font-medium">{course.subtitle}</p>
            )}
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto justify-between sm:justify-end">
            <div className="text-left sm:text-right">
              <div className="text-2xl sm:text-3xl font-bold text-orange-600">{course.progress}%</div>
              <div className="text-xs text-gray-500 mt-0.5">hoàn thành</div>
            </div>
            {hasRecommendationScore && (
              <Badge className="shrink-0 text-xs border-amber-200 text-amber-700 bg-amber-50">
                <svg className="w-3 h-3 mr-1 inline" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                {(course.recommendation_score * 100).toFixed(0)}%
              </Badge>
            )}
          </div>
        </div>
        
        {/* Meta Information */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs text-gray-600 pb-3 border-b border-gray-100">
          <div className="flex items-center gap-1.5" title="Người tạo">
            <User className="w-3.5 h-3.5 text-blue-500" />
            {course.isPublic && course.ownerId && onOwnerClick ? (
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onOwnerClick(course.ownerId); }}
                className="text-blue-600 hover:text-blue-700 font-medium hover:underline"
              >
                {creatorName}
              </button>
            ) : (
              <span className="font-medium">{creatorName}</span>
            )}
          </div>
          <div className="flex items-center gap-1.5" title="Ngày tạo">
            <Calendar className="w-3.5 h-3.5 text-gray-500" />
            <span>{timeElapsed}</span>
          </div>
          <div className="flex items-center gap-1.5 ml-auto">
            <BookOpen className="w-3.5 h-3.5 text-orange-500" />
            <span className="font-medium text-orange-600">
              {course.completedLessons}/{course.totalLessons} bài
            </span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3 sm:space-y-4 p-4 sm:p-6">
        {/* Description */}
        <p className="text-xs sm:text-sm text-gray-700 leading-relaxed line-clamp-2 min-h-[2.5rem]">
          {course.description}
        </p>
        
        {/* Progress Bar */}
        <div className="space-y-2">
          <Progress 
            value={course.progress} 
            className="h-2.5" 
            color={course.progress === 100 ? 'orange' : 'green'}
          />
          <div className="flex justify-between items-center text-xs text-gray-600">
            <span className="font-medium">
              {course.completedLessons < course.totalLessons 
                ? `Tiếp tục từ bài ${course.completedLessons + 1}` 
                : 'Đã hoàn thành tất cả bài học'}
            </span>
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{course.durationLabel}</span>
            </div>
          </div>
        </div>
        
        {/* Badges */}
        <div className="flex flex-wrap items-center gap-2">
          {course.badge && (
            <Badge 
              className="text-xs font-semibold"
              style={course.color ? { backgroundColor: course.color, color: '#fff', borderColor: 'transparent' } : undefined}
            >
              {course.badge}
            </Badge>
          )}
          {course.level && (
            <Badge variant="outline" className="text-xs border-gray-300 text-gray-700 bg-gray-50">
              {course.level}
            </Badge>
          )}
          {course.language && (
            <Badge variant="outline" className="text-xs border-gray-300 text-gray-700">
              {course.language}
            </Badge>
          )}
          {course.isPublic && (
            <Badge variant="outline" className="text-xs border-emerald-300 bg-emerald-50 text-emerald-700 font-semibold">
              Public
            </Badge>
          )}
        </div>
        
        {/* Action */}
        <div className="pt-2">
          <Link
            href={`/user/my-courses/${course.id}`}
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center text-sm font-semibold text-orange-600 hover:text-orange-700 group-hover:underline"
          >
            Xem chi tiết
            <span className="ml-1 group-hover:translate-x-1 transition-transform">→</span>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
