'use client';

import { use, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { courseApi } from '@/lib/api/course';
import { CourseHero, CourseHeroData } from '@/components/user/courses/CourseHero';
import { LessonList, type CourseModule } from '@/components/user/courses/LessonList';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { showToast } from '@/utils/toast';

interface LessonDetailApi {
  lesson_id: string;
  course_id?: string;
  title: string;
  overview?: string;
  content?: string;
  duration?: number;
  finish: boolean;
  locked?: boolean;  // Add locked field from backend
  order?: number;
}

interface CourseFullInfoApi {
  title: string;
  overview: string;
  level: string;
  duration: number;
  finish: boolean;
  lesson: Array<{ lesson_id: string; title: string; finish: boolean }>;
  updated_at: string;
}

interface CourseFullInfoResponseApi {
  status: number;
  info?: CourseFullInfoApi;
  message?: string;
}

interface LessonListResponseApi {
  status: number;
  lessons?: LessonDetailApi[];
  message?: string;
}

type CourseDetailPageProps = {
  params: Promise<{ courseId: string }>;
};

const minutesToWeeksLabel = (minutes: number) => {
  if (!minutes) return '4 tuần';
  const days = Math.max(1, Math.round(minutes / (60 * 24)));
  if (days < 7) return `${days} ngày`;
  const weeks = Math.max(1, Math.round(days / 7));
  return `${weeks} tuần`;
};

export default function CourseDetailPage({ params }: CourseDetailPageProps) {
  const { courseId } = use(params);
  const [hero, setHero] = useState<CourseHeroData | null>(null);
  const [lessons, setLessons] = useState<LessonDetailApi[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!courseId) {
        setError('Không tìm thấy khóa học');
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const [infoResp, lessonResp] = await Promise.all([
          courseApi.getById(courseId),
          courseApi.listLessons(courseId),
        ]);

        const infoData = infoResp.data as CourseFullInfoResponseApi;
        const lessonData = lessonResp.data as LessonListResponseApi;

        if (infoData?.status !== 200 || !infoData.info) {
          throw new Error(infoData?.message || 'Không thể lấy thông tin khóa học');
        }

        const progress = infoData.info.lesson.length
          ? Math.round(
              (infoData.info.lesson.filter((l) => l.finish).length / infoData.info.lesson.length) * 100,
            )
          : 0;

        const mappedHero: CourseHeroData = {
          id: courseId,
          title: infoData.info.title,
          subtitle: infoData.info.overview || 'Lộ trình học tập được tự động tạo',
          description: infoData.info.overview || 'Khóa học không có mô tả',
          level: infoData.info.level || 'Không xác định',
          durationLabel: minutesToWeeksLabel(infoData.info.duration),
          language: 'Tiếng Việt',
          progress,
          completedLessons: infoData.info.lesson.filter((l) => l.finish).length,
          totalLessons: infoData.info.lesson.length,
          badge: progress >= 100 ? 'Hoàn thành' : progress === 0 ? 'Chưa học' : 'Đang học',
          color: '#fb923c',
        };

        if (!cancelled) {
          const parseOrder = (title: string, idx: number) => {
            const match = title.match(/^(\d+)/);
            return match ? Number(match[1]) : idx + 1;
          };

          const normalizedLessons = (lessonData?.lessons || infoData.info.lesson || []).map((l, idx) => ({
            ...l,
            order: parseOrder(l.title, idx),
          })).sort((a, b) => (a.order || 0) - (b.order || 0));

          setHero(mappedHero);
          setLessons(normalizedLessons);
        }
      } catch (e: unknown) {
        const message = e instanceof Error ? e.message : 'Không thể tải thông tin khóa học';
        if (!cancelled) setError(message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [courseId]);

  const currentLessonId = useMemo(() => {
    if (!lessons.length) return null;
    const firstIncomplete = lessons.find((lesson) => !lesson.finish);
    return firstIncomplete?.lesson_id || lessons[lessons.length - 1]?.lesson_id || null;
  }, [lessons]);

  const modules = useMemo<CourseModule[]>(() => {
    return [
      {
        id: 'main',
        title: 'Lộ trình khóa học',
        lessons: lessons.map((lesson, idx) => {
          // Use backend-provided locked status
          let status: 'completed' | 'in-progress' | 'locked';
          if (lesson.finish) {
            status = 'completed';
          } else if (lesson.locked) {
            status = 'locked';
          } else {
            // Not finished and not locked = in progress
            status = 'in-progress';
          }

          return {
            id: lesson.lesson_id,
            title: lesson.title,
            duration: '—',
            status,
            order: idx + 1,
            isCurrent: status === 'in-progress',
          };
        }),
      },
    ];
  }, [lessons]);

  const continueLessonId = useMemo(() => {
    // Find the first in-progress lesson (next unfinished lesson)
    const inProgressLesson = modules[0]?.lessons.find((lesson) => lesson.status === 'in-progress');
    if (inProgressLesson) return inProgressLesson.id;
    
    // If no in-progress, find first not completed (shouldn't happen with proper logic)
    const firstIncomplete = modules[0]?.lessons.find((lesson) => lesson.status !== 'completed');
    return firstIncomplete?.id || null;
  }, [modules]);

  const handleSelectLesson = (lessonId: string) => {
    const selected = modules[0]?.lessons.find((lesson) => lesson.id === lessonId);
    if (!selected) return;
    if (selected.status === 'locked') {
      showToast.info('Hoàn thành bài trước để mở khóa bài này');
      return;
    }
    router.push(`/user/my-courses/${courseId}/lessons/${lessonId}`);
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-white rounded-xl p-10 text-center border border-gray-100 shadow-sm">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-orange-500 mx-auto" />
          <p className="mt-4 text-gray-600">Đang tải khóa học...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-red-50 text-red-700 rounded-xl p-4 border border-red-200 text-sm">{error}</div>
      </div>
    );
  }

  if (!hero) return null;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex items-center gap-3 text-sm text-gray-600">
        <Link href="/user/my-courses" className="text-orange-600 font-semibold hover:text-orange-700">← Quay lại danh sách</Link>
        <span className="text-gray-400">/</span>
        <span className="font-semibold text-gray-800">{hero.title}</span>
      </div>

      <CourseHero course={hero} />

      <div className="grid gap-6 lg:grid-cols-[320px,minmax(0,1fr)]">
        <div className="space-y-3">
          <Card className="shadow-sm border-gray-100 sticky top-4">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-gray-900">Mục lục</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-700 font-semibold">Tiến độ</span>
                <span className="text-gray-600">{hero.progress}%</span>
              </div>
              <Progress value={hero.progress} />
              <LessonList modules={modules} selectedId={currentLessonId} onSelect={handleSelectLesson} />
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6 lg:col-span-1">
          <Card className="shadow-sm border-gray-100">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg text-gray-900">Nội dung chi tiết</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-gray-700">
              <p>Chọn một bài học trong mục lục để mở trang nội dung và bài test toàn màn hình.</p>
              <Link
                href={continueLessonId ? `/user/my-courses/${courseId}/lessons/${continueLessonId}` : '#'}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-orange-500 text-white font-semibold hover:bg-orange-600 disabled:opacity-50"
              >
                Tiếp tục học bài hiện tại
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
