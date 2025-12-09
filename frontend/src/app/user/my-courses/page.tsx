'use client';

import { useEffect, useMemo, useState } from 'react';
import { courseApi } from '@/lib/api/course';
import { CourseCard, CourseCardData } from '@/components/user/courses/CourseCard';
import { CourseHero, CourseHeroData } from '@/components/user/courses/CourseHero';
import { Badge } from '@/components/ui/badge';

type SortOption = 'latest' | 'progress_desc' | 'title_asc';

interface ApiCourseSummary {
  course_id: string;
  title: string;
  description: string;
  duration: number;
  lesson_num: number;
  finish_lesson_num: number;
  updated_at: string;
}

interface ApiCourseListResponse {
  status: number;
  courses?: ApiCourseSummary[];
}

const minutesToWeeksLabel = (minutes: number) => {
  if (!minutes) return '4 tuần';
  const days = Math.max(1, Math.round(minutes / (60 * 24)));
  if (days < 7) return `${days} ngày`;
  const weeks = Math.max(1, Math.round(days / 7));
  return `${weeks} tuần`;
};

const mapApiToCard = (c: ApiCourseSummary): CourseCardData & CourseHeroData => {
  const progress = c.lesson_num > 0 ? Math.floor((c.finish_lesson_num / c.lesson_num) * 100) : 0;
  const badge = progress >= 100 ? 'Hoàn thành' : progress === 0 ? 'Bản nháp' : 'Đang học';
  return {
    id: c.course_id,
    title: c.title || 'Khóa học không tên',
    subtitle: 'Khoá học do bạn tạo',
    description: c.description || 'Cập nhật mô tả khóa học để học viên hiểu rõ mục tiêu.',
    level: 'Trung cấp',
    durationLabel: minutesToWeeksLabel(c.duration),
    language: 'Tiếng Việt',
    progress,
    completedLessons: c.finish_lesson_num || 0,
    totalLessons: c.lesson_num || 0,
    badge,
    color: '#fb923c',
    updatedAt: c.updated_at,
  };
};

export default function MyCoursesPage() {
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortOption>('latest');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [courses, setCourses] = useState<Array<CourseCardData & CourseHeroData>>([]);
  const greeting = (() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Chào buổi sáng';
    if (hour < 18) return 'Chào buổi chiều';
    return 'Chào buổi tối';
  })();

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await courseApi.getAll();
        const data = resp.data as ApiCourseListResponse | undefined;
        const list = (data?.courses || []).map(mapApiToCard);
        if (!cancelled) setCourses(list);
      } catch {
        if (!cancelled) setError('Không thể tải danh sách khóa học. Vui lòng thử lại.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    let list = courses.filter((c) => c.title.toLowerCase().includes(search.toLowerCase()));
    switch (sort) {
      case 'progress_desc':
        list = [...list].sort((a, b) => b.progress - a.progress);
        break;
      case 'title_asc':
        list = [...list].sort((a, b) => a.title.localeCompare(b.title, 'vi'));
        break;
      default:
        list = [...list].sort(
          (a, b) => new Date(b.updatedAt || '').getTime() - new Date(a.updatedAt || '').getTime(),
        );
    }
    return list;
  }, [courses, search, sort]);

  const highlight = filtered[0] || courses[0];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {highlight && (
        <CourseHero course={highlight} />
      )}

      <section className="space-y-4">
        <div className="flex flex-wrap items-center gap-3 justify-between">
          <div>
            <p className="text-sm text-gray-500">{greeting}</p>
            <h2 className="text-2xl font-semibold text-gray-900">Khóa Học Của Tôi</h2>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="relative">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Tìm khóa học..."
                className="w-72 sm:w-80 lg:w-96 h-11 pl-10 pr-4 rounded-full border border-gray-200 bg-white shadow-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-400 text-sm"
              />
              <svg className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div className="relative">
              <span className="absolute -top-5 left-0 text-[11px] font-semibold text-gray-500 tracking-wide uppercase">Sắp xếp</span>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value as SortOption)}
                className="appearance-none h-11 pl-3 pr-8 rounded-full bg-white border border-gray-200 shadow-sm text-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-400 min-w-[120px]"
              >
                <option value="latest">Mới nhất</option>
                <option value="progress_desc">Tiến độ cao</option>
                <option value="title_asc">Tên A-Z</option>
              </select>
              <svg className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
            <a
              href="/user/generation-tracking"
              className="inline-flex items-center gap-2 px-5 h-11 rounded-full border border-gray-200 bg-white text-gray-900 font-semibold shadow-sm hover:shadow-md"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2" />
              </svg>
              Theo dõi tiến trình
            </a>
            <a
              href="/user/create-course"
              className="inline-flex items-center gap-2 px-5 h-11 rounded-full bg-orange-500 hover:bg-orange-600 text-white font-semibold shadow-lg"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              Tạo khóa học
            </a>
          </div>
        </div>

        {loading && (
          <div className="bg-white rounded-xl p-10 text-center border border-gray-100 shadow-sm">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-orange-500 mx-auto" />
            <p className="mt-4 text-gray-600">Đang tải danh sách khóa học...</p>
          </div>
        )}

        {!loading && error && (
          <div className="bg-red-50 text-red-700 rounded-xl p-4 border border-red-200 text-sm">{error}</div>
        )}

        {!loading && !error && (
          <div className="grid gap-5 md:grid-cols-2">
            {filtered.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
            {filtered.length === 0 && (
              <div className="bg-white rounded-xl p-10 text-center border border-dashed border-gray-300">
                <p className="text-gray-600">Không tìm thấy khóa học phù hợp.</p>
              </div>
            )}
          </div>
        )}
      </section>

      <footer className="pt-2 pb-8 text-xs text-gray-400 flex flex-wrap gap-6 justify-center">
        <Badge variant="outline" className="text-gray-500 border-gray-200">FAQs</Badge>
        <Badge variant="outline" className="text-gray-500 border-gray-200">Privacy Policy</Badge>
        <Badge variant="outline" className="text-gray-500 border-gray-200">Terms & Condition</Badge>
      </footer>
    </div>
  );
}
