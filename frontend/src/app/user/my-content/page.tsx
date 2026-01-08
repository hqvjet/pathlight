'use client';
import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { BookOpen, FileQuestion, Plus, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

type TabType = 'courses' | 'quizzes';

function MyContentInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('courses');

  useEffect(() => {
    const tabParam = searchParams.get('tab');
    if (tabParam === 'quizzes') {
      setActiveTab('quizzes');
    }
  }, [searchParams]);

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    const url = new URL(window.location.href);
    url.searchParams.set('tab', tab);
    router.push(url.pathname + url.search, { scroll: false });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-purple-50 to-blue-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Nội dung của tôi</h1>
          <p className="text-gray-600">Quản lý khóa học và quiz của bạn</p>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-2 mb-6 border-b border-gray-200">
          <button
            onClick={() => handleTabChange('courses')}
            className={`flex items-center gap-2 px-6 py-3 font-medium transition-all ${
              activeTab === 'courses'
                ? 'text-orange-600 border-b-2 border-orange-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <BookOpen className="w-5 h-5" />
            Khóa học của tôi
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
            Quiz của tôi
          </button>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 mb-6">
          {activeTab === 'courses' ? (
            <>
              <Link href="/user/create-course">
                <Button className="bg-orange-500 hover:bg-orange-600">
                  <Plus className="w-4 h-4 mr-2" />
                  Tạo khóa học mới
                </Button>
              </Link>
              <Link href="/user/generation-tracking">
                <Button variant="outline" className="border-gray-200">
                  <TrendingUp className="w-4 h-4 mr-2" />
                  Theo dõi tiến trình
                </Button>
              </Link>
            </>
          ) : (
            <>
              <Link href="/user/create-quiz">
                <Button className="bg-green-500 hover:bg-green-600">
                  <Plus className="w-4 h-4 mr-2" />
                  Tạo quiz mới
                </Button>
              </Link>
              <Link href="/user/quiz-tracking">
                <Button variant="outline" className="border-gray-200">
                  <TrendingUp className="w-4 h-4 mr-2" />
                  Theo dõi tiến trình
                </Button>
              </Link>
            </>
          )}
        </div>

        {/* Content */}
        <div>
          {activeTab === 'courses' ? (
            <iframe
              src="/user/my-courses"
              className="w-full h-[calc(100vh-300px)] border-0"
              title="My Courses"
            />
          ) : (
            <iframe
              src="/user/my-quizzes"
              className="w-full h-[calc(100vh-300px)] border-0"
              title="My Quizzes"
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default function MyContentPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Đang tải...</div>}>
      <MyContentInner />
    </Suspense>
  );
}
