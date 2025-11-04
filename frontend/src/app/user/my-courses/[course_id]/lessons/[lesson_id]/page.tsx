'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import dynamic from 'next/dynamic';
import { 
  ArrowLeft, 
  CheckCircle2, 
  Circle, 
  Lock,
  Clock,
  BookOpen,
  ChevronRight,
  ChevronLeft,
  FileText,
  Play,
  Trophy
} from 'lucide-react';
import { courseApi } from '@/lib/api/course';
import CourseOutlineSidebar from '@/components/user/course/CourseOutlineSidebar';
import { showToast } from '@/utils/toast';

// Dynamic import for ReactMarkdown (ESM module)
const ReactMarkdown = dynamic(() => import('react-markdown'), { ssr: false });

// API Response Types
interface LessonInfo {
  lesson_id: string;
  title: string;
  finish: boolean;
}

interface CourseFullInfo {
  title: string;
  description: string;
  duration: number;
  roadmap: string | null;
  lesson: LessonInfo[];
  updated_at: string;
}

interface CourseFullInfoResponse {
  status: number;
  info?: CourseFullInfo;
}

interface LessonDetail {
  lesson_id: string;
  course_id: string;
  title: string;
  description: string;
  content: string;
  img_url: string | null;
  finish: boolean;
}

interface LessonDetailResponse {
  status: number;
  lesson?: LessonDetail;
  message?: string;
}

