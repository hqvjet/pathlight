'use client';

import React, { useState, useEffect } from 'react';
import { courseApi } from '@/lib/api/user';
import { BookOpen, Clock, CheckCircle2, ChevronLeft, ChevronRight } from 'lucide-react';

interface Course {
  id: string;
  title: string;
  description?: string;
  is_public?: boolean;
  created_at?: string;
  updated_at?: string;
  lesson_count?: number;
  duration?: number;
  progress?: number;
}

const ITEMS_PER_PAGE = 9;

export const CourseList: React.FC = () => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'my' | 'public'>('my');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    const fetchCourses = async () => {
      setLoading(true);
      try {
        const response = await courseApi.getAll();
        const data = response.data as { courses?: Course[] };
        setCourses(data.courses || []);
      } catch (error) {
        console.error('Failed to fetch courses:', error);
        setCourses([]);
      } finally {
        setLoading(false);
      }
    };
    fetchCourses();
  }, []);

  const filteredCourses = courses.filter(course => 
    activeTab === 'public' ? course.is_public : !course.is_public
  );

  const totalPages = Math.ceil(filteredCourses.length / ITEMS_PER_PAGE);
  const paginatedCourses = filteredCourses.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  // Reset to page 1 when switching tabs
  useEffect(() => {
    setCurrentPage(1);
  }, [activeTab]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl border p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-40 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border">
      {/* Tabs */}
      <div className="border-b px-6">
        <div className="flex gap-6">
          <button
            onClick={() => setActiveTab('my')}
            className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'my'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Khóa Học Của Tôi
            <span className="ml-2 px-2 py-0.5 rounded-full bg-gray-100 text-xs">
              {courses.filter(c => !c.is_public).length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('public')}
            className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'public'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Khóa Học Công Khai
            <span className="ml-2 px-2 py-0.5 rounded-full bg-gray-100 text-xs">
              {courses.filter(c => c.is_public).length}
            </span>
          </button>
        </div>
      </div>

      {/* Course Grid */}
      <div className="p-6">
        {paginatedCourses.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <BookOpen className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>Chưa có khóa học nào</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {paginatedCourses.map((course) => (
              <div
                key={course.id}
                className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer bg-gradient-to-br from-white to-gray-50"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 line-clamp-2 mb-1">
                      {course.title}
                    </h4>
                    {course.description && (
                      <p className="text-xs text-gray-500 line-clamp-2 mt-1">
                        {course.description}
                      </p>
                    )}
                  </div>
                  {course.is_public && (
                    <span className="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full shrink-0">
                      Công khai
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-4 text-xs text-gray-500 mt-3 pt-3 border-t">
                  {course.lesson_count !== undefined && (
                    <div className="flex items-center gap-1">
                      <BookOpen className="w-3.5 h-3.5" />
                      <span>{course.lesson_count} bài</span>
                    </div>
                  )}
                  {course.duration !== undefined && (
                    <div className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{Math.round(course.duration / 60)} phút</span>
                    </div>
                  )}
                  {course.progress !== undefined && course.progress > 0 && (
                    <div className="flex items-center gap-1 text-green-600">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{course.progress}%</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6 pt-6 border-t">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-2 rounded-lg border hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            
            <div className="flex items-center gap-1">
              {[...Array(totalPages)].map((_, i) => {
                const pageNum = i + 1;
                // Show first, last, current, and adjacent pages
                if (
                  pageNum === 1 ||
                  pageNum === totalPages ||
                  Math.abs(pageNum - currentPage) <= 1
                ) {
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`min-w-[32px] h-8 px-2 rounded-lg text-sm font-medium transition-colors ${
                        currentPage === pageNum
                          ? 'bg-blue-600 text-white'
                          : 'hover:bg-gray-100 text-gray-700'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                } else if (
                  pageNum === currentPage - 2 ||
                  pageNum === currentPage + 2
                ) {
                  return (
                    <span key={pageNum} className="px-2 text-gray-400">
                      ...
                    </span>
                  );
                }
                return null;
              })}
            </div>

            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-2 rounded-lg border hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
