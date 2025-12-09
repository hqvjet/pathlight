'use client';

import { useEffect, useMemo, useState } from 'react';
import { courseApi } from '@/lib/api/course';
import { CourseHero, CourseHeroData } from '@/components/user/courses/CourseHero';
import { LessonList } from '@/components/user/courses/LessonList';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface CourseDetailPageProps {
  params: {
    courseId: string;
  };
}

interface LessonDetailApi {
  lesson_id: string;
  course_id: string;
  title: string;
  description: string;
  content: string;
  finish: boolean;
}

interface CourseFullInfoApi {
  title: string;
  description: string;
  duration: number;
  roadmap?: string | null;
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

const minutesToWeeksLabel = (minutes: number) => {
  if (!minutes) return '4 tuần';
  const days = Math.max(1, Math.round(minutes / (60 * 24)));
  if (days < 7) return `${days} ngày`;
  const weeks = Math.max(1, Math.round(days / 7));
  return `${weeks} tuần`;
};

export default function CourseDetailPage({ params }: CourseDetailPageProps) {
  const [hero, setHero] = useState<CourseHeroData | null>(null);
  const [lessons, setLessons] = useState<LessonDetailApi[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [infoResp, lessonResp] = await Promise.all([
          courseApi.getById(params.courseId),
          courseApi.listLessons(params.courseId),
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
          id: params.courseId,
          title: infoData.info.title,
          subtitle: infoData.info.roadmap || 'Lộ trình học tập được tự động tạo',
          description: infoData.info.description || 'Khóa học không có mô tả',
          level: 'Trung cấp',
          durationLabel: minutesToWeeksLabel(infoData.info.duration),
          language: 'Tiếng Việt',
          progress,
          completedLessons: infoData.info.lesson.filter((l) => l.finish).length,
          totalLessons: infoData.info.lesson.length,
          badge: progress >= 100 ? 'Hoàn thành' : progress === 0 ? 'Chưa học' : 'Đang học',
          color: '#fb923c',
        };

        if (!cancelled) {
          setHero(mappedHero);
          setLessons(lessonData?.lessons || []);
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Không thể tải dữ liệu khóa học';
        if (!cancelled) setError(message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [params.courseId]);

  const modules = useMemo(() => {
    if (!lessons.length) return [];
    return [
      {
        id: 'main',
        title: 'Nội dung khóa học',
        lessons: lessons.map((lesson, idx) => ({
          id: lesson.lesson_id,
          title: `${idx + 1}. ${lesson.title}`,
          duration: '—',
          status: lesson.finish ? 'completed' : 'locked',
          summary: lesson.description,
          isCurrent: !lesson.finish && idx === lessons.findIndex((l) => !l.finish),
        })),
      },
    ];
  }, [lessons]);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {loading && (
        <div className="bg-white rounded-xl p-10 text-center border border-gray-100 shadow-sm">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-orange-500 mx-auto" />
          <p className="mt-4 text-gray-600">Đang tải khóa học...</p>
        </div>
      )}

      {!loading && error && (
        <div className="bg-red-50 text-red-700 rounded-xl p-4 border border-red-200 text-sm">{error}</div>
      )}

      {!loading && !error && hero && (
        <>
          <CourseHero course={hero} />

          <div className="grid gap-6 lg:grid-cols-[1.6fr,1fr]">
            <LessonList modules={modules} />
            <Card className="shadow-sm border-gray-100">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg text-gray-900">Thông tin khóa học</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm text-gray-700">
                <div className="rounded-lg bg-gray-50 border border-gray-100 p-3 space-y-1">
                  <p className="text-xs text-gray-500">Tổng quan</p>
                  <p className="font-medium text-gray-900 leading-6">{hero.subtitle}</p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg border border-gray-100 bg-white">
                    <p className="text-xs text-gray-500">Cấp độ</p>
                    <p className="font-semibold text-gray-900">{hero.level || 'N/A'}</p>
                  </div>
                  <div className="p-3 rounded-lg border border-gray-100 bg-white">
                    <p className="text-xs text-gray-500">Thời lượng</p>
                    <p className="font-semibold text-gray-900">{hero.durationLabel}</p>
                  </div>
                  <div className="p-3 rounded-lg border border-gray-100 bg-white">
                    <p className="text-xs text-gray-500">Tiến độ</p>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-orange-500 text-white border-none">{hero.progress}%</Badge>
                      <span className="text-gray-700">{hero.completedLessons}/{hero.totalLessons} bài</span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg border border-gray-100 bg-white">
                    <p className="text-xs text-gray-500">Ngôn ngữ</p>
                    <p className="font-semibold text-gray-900">{hero.language || 'N/A'}</p>
                  </div>
                </div>
                <div className="text-xs text-gray-500">Dữ liệu hiển thị từ API course-service.</div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