export default function LessonDetailPage() {
  const params = useParams();
  const router = useRouter();
  const courseId = params.course_id as string;
  const lessonId = params.lesson_id as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [courseData, setCourseData] = useState<CourseFullInfo | null>(null);
  const [lessonData, setLessonData] = useState<LessonDetail | null>(null);

  // Load course data for sidebar
  useEffect(() => {
    if (!courseId) return;

    let cancelled = false;
    const loadCourse = async () => {
      try {
        const response = await courseApi.getById(courseId);
        
        // Check if response.data has 'info' property (wrapped) or is the info itself (direct)
        const courseInfo = response.data as any;
        
        if (!cancelled) {
          if (courseInfo && courseInfo.info) {
            // Response is wrapped: { status: 200, info: {...} }
            setCourseData(courseInfo.info);
          } else if (courseInfo && courseInfo.title) {
            // Response is direct CourseFullInfo object
            setCourseData(courseInfo);
          }
        }
      } catch (err) {
        console.error('Error loading course for sidebar:', err);
      }
    };

    loadCourse();
    return () => { cancelled = true; };
  }, [courseId]);

  // Load lesson data
  useEffect(() => {
    if (!courseId || !lessonId) return;

    let cancelled = false;
    const loadLesson = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await courseApi.getLessonDetail(courseId, lessonId);
        
        // The API returns the lesson object directly in response.data
        const lessonFromApi = response.data as LessonDetail;
        
        if (!cancelled) {
          if (lessonFromApi && lessonFromApi.lesson_id) {
            // Response is the lesson object itself
            setLessonData(lessonFromApi);
          } else {
            setError('Không thể tải bài học');
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError('Đã xảy ra lỗi khi tải bài học. Vui lòng thử lại.');
          console.error('Error loading lesson:', err);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    loadLesson();
    return () => { cancelled = true; };
  }, [courseId, lessonId]);

  // Get current lesson index and navigation info
  const currentLessonIndex = courseData?.lesson.findIndex(l => l.lesson_id === lessonId) ?? -1;
  const previousLesson = currentLessonIndex > 0 ? courseData?.lesson[currentLessonIndex - 1] : null;
  const nextLesson = currentLessonIndex >= 0 && currentLessonIndex < (courseData?.lesson.length ?? 0) - 1 
    ? courseData?.lesson[currentLessonIndex + 1] 
    : null;
  const isLastLesson = currentLessonIndex === (courseData?.lesson.length ?? 0) - 1;

  const handleNavigateToTest = () => {
    router.push(`/user/my-courses/${courseId}/lessons/${lessonId}/test`);
  };

  const handleNavigateToFinalTest = () => {
    router.push(`/user/my-courses/${courseId}/final-test`);
  };

  if (loading || !courseData || !lessonData) {
    return (
      <div className="flex h-screen">
        <div className="w-80 bg-slate-800"></div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
            <p className="mt-4 text-gray-600">Đang tải bài học...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen">
        {courseData && (
          <CourseOutlineSidebar
            courseId={courseId}
            courseTitle={courseData.title}
            lessons={courseData.lesson}
            currentLessonId={lessonId}
          />
        )}
        <div className="flex-1 flex items-center justify-center p-8">
          <Card className="p-8 text-center border-red-200 bg-red-50 max-w-md">
            <p className="text-red-700 mb-4">{error}</p>
            <Button 
              onClick={() => router.push(`/user/my-courses/${courseId}`)}
              className="bg-orange-500 hover:bg-orange-600"
            >
              Quay lại khóa học
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar */}
      <CourseOutlineSidebar
        courseId={courseId}
        courseTitle={courseData.title}
        lessons={courseData.lesson}
        currentLessonId={lessonId}
      />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-6 lg:p-10 space-y-8">
          {/* Header */}
          <div className="space-y-5">
            <div className="flex items-center gap-3 text-sm">
              <button 
                onClick={() => router.push(`/user/my-courses/${courseId}`)}
                className="text-slate-600 hover:text-blue-600 transition font-medium"
              >
                {courseData.title}
              </button>
              <ChevronRight className="w-4 h-4 text-slate-400" />
              <span className="text-slate-800 font-medium">
                Lesson {currentLessonIndex + 1}: {lessonData.title}
              </span>
            </div>

            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-3 leading-tight">
                  {lessonData.title}
                </h1>
                {lessonData.description && (
                  <p className="text-lg text-slate-600 leading-relaxed">
                    {lessonData.description}
                  </p>
                )}
              </div>
              {lessonData.finish && (
                <Badge className="bg-emerald-500 text-white shrink-0 px-3 py-1.5">
                  <CheckCircle2 className="w-4 h-4 mr-1.5" />
                  Hoàn thành
                </Badge>
              )}
            </div>
          </div>

          {/* Lesson Content */}
          <Card className="p-8 lg:p-12 bg-white shadow-sm border border-gray-100">
            <div 
              className="prose prose-lg max-w-none
                prose-headings:font-bold prose-headings:text-slate-800
                prose-h1:text-3xl prose-h1:mb-6 prose-h1:mt-8 prose-h1:text-slate-900
                prose-h2:text-2xl prose-h2:mb-5 prose-h2:mt-8 prose-h2:text-slate-800 prose-h2:pb-2 prose-h2:border-b prose-h2:border-slate-200
                prose-h3:text-xl prose-h3:mb-4 prose-h3:mt-6 prose-h3:text-slate-700
                prose-p:text-slate-600 prose-p:leading-relaxed prose-p:mb-4 prose-p:text-base
                prose-a:text-blue-600 prose-a:no-underline hover:prose-a:text-blue-700 hover:prose-a:underline
                prose-strong:text-slate-800 prose-strong:font-semibold
                prose-ul:my-4 prose-ul:list-disc prose-ul:pl-6
                prose-ol:my-4 prose-ol:list-decimal prose-ol:pl-6
                prose-li:text-slate-600 prose-li:mb-2 prose-li:leading-relaxed
                prose-code:text-pink-600 prose-code:bg-pink-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:before:content-[''] prose-code:after:content-['']
                prose-pre:bg-slate-900 prose-pre:text-slate-100 prose-pre:p-5 prose-pre:rounded-lg prose-pre:overflow-x-auto prose-pre:shadow-inner
                prose-blockquote:border-l-4 prose-blockquote:border-blue-400 prose-blockquote:pl-4 prose-blockquote:py-1 prose-blockquote:italic prose-blockquote:text-slate-600 prose-blockquote:bg-blue-50/50
                prose-img:rounded-lg prose-img:shadow-md prose-img:border prose-img:border-slate-200
              "
            >
              <ReactMarkdown>{lessonData.content}</ReactMarkdown>
            </div>
          </Card>

          {/* Action Buttons */}
          <div className="space-y-6">
            {/* Lesson Test */}
            <Card className="p-6 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border border-blue-200/60 shadow-sm">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-4 flex-1">
                  <div className="p-2 bg-blue-100 rounded-full">
                    <BookOpen className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 mb-0.5">Kiểm tra kiến thức</h3>
                    <p className="text-sm text-slate-600">
                      {lessonData.finish 
                        ? 'Bạn đã hoàn thành bài học này' 
                        : 'Hoàn thành bài test để đánh dấu bài học hoàn thành'}
                    </p>
                  </div>
                </div>
                {lessonData.finish ? (
                  <Badge className="bg-emerald-500 text-white px-4 py-2">
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Đã Hoàn Thành
                  </Badge>
                ) : (
                  <Button 
                    onClick={handleNavigateToTest}
                    className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm w-full sm:w-auto min-w-[140px]"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Làm Bài Test
                  </Button>
                )}
              </div>
            </Card>

            {/* Final Test - Show only on last lesson if all completed */}
            {isLastLesson && courseData.lesson.every(l => l.finish) && (
              <Card className="p-6 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 border border-amber-200/60 shadow-sm">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-4 flex-1">
                    <div className="p-2 bg-amber-100 rounded-full">
                      <Trophy className="w-6 h-6 text-amber-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900 mb-0.5">Bài kiểm tra cuối khóa</h3>
                      <p className="text-sm text-slate-600">Hoàn thành để nhận chứng chỉ</p>
                    </div>
                  </div>
                  <Button 
                    onClick={handleNavigateToFinalTest}
                    className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white shadow-sm w-full sm:w-auto min-w-[140px]"
                  >
                    <Trophy className="w-4 h-4 mr-2" />
                    Bài Test
                  </Button>
                </div>
              </Card>
            )}

            {/* Navigation */}
            <div className="flex items-center justify-between gap-4 pt-6 border-t border-slate-200">
              <Button
                variant="outline"
                onClick={() => previousLesson && router.push(`/user/my-courses/${courseId}/lessons/${previousLesson.lesson_id}`)}
                disabled={!previousLesson}
                className="flex-1 sm:flex-none border-slate-300 text-slate-700 hover:bg-slate-50 hover:text-slate-900 disabled:opacity-50"
              >
                <ChevronLeft className="w-4 h-4 mr-2" />
                Trở Về
              </Button>
              
              {nextLesson ? (
                <Button
                  onClick={() => router.push(`/user/my-courses/${courseId}/lessons/${nextLesson.lesson_id}`)}
                  className="flex-1 sm:flex-none bg-blue-600 hover:bg-blue-700 text-white shadow-sm"
                >
                  Tiếp Theo
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              ) : (
                <Button
                  onClick={() => router.push(`/user/my-courses/${courseId}`)}
                  className="flex-1 sm:flex-none bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                >
                  Hoàn thành khóa học
                  <CheckCircle2 className="w-4 h-4 ml-2" />
                </Button>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
