'use client';

import React, { useState, useEffect } from 'react';
import { quizApi } from '@/lib/api/user';
import { FileQuestion, Clock, CheckCircle2, ChevronLeft, ChevronRight, Award } from 'lucide-react';

interface Quiz {
  id: string;
  title: string;
  description?: string;
  is_public?: boolean;
  created_at?: string;
  updated_at?: string;
  question_count?: number;
  duration?: number;
  score?: number;
  completed?: boolean;
}

const ITEMS_PER_PAGE = 9;

export const QuizList: React.FC = () => {
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'my' | 'public'>('my');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    const fetchQuizzes = async () => {
      setLoading(true);
      try {
        const response = await quizApi.getAll();
        const data = response.data as { quizzes?: Quiz[] };
        setQuizzes(data.quizzes || []);
      } catch (error) {
        console.error('Failed to fetch quizzes:', error);
        setQuizzes([]);
      } finally {
        setLoading(false);
      }
    };
    fetchQuizzes();
  }, []);

  const filteredQuizzes = quizzes.filter(quiz => 
    activeTab === 'public' ? quiz.is_public : !quiz.is_public
  );

  const totalPages = Math.ceil(filteredQuizzes.length / ITEMS_PER_PAGE);
  const paginatedQuizzes = filteredQuizzes.slice(
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
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Quiz Của Tôi
            <span className="ml-2 px-2 py-0.5 rounded-full bg-gray-100 text-xs">
              {quizzes.filter(q => !q.is_public).length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('public')}
            className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'public'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Quiz Công Khai
            <span className="ml-2 px-2 py-0.5 rounded-full bg-gray-100 text-xs">
              {quizzes.filter(q => q.is_public).length}
            </span>
          </button>
        </div>
      </div>

      {/* Quiz Grid */}
      <div className="p-6">
        {paginatedQuizzes.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <FileQuestion className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>Chưa có quiz nào</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {paginatedQuizzes.map((quiz) => (
              <div
                key={quiz.id}
                className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer bg-gradient-to-br from-white to-purple-50/30"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 line-clamp-2 mb-1">
                      {quiz.title}
                    </h4>
                    {quiz.description && (
                      <p className="text-xs text-gray-500 line-clamp-2 mt-1">
                        {quiz.description}
                      </p>
                    )}
                  </div>
                  {quiz.is_public && (
                    <span className="ml-2 px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded-full shrink-0">
                      Công khai
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-4 text-xs text-gray-500 mt-3 pt-3 border-t">
                  {quiz.question_count !== undefined && (
                    <div className="flex items-center gap-1">
                      <FileQuestion className="w-3.5 h-3.5" />
                      <span>{quiz.question_count} câu</span>
                    </div>
                  )}
                  {quiz.duration !== undefined && (
                    <div className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{quiz.duration} phút</span>
                    </div>
                  )}
                  {quiz.completed && quiz.score !== undefined && (
                    <div className="flex items-center gap-1 text-purple-600">
                      <Award className="w-3.5 h-3.5" />
                      <span>{quiz.score}%</span>
                    </div>
                  )}
                  {quiz.completed && (
                    <div className="flex items-center gap-1 text-green-600">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Hoàn thành</span>
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
                          ? 'bg-purple-600 text-white'
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
