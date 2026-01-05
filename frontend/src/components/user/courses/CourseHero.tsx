import { ReactNode } from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Calendar } from 'lucide-react';

export interface CourseHeroData {
  id?: string;
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
  ownerId?: string;
  ownerName?: string;
  isPublic?: boolean;
  createdAt?: string;
  updatedAt?: string;
  lastAccessed?: string;
}

interface CourseHeroProps {
  course: CourseHeroData;
  actions?: ReactNode;
}

// Format date to Vietnamese format
function formatDate(dateStr?: string): string {
  if (!dateStr) return 'Không rõ';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('vi-VN', { 
      day: '2-digit', 
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return 'Không rõ';
  }
}

export function CourseHero({ course, actions }: CourseHeroProps) {
  return (
    <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-orange-50 via-white to-blue-50 border border-orange-100 shadow-sm">
      <div className="absolute inset-y-0 right-0 w-1/3 bg-gradient-to-l from-orange-100/60 to-transparent" aria-hidden />
      <div className="p-6 sm:p-8 relative z-10 grid gap-6 lg:grid-cols-[2fr,1fr] items-start">
        <div className="space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            {course.badge && <Badge className="bg-orange-500 text-white border-none">{course.badge}</Badge>}
            <span className="text-xs font-semibold uppercase tracking-wide text-orange-700">{course.level}</span>
            <span className="text-xs text-gray-500">{course.language}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight">{course.title}</h1>
          <p className="text-base text-gray-700 max-w-3xl leading-7 line-clamp-2 sm:line-clamp-3">{course.description}</p>
          <div className="flex flex-wrap gap-4 text-sm text-gray-600">
            <span className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-white shadow-sm border border-gray-100">
              <span className="h-2 w-2 rounded-full bg-green-500" />
              {course.completedLessons}/{course.totalLessons} bài • {course.progress}%
            </span>
            <span className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-white shadow-sm border border-gray-100">
              <span className="h-2 w-2 rounded-full bg-orange-500" />
              Lộ trình {course.durationLabel}
            </span>
            {course.isPublic && (
              <span className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 font-semibold">
                Public
              </span>
            )}
            {(course.ownerName || course.ownerId) && (
              <span className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-50 border border-blue-200 text-blue-700">
                👤 {course.ownerName || (course.ownerId?.includes('@') ? course.ownerId.split('@')[0] : course.ownerId?.substring(0, 8) + '...')}
              </span>
            )}
          </div>
          
          {/* Additional info section - moved to left column */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <div className="flex items-start gap-2 text-xs bg-white rounded-lg border border-gray-100 p-3">
              <Calendar className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
              <div className="flex-1">
                <div className="text-gray-500 mb-0.5">Ngày tạo</div>
                <div className="font-medium text-gray-700">{formatDate(course.createdAt)}</div>
              </div>
            </div>
            {course.progress < 100 && course.progress > 0 && (
              <div className="flex items-start gap-2 text-xs bg-white rounded-lg border border-gray-100 p-3">
                <svg className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <div className="flex-1">
                  <div className="text-gray-500 mb-0.5">Còn lại</div>
                  <div className="font-medium text-blue-600">{course.totalLessons - course.completedLessons} bài chưa học</div>
                </div>
              </div>
            )}
            {course.progress === 100 && (
              <div className="flex items-start gap-2 text-xs bg-white rounded-lg border border-gray-100 p-3">
                <svg className="w-4 h-4 text-green-400 mt-0.5 shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <div className="text-gray-500 mb-0.5">Trạng thái</div>
                  <div className="font-medium text-green-600">Đã hoàn thành khóa học</div>
                </div>
              </div>
            )}
          </div>
        </div>
        <div className="bg-white/80 backdrop-blur rounded-xl border border-gray-100 p-5 shadow-sm space-y-5">
          <div className="flex items-center justify-between text-sm">
            <span className="font-semibold text-gray-800">Tiến độ tổng</span>
            <span className="text-gray-600">{course.progress}%</span>
          </div>
          <div className="space-y-3">
            <Progress value={course.progress} className="h-3" />
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Hoàn thành {course.completedLessons} / {course.totalLessons} bài</span>
              <span>{course.durationLabel}</span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="rounded-lg border border-gray-100 p-3 bg-white">
              <div className="text-xs text-gray-500">Trạng thái</div>
              <div className="font-semibold text-gray-900">Đang học</div>
            </div>
            <div className="rounded-lg border border-gray-100 p-3 bg-white">
              <div className="text-xs text-gray-500">Ngôn ngữ</div>
              <div className="font-semibold text-gray-900">{course.language}</div>
            </div>
          </div>
          
          {actions && <div className="pt-2 flex justify-end">{actions}</div>}
        </div>
      </div>
    </section>
  );
}
