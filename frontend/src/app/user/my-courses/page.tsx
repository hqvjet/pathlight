'use client';

import { useEffect, useMemo, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { courseApi } from '@/lib/api/course';
import { userApi } from '@/lib/api/user';
import { CourseCard, CourseCardData } from '@/components/user/courses/CourseCard';
import { CourseHero, CourseHeroData } from '@/components/user/courses/CourseHero';
import { Badge } from '@/components/ui/badge';
import Link from 'next/link';
import { useAuthContext } from '@/context/AuthContext';

type SortOption = 'latest' | 'progress_desc' | 'title_asc';
type TabType = 'my' | 'public';

interface ApiCourseSummary {
  course_id: string;
  title: string;
  overview: string;
  level: string;
  finish: boolean;
  duration: number;
  lesson_num: number;
  finish_lesson_num: number;
  created_at: string;
  updated_at: string;
  publish?: boolean;
  user_id?: string;
  owner_id?: string;
  owner_name?: string;
  recommendation_score?: number;
}

interface ApiCourseListResponse {
  status: number;
  courses?: ApiCourseSummary[];
}

const ITEMS_PER_PAGE = 9;

const minutesToWeeksLabel = (minutes: number) => {
  if (!minutes) return '4 tuần';
  const days = Math.max(1, Math.round(minutes / (60 * 24)));
  if (days < 7) return `${days} ngày`;
  const weeks = Math.max(1, Math.round(days / 7));
  return `${weeks} tuần`;
};

const mapApiToCard = (c: ApiCourseSummary): CourseCardData & CourseHeroData => {
  const progress = c.lesson_num > 0 ? Math.floor((c.finish_lesson_num / c.lesson_num) * 100) : 0;
  const badge = c.finish || progress >= 100 ? 'Hoàn thành' : 'Đang học';
  const ownerName = c.owner_name || '';
  const ownerId = c.user_id || c.owner_id || '';
  
  // If course has owner info and owner_name is available, show it; otherwise show "do bạn tạo"
  let subtitle = 'Khóa học do bạn tạo';
  if (c.publish && ownerName) {
    subtitle = ownerName;
  } else if (c.publish && ownerId) {
    subtitle = ownerId.includes('@') ? ownerId.split('@')[0] : ownerId.substring(0, 8) + '...';
  }
  
  return {
    id: c.course_id,
    title: c.title || 'Khóa học không tên',
    subtitle,
    description: c.overview || 'Cập nhật mô tả khóa học để học viên hiểu rõ mục tiêu.',
    level: c.level || 'Không xác định',
    durationLabel: minutesToWeeksLabel(c.duration),
    language: 'Tiếng Việt',
    progress,
    completedLessons: c.finish_lesson_num || 0,
    totalLessons: c.lesson_num || 0,
    badge,
    color: '#fb923c',
    createdAt: c.created_at,
    updatedAt: c.updated_at,
    lastAccessed: progress > 0 ? c.updated_at : undefined, // Show last accessed only if has progress
    isPublic: !!c.publish,
    ownerId,
    ownerName,
    recommendation_score: c.recommendation_score,
  };
};

function MyCoursesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, loading: authLoading, user } = useAuthContext();
  const [activeTab, setActiveTab] = useState<TabType>('my');
  const [currentPage, setCurrentPage] = useState(1);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortOption>('latest');
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [ownerFilter, setOwnerFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [courses, setCourses] = useState<Array<CourseCardData & CourseHeroData>>([]);
  const [publicCourses, setPublicCourses] = useState<Array<CourseCardData & CourseHeroData>>([]);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const greeting = (() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Chào buổi sáng';
    if (hour < 18) return 'Chào buổi chiều';
    return 'Chào buổi tối';
  })();

  useEffect(() => {
    const tabParam = searchParams.get('tab');
    if (tabParam === 'public') {
      setActiveTab('public');
    }
  }, [searchParams]);
  
  useEffect(() => {
    setCurrentPage(1);
  }, [activeTab, search, sort, levelFilter, statusFilter, ownerFilter]);
  
  useEffect(() => {
    // Clear owner filter when switching tabs or searching
    if (activeTab === 'my' || search) {
      setOwnerFilter('');
    }
  }, [activeTab, search]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/auth/signin?redirect=/user/my-courses');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (authLoading || !isAuthenticated) return;
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await courseApi.getAll();
        const data = resp.data as ApiCourseListResponse | undefined;
        let list = (data?.courses || []).map(mapApiToCard);
        
        // Fetch owner names for all courses
        const uniqueOwnerIds = Array.from(new Set(list.map(c => c.ownerId).filter(Boolean)));
        if (uniqueOwnerIds.length > 0) {
          try {
            const usersResp = await userApi.batchUsers(uniqueOwnerIds);
            const usersData = usersResp.data as Record<string, { name: string }>;
            // Update owner names
            list = list.map(course => ({
              ...course,
              ownerName: course.ownerId && usersData[course.ownerId] 
                ? usersData[course.ownerId].name 
                : course.ownerName
            }));
          } catch (err) {
            console.warn('Failed to fetch user names:', err);
          }
        }
        
        if (!cancelled) {
          setCourses(list);
          if (list.length > 0 && !selectedId) {
            setSelectedId(list[0].id || null);
          }
        }
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading, isAuthenticated]); // selectedId intentionally omitted to prevent infinite loop

  // Load recommended courses immediately on mount
  useEffect(() => {
    if (authLoading || !isAuthenticated) return;
    let cancelled = false;
    const loadPublic = async () => {
      try {
        // Use recommendation API instead of listPublic
        const resp = await courseApi.getRecommended(20);
        const data = resp.data as { status: number; items?: unknown[] };
        let list = (data?.items || []).map((item: unknown) => {
          const courseItem = item as Record<string, unknown>;
          return {
            course_id: courseItem.course_id as string,
            title: courseItem.title as string,
            overview: courseItem.description as string,
            level: courseItem.difficulty as string,
            finish: false,
            duration: courseItem.duration as number,
            lesson_num: (courseItem.num_lessons as number) || 0,
            finish_lesson_num: 0,
            created_at: (courseItem.created_at as string) || new Date().toISOString(),
            updated_at: (courseItem.updated_at as string) || new Date().toISOString(),
            publish: true,
            user_id: courseItem.user_id as string,
            owner_id: courseItem.user_id as string,
            recommendation_score: courseItem.recommendation_score as number | undefined,
          };
        }).map(mapApiToCard);
        
        // Fetch owner names for public courses
        const uniqueOwnerIds = Array.from(new Set(list.map(c => c.ownerId).filter(Boolean)));
        if (uniqueOwnerIds.length > 0) {
          try {
            const usersResp = await userApi.batchUsers(uniqueOwnerIds);
            const usersData = usersResp.data as Record<string, { name: string }>;
            // Update owner names
            list = list.map(course => ({
              ...course,
              ownerName: course.ownerId && usersData[course.ownerId] 
                ? usersData[course.ownerId].name 
                : course.ownerName
            }));
          } catch (err) {
            console.warn('Failed to fetch user names for public courses:', err);
          }
        }
        
        if (!cancelled) setPublicCourses(list);
      } catch {
        if (!cancelled) setPublicCourses([]);
      }
    };
    loadPublic();
    return () => { cancelled = true; };
  }, [authLoading, isAuthenticated]);

  const updateCourseVisibility = async (courseId: string, isPublic: boolean) => {
    setSavingId(courseId);
    try {
      await courseApi.updateVisibility({ course_id: courseId, is_public: isPublic });
      setCourses((prev) => prev.map((c) => (c.id === courseId ? { ...c, isPublic } : c)));
    } catch {
      setError('Không thể cập nhật quyền riêng tư của khóa học.');
    } finally {
      setSavingId(null);
    }
  };

  const deleteCourse = async (courseId: string) => {
    setSavingId(courseId);
    try {
      await courseApi.deleteCourse(courseId);
      setCourses((prev) => prev.filter((c) => c.id !== courseId));
      setPublicCourses((prev) => prev.filter((c) => c.id !== courseId)); // Also remove from public list
      if (selectedId === courseId) setSelectedId(null);
    } catch (err) {
      console.error('Delete course error:', err);
      setError('Không thể xóa khóa học.');
    } finally {
      setSavingId(null);
    }
  };

  const filtered = useMemo(() => {
    const source = activeTab === 'my' ? courses : publicCourses;
    let list = source.filter((c) => c.title.toLowerCase().includes(search.toLowerCase()));
    
    // Filter by owner (only in public tab)
    if (ownerFilter && activeTab === 'public') {
      list = list.filter((c) => c.ownerId === ownerFilter);
    }
    
    if (levelFilter !== 'all') {
      list = list.filter((c) => c.level === levelFilter);
    }
    
    if (statusFilter !== 'all') {
      if (statusFilter === 'completed') {
        list = list.filter((c) => c.progress >= 100 || c.badge === 'Hoàn thành');
      } else if (statusFilter === 'in_progress') {
        list = list.filter((c) => c.progress > 0 && c.progress < 100 && c.badge !== 'Hoàn thành');
      }
    }
    
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
  }, [courses, publicCourses, activeTab, search, sort, levelFilter, statusFilter, ownerFilter]);

  const paginatedCourses = filtered.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const heroCourse = selectedId ? paginatedCourses.find((c) => c.id === selectedId) : null;
  const remaining = heroCourse ? paginatedCourses.filter((c) => c.id !== heroCourse.id) : paginatedCourses;

  useEffect(() => {
    if (selectedId && !paginatedCourses.find((c) => c.id === selectedId)) {
      setSelectedId(null);
    }
  }, [paginatedCourses, selectedId]);

  useEffect(() => {
    setCurrentPage(1);
  }, [search, levelFilter, statusFilter, ownerFilter, activeTab]);

  const handleSelect = (course: CourseCardData) => {
    setSelectedId(course.id);
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleOwnerClick = (ownerId: string) => {
    if (activeTab === 'public') {
      setOwnerFilter(ownerId);
      setSearch(''); // Clear search when filtering by owner
      if (typeof window !== 'undefined') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }
  };

  if (!authLoading && !isAuthenticated) return null;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <header className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <p className="text-sm text-gray-500">{greeting}</p>
            <h2 className="text-2xl font-semibold text-gray-900">Khóa Học Của Tôi</h2>
          </div>
          <div className="flex-1" />
          <div className="flex items-center gap-2 text-sm">
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
      </header>

      <div className="border-b">
        <div className="flex gap-6">
          <button
            onClick={() => setActiveTab('my')}
            className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'my'
                ? 'border-orange-600 text-orange-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Khóa Học Của Tôi
            <span className="ml-2 px-2 py-0.5 rounded-full bg-gray-100 text-xs">
              {courses.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('public')}
            className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'public'
                ? 'border-orange-600 text-orange-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Khóa Học Công Khai
            <span className="ml-2 px-2 py-0.5 rounded-full bg-gray-100 text-xs">
              {publicCourses.length}
            </span>
          </button>
        </div>
      </div>

      {/* Mobile-friendly layout */}
      <div className="flex flex-col gap-3">
        {/* Search bar - full width on mobile */}
        <div className="relative w-full">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm khóa học..."
            className="w-full h-11 pl-10 pr-4 rounded-full border border-gray-200 bg-white shadow-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-400 text-sm"
          />
          <svg className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        
        {/* View Mode Toggle - Hide on mobile */}
        <div className="hidden md:flex items-center gap-1 bg-gray-100 p-1 rounded-lg self-end">
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'grid'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
            title="Hiển thị lưới"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'list'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
            title="Hiển thị danh sách"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
        
        {ownerFilter && activeTab === 'public' && (() => {
          const ownerCourse = publicCourses.find(c => c.ownerId === ownerFilter);
          const displayName = ownerCourse?.ownerName || ownerFilter.substring(0, 8) + '...';
          return (
            <div className="flex items-center gap-2 px-3 py-2 rounded-full bg-blue-50 border border-blue-200 text-sm">
              <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span className="text-blue-700 font-medium">{displayName}</span>
              <button
                onClick={() => setOwnerFilter('')}
                className="ml-1 w-4 h-4 rounded-full hover:bg-blue-200 flex items-center justify-center text-blue-600"
                title="Xóa bộ lọc"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          );
        })()}
        
        <div className="flex gap-2 flex-wrap">
          <div className="relative">
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="appearance-none h-11 pl-3 pr-8 rounded-full bg-white border border-gray-200 shadow-sm text-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-400 min-w-[110px]"
            >
              <option value="all">Tất cả mức</option>
              <option value="EASY">Easy</option>
              <option value="MEDIUM">Medium</option>
              <option value="HARD">Hard</option>
            </select>
            <svg className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          
          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="appearance-none h-11 pl-3 pr-8 rounded-full bg-white border border-gray-200 shadow-sm text-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-400 min-w-[120px]"
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="completed">Hoàn thành</option>
              <option value="in_progress">Đang học</option>
            </select>
            <svg className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          
          <div className="relative">
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
        </div>
      </div>

      {heroCourse && filtered.length > 0 && (() => {
        // Check if current user is the owner of the course
        const isOwner = activeTab === 'my' || (user?.id && heroCourse.ownerId === user.id);
        
        return (
          <div className="transition-all duration-500 ease-out relative" key={heroCourse.id}>
            <button
              onClick={() => setSelectedId(null)}
              className="absolute -top-4 -right-4 z-50 w-10 h-10 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-900 shadow-md flex items-center justify-center transition-all hover:scale-110 cursor-pointer"
              title="Đóng chi tiết"
            >
              <svg className="w-6 h-6 pointer-events-none" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <CourseHero
              course={heroCourse}
              actions={(
                <div className="flex flex-wrap gap-2">
                  <Link
                    href={`/user/my-courses/${heroCourse.id}`}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-orange-500 text-white font-semibold shadow-sm hover:bg-orange-600"
                  >
                    Xem chi tiết →
                  </Link>
                  {isOwner && (
                    <>
                      <button
                        onClick={() => updateCourseVisibility(heroCourse.id, !heroCourse.isPublic)}
                        disabled={savingId === heroCourse.id}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 bg-white text-gray-800 font-semibold shadow-sm hover:shadow disabled:opacity-60"
                      >
                        {heroCourse.isPublic ? 'Chuyển Private' : 'Công khai'}
                      </button>
                      <button
                        onClick={() => deleteCourse(heroCourse.id)}
                        disabled={savingId === heroCourse.id}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-red-50 text-red-600 font-semibold border border-red-200 hover:bg-red-100 disabled:opacity-60"
                      >
                        Xóa
                      </button>
                    </>
                  )}
                </div>
              )}
            />
          </div>
        );
      })()}

      <section className="space-y-4">
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
          <div className={viewMode === 'grid' ? 'grid gap-4 sm:gap-5 md:grid-cols-2 lg:grid-cols-3 auto-rows-fr' : 'space-y-4'}>
            {remaining.map((course) => (
              <div
                key={course.id}
                className="transition-all duration-300 ease-in-out hover:-translate-y-0.5"
              >
                <CourseCard course={course} onSelect={handleSelect} onOwnerClick={handleOwnerClick} />
              </div>
            ))}
            {remaining.length === 0 && courses.length > 0 && (
              <div className="bg-white rounded-xl p-8 sm:p-10 text-center border border-dashed border-gray-300 col-span-full">
                <p className="text-gray-600">Không tìm thấy khóa học phù hợp với bộ lọc.</p>
                <button
                  onClick={() => { setSearch(''); setLevelFilter('all'); setStatusFilter('all'); }}
                  className="mt-3 text-sm text-orange-600 hover:text-orange-700 font-medium"
                >
                  Xóa bộ lọc
                </button>
              </div>
            )}
            {courses.length === 0 && (
              <div className="bg-white rounded-xl p-8 sm:p-12 text-center border border-dashed border-gray-300 col-span-full">
                <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <p className="text-gray-600 mb-2">Bạn chưa có khóa học nào.</p>
                <p className="text-sm text-gray-500 mb-4">Bắt đầu bằng cách tạo khóa học mới!</p>
                <a
                  href="/user/create-course"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-semibold shadow-sm"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                  Tạo khóa học đầu tiên
                </a>
              </div>
            )}
          </div>
        )}
        
        {/* Pagination */}
        {filtered.length > ITEMS_PER_PAGE && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 rounded-lg border border-gray-200 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Trước
            </button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.ceil(filtered.length / ITEMS_PER_PAGE) }, (_, i) => i + 1).map(page => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    currentPage === page
                      ? 'bg-orange-500 text-white'
                      : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {page}
                </button>
              ))}
            </div>
            <button
              onClick={() => setCurrentPage(prev => Math.min(Math.ceil(filtered.length / ITEMS_PER_PAGE), prev + 1))}
              disabled={currentPage === Math.ceil(filtered.length / ITEMS_PER_PAGE)}
              className="px-4 py-2 rounded-lg border border-gray-200 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Sau
            </button>
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

export default function MyCoursesPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500" />
      </div>
    }>
      <MyCoursesContent />
    </Suspense>
  );
}
