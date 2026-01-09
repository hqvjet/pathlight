'use client';
import { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { BookOpen, FileQuestion, RefreshCw, TrendingUp, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import GenerationList, { GenerationItem } from '@/components/user/generation/GenerationList';
import QuizGenerationList, { QuizGenerationItem } from '@/components/user/quiz-generation/QuizGenerationList';
import { courseApi } from '@/lib/api/course';
import { quizApi } from '@/lib/api/quiz';
import { showToast } from '@/utils/toast';

type TabType = 'courses' | 'quizzes';

function TrackingInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('courses');
  const [courseItems, setCourseItems] = useState<GenerationItem[]>([]);
  const [quizItems, setQuizItems] = useState<QuizGenerationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(6);

  useEffect(() => {
    const tabParam = searchParams.get('tab');
    if (tabParam === 'quizzes') {
      setActiveTab('quizzes');
    }
  }, [searchParams]);

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    setCurrentPage(1);
    const url = new URL(window.location.href);
    url.searchParams.set('tab', tab);
    router.push(url.pathname + url.search, { scroll: false });
  };

  const loadCourseData = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await courseApi.listMyGenerations();
      if (resp.status === 200 && Array.isArray(resp.data?.items)) {
        const items = resp.data.items as GenerationItem[];
        items.sort((a, b) => {
          const aTime = a.updated_at || a.last_updated;
          const bTime = b.updated_at || b.last_updated;
          if (!aTime) return 1;
          if (!bTime) return -1;
          return new Date(bTime).getTime() - new Date(aTime).getTime();
        });
        setCourseItems(items);
      } else if (resp.status === 401) {
        showToast.error("Bạn cần đăng nhập để xem tiến trình.");
      } else {
        showToast.error("Không thể tải dữ liệu tiến trình khóa học.");
      }
    } catch {
      showToast.error("Có lỗi xảy ra khi tải dữ liệu khóa học.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadQuizData = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await quizApi.listMyGenerations();
      if (resp.status === 200 && Array.isArray(resp.data?.items)) {
        const mapped = (resp.data.items as unknown as Array<Record<string, unknown>>).map((r) => ({
          quiz_id: String(r.quiz_id ?? ""),
          user_id: r.user_id ? String(r.user_id) : undefined,
          status: r.status ? String(r.status) : undefined,
          progress_percentage: typeof r.progress_percentage === 'number' ? r.progress_percentage : undefined,
          current_step: r.current_step ? String(r.current_step) : undefined,
          current_step_detail: r.current_step_detail ? String(r.current_step_detail) : undefined,
          vectorized: r.vectorized !== undefined ? Boolean(r.vectorized) : undefined,
          plan_ready: r.plan_ready !== undefined ? Boolean(r.plan_ready) : undefined,
          questions_ready: r.questions_ready !== undefined ? Boolean(r.questions_ready) : undefined,
          title: r.title ? String(r.title) : undefined,
          overview: r.overview ? String(r.overview) : undefined,
          ideas_count: typeof r.ideas_count === 'number' ? r.ideas_count : undefined,
          questions_count: typeof r.questions_count === 'number' ? r.questions_count : undefined,
          start_timestamp: r.start_timestamp ? String(r.start_timestamp) : undefined,
          end_timestamp: r.end_timestamp ? String(r.end_timestamp) : undefined,
          updated_at: r.updated_at ? String(r.updated_at) : undefined,
          title_ready: r.title_ready !== undefined ? Boolean(r.title_ready) : r.plan_ready !== undefined ? Boolean(r.plan_ready) : undefined,
          cards_ready: r.cards_ready !== undefined ? Boolean(r.cards_ready) : r.questions_ready !== undefined ? Boolean(r.questions_ready) : undefined,
        })) as QuizGenerationItem[];
        
        mapped.sort((a, b) => {
          if (!a.updated_at) return 1;
          if (!b.updated_at) return -1;
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        });
        
        setQuizItems(mapped);
      } else if (resp.status === 401) {
        showToast.error("Bạn cần đăng nhập để xem tiến trình.");
      } else {
        showToast.error("Không thể tải dữ liệu tiến trình quiz.");
      }
    } catch {
      showToast.error("Có lỗi xảy ra khi tải dữ liệu quiz.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'courses') {
      loadCourseData();
    } else {
      loadQuizData();
    }
  }, [activeTab, loadCourseData, loadQuizData]);

  const handleRefresh = () => {
    if (activeTab === 'courses') {
      loadCourseData();
    } else {
      loadQuizData();
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
  };

  return (
    <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-10 py-4 sm:py-6 md:py-8 space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:gap-4">
        <div className="space-y-1 sm:space-y-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6 text-purple-500" />
            <span className="text-xs sm:text-sm font-medium text-purple-600 uppercase tracking-wide">
              Generation Tracking
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-900">Theo dõi tiến trình tạo nội dung</h1>
          <p className="text-xs sm:text-sm md:text-base text-gray-600">
            Theo dõi chi tiết quá trình AI tạo khóa học và quiz tự động của bạn.
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
          <Button 
            variant="outline" 
            onClick={handleRefresh} 
            disabled={loading}
            className="border-gray-200 text-sm w-full sm:w-auto"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Làm mới
          </Button>
          {activeTab === 'courses' ? (
            <>
              <Link href="/user/my-courses" className="w-full sm:w-auto">
                <Button variant="outline" className="border-gray-200 text-sm w-full">
                  Khóa học của tôi
                </Button>
              </Link>
              <Link href="/user/create-course" className="w-full sm:w-auto">
                <Button className="bg-orange-500 hover:bg-orange-600 text-sm w-full">
                  <Plus className="w-4 h-4 mr-2" />
                  Tạo khóa học mới
                </Button>
              </Link>
            </>
          ) : (
            <>
              <Link href="/user/my-quizzes" className="w-full sm:w-auto">
                <Button variant="outline" className="border-gray-200 text-sm w-full">
                  Quiz của tôi
                </Button>
              </Link>
              <Link href="/user/create-quiz" className="w-full sm:w-auto">
                <Button className="bg-green-500 hover:bg-green-600 text-sm w-full">
                  <Plus className="w-4 h-4 mr-2" />
                  Tạo Quiz mới
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 sm:gap-2 border-b border-gray-200 overflow-x-auto">
        <button
          onClick={() => handleTabChange('courses')}
          className={`flex items-center gap-2 px-4 sm:px-6 py-2 sm:py-3 font-medium transition-all text-sm sm:text-base whitespace-nowrap ${
            activeTab === 'courses'
              ? 'text-orange-600 border-b-2 border-orange-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <BookOpen className="w-5 h-5" />
          Khóa học
        </button>
        <button
          onClick={() => handleTabChange('quizzes')}
          className={`flex items-center gap-2 px-6 py-3 font-medium transition-all ${
            activeTab === 'quizzes'
              ? 'text-green-600 border-b-2 border-green-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <FileQuestion className="w-5 h-5" />
          Quiz
        </button>
      </div>

      {/* Content */}
      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Đang tải dữ liệu...</p>
        </div>
      )}

      {!loading && activeTab === 'courses' && (
        <>
          {courseItems.length === 0 ? (
            <div className="text-center py-12">
              <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">Chưa có tiến trình tạo khóa học nào.</p>
              <Link href="/user/create-course">
                <Button className="bg-orange-500 hover:bg-orange-600">
                  <Plus className="w-4 h-4 mr-2" />
                  Tạo khóa học đầu tiên
                </Button>
              </Link>
            </div>
          ) : (
            <GenerationList
              items={courseItems}
              currentPage={currentPage}
              itemsPerPage={itemsPerPage}
              onPageChange={handlePageChange}
              onItemsPerPageChange={handleItemsPerPageChange}
            />
          )}
        </>
      )}

      {!loading && activeTab === 'quizzes' && (
        <>
          {quizItems.length === 0 ? (
            <div className="text-center py-12">
              <FileQuestion className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">Chưa có tiến trình tạo quiz nào.</p>
              <Link href="/user/create-quiz">
                <Button className="bg-green-500 hover:bg-green-600">
                  <Plus className="w-4 h-4 mr-2" />
                  Tạo quiz đầu tiên
                </Button>
              </Link>
            </div>
          ) : (
            <QuizGenerationList
              items={quizItems}
              currentPage={currentPage}
              itemsPerPage={itemsPerPage}
              onPageChange={handlePageChange}
              onItemsPerPageChange={handleItemsPerPageChange}
            />
          )}
        </>
      )}
    </div>
  );
}

export default function TrackingPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Đang tải...</div>}>
      <TrackingInner />
    </Suspense>
  );
}
