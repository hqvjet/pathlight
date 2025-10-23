'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { courseApi } from '@/lib/api/course';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { 
  ArrowLeft, 
  BookOpen, 
  CheckCircle2, 
  Circle, 
  Clock, 
  Lock,
  Play,
  Trophy,
  Calendar,
  ListChecks
} from 'lucide-react';

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
  message?: string;
}

export default function CourseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const courseId = params.course_id as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [courseData, setCourseData] = useState<CourseFullInfo | null>(null);

  useEffect(() => {
    if (!courseId) return;

    let cancelled = false;
    const loadCourse = async () => {
      setLoading(true);
      setError(null);
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
          } else {
            setError('Không thể tải thông tin khóa học');
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError('Đã xảy ra lỗi khi tải khóa học. Vui lòng thử lại.');
          console.error('Error loading course:', err);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    loadCourse();
    return () => { cancelled = true; };
  }, [courseId]);

  // Calculate progress
  const completedLessons = courseData?.lesson.filter(l => l.finish).length || 0;
  const totalLessons = courseData?.lesson.length || 0;
  const progressPercent = totalLessons > 0 ? Math.round((completedLessons / totalLessons) * 100) : 0;

  // Get current lesson (first incomplete or first lesson)
  const currentLesson = courseData?.lesson.find(l => !l.finish) || courseData?.lesson[0];

  // Format duration
  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
    }
    return `${mins}m`;
  };

  // Format date
  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  // Parse roadmap
  const roadmapItems = courseData?.roadmap 
    ? courseData.roadmap.split(';').map(item => item.trim()).filter(Boolean)
    : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-purple-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-8">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
              <p className="mt-4 text-gray-600">Đang tải khóa học...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !courseData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-purple-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-8">
          <Button
            variant="outline"
            onClick={() => router.push('/user/my-courses')}
            className="mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Quay lại
          </Button>
          <Card className="p-8 text-center border-red-200 bg-red-50">
            <p className="text-red-700">{error}</p>
            <Button 
              onClick={() => router.push('/user/my-courses')}
              className="mt-4 bg-orange-500 hover:bg-orange-600"
            >
              Về trang khóa học
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-8 space-y-6">
        {/* Back Button */}
        <Button
          variant="outline"
          onClick={() => router.push('/user/my-courses')}
          className="hover:bg-white"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Quay lại khóa học của tôi
        </Button>

        {/* Course Header Card */}
        <Card className="p-8 bg-white shadow-lg border-0">
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Left: Course Info */}
            <div className="lg:col-span-2 space-y-6">
              {/* Title */}
              <div>
                <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
                  {courseData.title}
                </h1>
                <p className="text-gray-600 leading-relaxed text-lg">
                  {courseData.description}
                </p>
              </div>

              {/* Course Meta */}
              <div className="flex flex-wrap gap-6 text-sm">
                <div className="flex items-center gap-2 text-gray-700">
                  <BookOpen className="w-5 h-5 text-orange-500" />
                  <span className="font-medium">{totalLessons} bài học</span>
                </div>
                <div className="flex items-center gap-2 text-gray-700">
                  <Clock className="w-5 h-5 text-orange-500" />
                  <span className="font-medium">{formatDuration(courseData.duration)}</span>
                </div>
                {courseData.updated_at && (
                  <div className="flex items-center gap-2 text-gray-700">
                    <Calendar className="w-5 h-5 text-orange-500" />
                    <span className="font-medium">{formatDate(courseData.updated_at)}</span>
                  </div>
                )}
              </div>

              {/* Progress Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Tiến trình học
                  </span>
                  <span className="text-2xl font-bold text-orange-600">
                    {progressPercent}%
                  </span>
                </div>
                <Progress value={progressPercent} className="h-3" />
                <p className="text-sm text-gray-600">
                  {completedLessons}/{totalLessons} bài học đã hoàn thành
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-4 pt-4">
                <Button 
                  className="bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600 text-white shadow-lg shadow-orange-500/30 px-8"
                  onClick={() => {
                    if (currentLesson) {
                      router.push(`/user/my-courses/${courseId}/lessons/${currentLesson.lesson_id}`);
                    }
                  }}
                >
                  <Play className="w-4 h-4 mr-2" />
                  {completedLessons === 0 ? 'Bắt đầu học' : 'Tiếp tục học'}
                </Button>
                {progressPercent === 100 && (
                  <Button 
                    variant="outline"
                    className="border-orange-500 text-orange-600 hover:bg-orange-50"
                  >
                    <Trophy className="w-4 h-4 mr-2" />
                    Làm bài kiểm tra cuối khóa
                  </Button>
                )}
              </div>
            </div>

            {/* Right: Course Stats Card */}
            <div className="space-y-4">
              <Card className="p-6 bg-gradient-to-br from-orange-50 to-purple-50 border-orange-100">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <ListChecks className="w-5 h-5 text-orange-500" />
                  Tổng quan
                </h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 text-sm">Tổng bài học</span>
                    <span className="font-bold text-gray-900">{totalLessons}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 text-sm">Đã hoàn thành</span>
                    <span className="font-bold text-green-600">{completedLessons}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 text-sm">Còn lại</span>
                    <span className="font-bold text-orange-600">{totalLessons - completedLessons}</span>
                  </div>
                  <div className="pt-3 border-t border-orange-200">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600 text-sm">Thời lượng</span>
                      <span className="font-bold text-gray-900">{formatDuration(courseData.duration)}</span>
                    </div>
                  </div>
                </div>
              </Card>

              {progressPercent === 100 && (
                <Card className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
                  <div className="text-center">
                    <Trophy className="w-12 h-12 text-green-600 mx-auto mb-3" />
                    <h3 className="font-bold text-green-900 mb-2">
                      Hoàn thành khóa học!
                    </h3>
                    <p className="text-sm text-green-700">
                      Chúc mừng bạn đã hoàn thành tất cả bài học
                    </p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        </Card>

        {/* Roadmap Section */}
        {roadmapItems.length > 0 && (
          <Card className="p-8 bg-white shadow-md border-0">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-400 to-pink-500 flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-white" />
              </div>
              Lộ Trình Học
            </h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {roadmapItems.map((item, index) => (
                <div 
                  key={index}
                  className="flex items-start gap-3 p-4 rounded-lg bg-gradient-to-r from-orange-50 to-purple-50 border border-orange-100 hover:shadow-md transition-shadow"
                >
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-orange-400 to-pink-500 text-white flex items-center justify-center text-sm font-bold shrink-0">
                    {index + 1}
                  </div>
                  <p className="text-sm text-gray-700 leading-relaxed flex-1">{item}</p>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Lessons List */}
        <Card className="p-8 bg-white shadow-md border-0">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-400 to-pink-500 flex items-center justify-center">
              <ListChecks className="w-5 h-5 text-white" />
            </div>
            Bài Học
          </h2>

          <div className="space-y-3">
            {courseData.lesson.map((lesson, index) => {
              const isCompleted = lesson.finish;
              const isCurrent = currentLesson?.lesson_id === lesson.lesson_id;
              const isLocked = index > 0 && !courseData.lesson[index - 1].finish;

              return (
                <div
                  key={lesson.lesson_id}
                  className={`
                    flex items-center gap-4 p-5 rounded-xl border-2 transition-all
                    ${isCompleted ? 'bg-green-50 border-green-200 hover:shadow-md' : ''}
                    ${isCurrent && !isCompleted ? 'bg-orange-50 border-orange-300 shadow-md' : ''}
                    ${isLocked ? 'bg-gray-50 border-gray-200 opacity-60' : ''}
                    ${!isCompleted && !isCurrent && !isLocked ? 'bg-white border-gray-200 hover:border-orange-200 hover:shadow-md' : ''}
                    cursor-pointer
                  `}
                  onClick={() => {
                    if (!isLocked) {
                      router.push(`/user/my-courses/${courseId}/lessons/${lesson.lesson_id}`);
                    }
                  }}
                >
                  {/* Lesson Number & Icon */}
                  <div className="shrink-0">
                    {isCompleted ? (
                      <div className="w-12 h-12 rounded-full bg-green-500 text-white flex items-center justify-center shadow-md">
                        <CheckCircle2 className="w-6 h-6" />
                      </div>
                    ) : isLocked ? (
                      <div className="w-12 h-12 rounded-full bg-gray-300 text-gray-500 flex items-center justify-center">
                        <Lock className="w-5 h-5" />
                      </div>
                    ) : (
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg shadow-md ${
                        isCurrent 
                          ? 'bg-gradient-to-br from-orange-400 to-pink-500 text-white' 
                          : 'bg-white text-gray-700 border-2 border-gray-300'
                      }`}>
                        {index + 1}
                      </div>
                    )}
                  </div>

                  {/* Lesson Title */}
                  <div className="flex-1 min-w-0">
                    <h3 className={`font-semibold mb-1 ${
                      isCompleted ? 'text-green-900' : 
                      isCurrent ? 'text-orange-900' : 
                      isLocked ? 'text-gray-500' : 'text-gray-900'
                    }`}>
                      Bài {index + 1}: {lesson.title}
                    </h3>
                    {isCurrent && !isCompleted && (
                      <p className="text-sm text-orange-600 font-medium">Bài học hiện tại</p>
                    )}
                  </div>

                  {/* Status Badge */}
                  <div className="shrink-0">
                    {isCompleted ? (
                      <Badge className="bg-green-500 text-white">
                        <CheckCircle2 className="w-3 h-3 mr-1" />
                        Hoàn thành
                      </Badge>
                    ) : isLocked ? (
                      <Badge variant="outline" className="border-gray-300 text-gray-500">
                        <Lock className="w-3 h-3 mr-1" />
                        Khóa
                      </Badge>
                    ) : isCurrent ? (
                      <Badge className="bg-orange-500 text-white">
                        <Circle className="w-3 h-3 mr-1 fill-current" />
                        Đang học
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="border-gray-300 text-gray-600">
                        Chưa học
                      </Badge>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>
    </div>
  );
}
