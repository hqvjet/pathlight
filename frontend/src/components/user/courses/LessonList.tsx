import { CourseModule, LessonItem } from '@/fake/course-landing';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

function LessonRow({ lesson }: { lesson: LessonItem }) {
  const statusStyles: Record<LessonItem['status'], string> = {
    completed: 'bg-green-50 border-green-100 text-green-700',
    'in-progress': 'bg-orange-50 border-orange-100 text-orange-700',
    locked: 'bg-gray-50 border-gray-200 text-gray-500'
  };

  return (
    <div
      className={cn(
        'flex items-center justify-between gap-3 rounded-lg border px-3 py-3 transition',
        statusStyles[lesson.status],
        lesson.isCurrent && 'ring-2 ring-orange-200'
      )}
    >
      <div className="min-w-0 space-y-0.5">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Bài</span>
          {lesson.isCurrent && <span className="text-xs font-semibold text-orange-700">Đang học</span>}
        </div>
        <p className="text-sm font-semibold text-gray-900 truncate">{lesson.title}</p>
        {lesson.summary && <p className="text-xs text-gray-600 truncate">{lesson.summary}</p>}
      </div>
      <div className="text-sm font-medium text-gray-700 whitespace-nowrap">{lesson.duration}</div>
    </div>
  );
}

interface LessonListProps {
  modules: CourseModule[];
}

export function LessonList({ modules }: LessonListProps) {
  return (
    <Card className="shadow-sm border-gray-100">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg text-gray-900">Lộ trình học</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {modules.map((module) => (
          <div key={module.id} className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-gray-900">{module.title}</p>
              <span className="text-xs text-gray-500">{module.lessons.length} bài</span>
            </div>
            <div className="space-y-2">
              {module.lessons.map((lesson) => (
                <LessonRow key={lesson.id} lesson={lesson} />
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
