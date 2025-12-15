import { ReactNode } from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

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
  isPublic?: boolean;
}

interface CourseHeroProps {
  course: CourseHeroData;
  actions?: ReactNode;
}

export function CourseHero({ course, actions }: CourseHeroProps) {
  return (
    <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-orange-50 via-white to-blue-50 border border-orange-100 shadow-sm">
      <div className="absolute inset-y-0 right-0 w-1/3 bg-gradient-to-l from-orange-100/60 to-transparent" aria-hidden />
      <div className="p-6 sm:p-8 relative z-10 grid gap-6 lg:grid-cols-[2fr,1fr] items-center">
        <div className="space-y-3">
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
            {course.ownerId && (
              <span className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-50 border border-blue-200 text-blue-700">
                Chủ sở hữu: {course.ownerId}
              </span>
            )}
          </div>
        </div>
        <div className="bg-white/80 backdrop-blur rounded-xl border border-gray-100 p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="font-semibold text-gray-800">Tiến độ tổng</span>
            <span className="text-gray-600">{course.progress}%</span>
          </div>
          <Progress value={course.progress} />
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Hoàn thành {course.completedLessons} / {course.totalLessons} bài</span>
            <span>{course.durationLabel}</span>
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
