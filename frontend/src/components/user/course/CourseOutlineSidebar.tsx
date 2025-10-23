'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  CheckCircle2, 
  Lock, 
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Menu,
  X
} from 'lucide-react';

interface LessonInfo {
  lesson_id: string;
  title: string;
  finish: boolean;
}

interface CourseOutlineSidebarProps {
  courseId: string;
  courseTitle: string;
  lessons: LessonInfo[];
  currentLessonId: string;
  onLessonClick?: (lessonId: string) => void;
}

export default function CourseOutlineSidebar({
  courseId,
  courseTitle,
  lessons,
  currentLessonId,
  onLessonClick
}: CourseOutlineSidebarProps) {
  const router = useRouter();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const handleLessonClick = (lesson: LessonInfo, index: number) => {
    // Check if lesson is locked (previous lesson not completed)
    if (index > 0 && !lessons[index - 1].finish) {
      return; // Don't navigate if locked
    }

    if (onLessonClick) {
      onLessonClick(lesson.lesson_id);
    } else {
      router.push(`/user/my-courses/${courseId}/lessons/${lesson.lesson_id}`);
    }
    setIsMobileOpen(false);
  };

  const completedCount = lessons.filter(l => l.finish).length;
  const progressPercent = lessons.length > 0 ? Math.round((completedCount / lessons.length) * 100) : 0;

  const SidebarContent = () => (
    <div className="h-full flex flex-col bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 text-white shadow-2xl">
      {/* Header */}
      <div className="p-6 border-b border-slate-700/60">
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0 shadow-lg">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            {!isCollapsed && (
              <div className="flex-1 min-w-0">
                <h2 className="text-sm font-semibold text-slate-200 mb-1">Nội dung khóa học</h2>
                <p className="text-xs text-slate-400 line-clamp-2">{courseTitle}</p>
              </div>
            )}
          </div>
          
          {/* Desktop collapse button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden lg:flex text-slate-400 hover:text-white hover:bg-slate-700/60 shrink-0"
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </Button>

          {/* Mobile close button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsMobileOpen(false)}
            className="lg:hidden text-gray-400 hover:text-white hover:bg-slate-700 shrink-0"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Progress */}
        {!isCollapsed && (
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Tiến độ</span>
              <span className="font-bold text-blue-400">{progressPercent}%</span>
            </div>
            <div className="h-2.5 bg-slate-700/50 rounded-full overflow-hidden shadow-inner">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 transition-all duration-500 shadow-sm"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <p className="text-xs text-slate-400">
              {completedCount} / {lessons.length} bài đã hoàn thành
            </p>
          </div>
        )}
      </div>

      {/* Lessons List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-800">
        <div className={`${isCollapsed ? 'p-2' : 'p-4'} space-y-2`}>
          {lessons.map((lesson, index) => {
            const isCompleted = lesson.finish;
            const isCurrent = lesson.lesson_id === currentLessonId;
            const isLocked = index > 0 && !lessons[index - 1].finish;

            return (
              <button
                key={lesson.lesson_id}
                onClick={() => handleLessonClick(lesson, index)}
                disabled={isLocked}
                className={`
                  w-full text-left transition-all duration-200
                  ${isCollapsed ? 'p-3' : 'p-4'}
                  rounded-lg border
                  ${isCurrent 
                    ? 'bg-gradient-to-r from-blue-600/30 to-indigo-600/30 border-blue-400 shadow-lg shadow-blue-500/20' 
                    : isCompleted
                    ? 'bg-slate-700/40 border-emerald-500/40 hover:bg-slate-700/60 hover:border-emerald-500/60'
                    : isLocked
                    ? 'bg-slate-800/30 border-slate-700/50 opacity-50 cursor-not-allowed'
                    : 'bg-slate-800/40 border-slate-600/50 hover:bg-slate-700/50 hover:border-slate-500'
                  }
                `}
              >
                <div className="flex items-center gap-3">
                  {/* Icon/Number */}
                  <div className="shrink-0">
                    {isCompleted ? (
                      <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center shadow-sm">
                        <CheckCircle2 className="w-5 h-5 text-white" />
                      </div>
                    ) : isLocked ? (
                      <div className="w-8 h-8 rounded-full bg-slate-700/60 flex items-center justify-center">
                        <Lock className="w-4 h-4 text-slate-500" />
                      </div>
                    ) : (
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shadow-sm ${
                        isCurrent 
                          ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white' 
                          : 'bg-slate-700/60 text-slate-300'
                      }`}>
                        {index + 1}
                      </div>
                    )}
                  </div>

                  {/* Lesson Info */}
                  {!isCollapsed && (
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-medium line-clamp-2 ${
                        isCurrent ? 'text-white' : 
                        isCompleted ? 'text-emerald-300' : 
                        isLocked ? 'text-slate-500' : 'text-slate-300'
                      }`}>
                        Bài {index + 1}: {lesson.title}
                      </p>
                      {isCurrent && (
                        <Badge className="mt-1.5 bg-blue-500/80 text-white text-xs px-2 py-0.5">
                          Đang học
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
              </button>
            );
          })}

          {/* Final Test */}
          {!isCollapsed && (
            <div className={`p-4 rounded-lg border-2 mt-4 ${
              completedCount === lessons.length
                ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-purple-500'
                : 'bg-slate-800/50 border-slate-700 opacity-60'
            }`}>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center shrink-0">
                  <BookOpen className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">Final Test</p>
                  {completedCount === lessons.length ? (
                    <Badge className="mt-1 bg-green-500 text-white text-xs">
                      Ready
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="mt-1 border-slate-600 text-gray-400 text-xs">
                      <Lock className="w-3 h-3 mr-1" />
                      Locked
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Back to Course Button */}
      {!isCollapsed && (
        <div className="p-4 border-t border-slate-700/60">
          <Button
            className="w-full justify-center bg-slate-700 hover:bg-slate-600 text-white border border-slate-600 hover:border-slate-500 transition-all shadow-sm"
            onClick={() => router.push(`/user/my-courses/${courseId}`)}
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Về Tổng Quan
          </Button>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <Button
        onClick={() => setIsMobileOpen(true)}
        className="lg:hidden fixed top-20 left-4 z-40 bg-slate-800 hover:bg-slate-700 text-white shadow-lg"
        size="sm"
      >
        <Menu className="w-4 h-4 mr-2" />
        Lessons
      </Button>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <div className={`
        lg:hidden fixed inset-y-0 left-0 w-80 z-50 transform transition-transform duration-300
        ${isMobileOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <SidebarContent />
      </div>

      {/* Desktop Sidebar */}
      <div className={`
        hidden lg:block sticky top-0 h-screen transition-all duration-300
        ${isCollapsed ? 'w-20' : 'w-80'}
      `}>
        <SidebarContent />
      </div>
    </>
  );
}
