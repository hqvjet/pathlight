import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

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
}

interface CourseCardProps {
  course: CourseCardData;
}

export function CourseCard({ course }: CourseCardProps) {
  return (
    <Card className="h-full border-gray-100 shadow-sm hover:shadow-lg transition-shadow bg-white">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-3">
          <div>
            {course.badge && (
              <Badge className="mb-2" style={course.color ? { backgroundColor: course.color, color: '#fff', borderColor: 'transparent' } : undefined}>
                {course.badge}
              </Badge>
            )}
            <CardTitle className="text-lg text-gray-900">{course.title}</CardTitle>
            <CardDescription className="text-sm text-gray-600">{course.subtitle}</CardDescription>
          </div>
          <div className="text-right text-sm text-gray-500 shrink-0">
            <div className="font-semibold text-gray-900">{course.progress}%</div>
            <div>Hoàn thành</div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-sm text-gray-700 leading-6 line-clamp-3">{course.description}</div>
        <div className="space-y-2">
          <Progress value={course.progress} />
          <div className="flex justify-between text-xs text-gray-500">
            <span>
              {course.completedLessons}/{course.totalLessons} bài
            </span>
            <span>{course.durationLabel}</span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-gray-600">
          <span className={cn('rounded-full border px-3 py-1 font-medium', 'border-gray-200 bg-gray-50 text-gray-700')}>{course.level}</span>
          <span className="rounded-full border px-3 py-1 border-gray-200 bg-white">{course.language}</span>
          <span className="rounded-full border px-3 py-1 border-gray-200 bg-white">{course.totalLessons} bài</span>
        </div>
        <div className="flex justify-between items-center pt-1">
          <div className="text-sm text-gray-500">Tiếp tục từ bài {course.completedLessons + 1}</div>
          <Link
            href={`/user/my-courses/${course.id}`}
            className="text-sm font-semibold text-orange-600 hover:text-orange-700"
          >
            Xem chi tiết →
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
