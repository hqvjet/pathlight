import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export type LessonStatus = 'completed' | 'in-progress' | 'locked';

export interface LessonItem {
  id: string;
  title: string;
  duration: string;
  status: LessonStatus;
  summary?: string;
  isCurrent?: boolean;
  order?: number;
}

export interface CourseModule {
  id: string;
  title: string;
  lessons: LessonItem[];
}

interface LessonRowProps {
  lesson: LessonItem;
  selected?: boolean;
  onSelect?: (lessonId: string) => void;
}

function LessonRow({ lesson, selected, onSelect }: LessonRowProps) {
  const statusStyles: Record<LessonItem['status'], string> = {
    completed: 'bg-green-50 border-green-100 text-green-700',
    'in-progress': 'bg-orange-50 border-orange-100 text-orange-700',
    locked: 'bg-gray-50 border-gray-200 text-gray-500'
  };

  const numberLabel = lesson.order ?? lesson.title.split('.')[0] ?? '';

  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-lg border px-3 py-3 transition',
        statusStyles[lesson.status],
        lesson.isCurrent && 'ring-2 ring-orange-200',
        onSelect && lesson.status !== 'locked' && 'cursor-pointer hover:shadow-sm',
        selected && 'ring-2 ring-orange-300',
        lesson.status === 'locked' && 'opacity-70 pointer-events-none'
      )}
      role={onSelect ? 'button' : undefined}
      tabIndex={onSelect ? 0 : undefined}
      onClick={() => {
        if (lesson.status === 'locked') return;
        onSelect?.(lesson.id);
      }}
      onKeyDown={(e) => {
        if (!onSelect) return;
        if (lesson.status === 'locked') return;
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(lesson.id);
        }
      }}
    >
      <div className="min-w-0 space-y-1">
        <div className="flex items-center justify-between text-xs font-semibold text-gray-800">
          <span className="uppercase tracking-wide">Bài {numberLabel}</span>
          <span
            className={cn(
              'inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[11px] font-semibold',
              lesson.status === 'completed' && 'border-green-200 text-green-700 bg-white',
              lesson.status === 'in-progress' && 'border-orange-200 text-orange-700 bg-white',
              lesson.status === 'locked' && 'border-gray-200 text-gray-600 bg-white'
            )}
          >
            {lesson.status === 'completed' ? '✓' : lesson.status === 'locked' ? 'Khóa' : 'Đang học'}
          </span>
        </div>
        <p className="text-sm font-semibold text-gray-900 leading-5 line-clamp-2">{lesson.title.replace(/^\d+\.\s*/, '')}</p>
        {lesson.summary && <p className="text-xs text-gray-600 line-clamp-2 leading-5">{lesson.summary}</p>}
      </div>
    </div>
  );
}

interface LessonListProps {
  modules: CourseModule[];
  selectedId?: string | null;
  onSelect?: (lessonId: string) => void;
}

export function LessonList({ modules, selectedId, onSelect }: LessonListProps) {
  return (
    <Card className="shadow-sm border-gray-100">
      <CardContent className="space-y-6">
        {modules.map((module) => (
          <div key={module.id} className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-gray-900">{module.title}</p>
              <span className="text-xs text-gray-500">{module.lessons.length} bài</span>
            </div>
            <div className="space-y-2">
              {module.lessons.map((lesson) => (
                <LessonRow
                  key={lesson.id}
                  lesson={lesson}
                  selected={selectedId === lesson.id}
                  onSelect={onSelect}
                />
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
