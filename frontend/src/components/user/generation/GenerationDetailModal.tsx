"use client";
import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Clock, Zap, Calendar, ChevronDown, ChevronUp, BookOpen } from "lucide-react";
import { GenerationItem } from "./GenerationCard";

function getDetailedStatus(item: GenerationItem) {
  const steps = [
    { 
      key: 'vectorization', 
      label: 'Phân tích tài liệu', 
      done: item.vectorization_status === 'done',
      description: 'Vectorize và index tài liệu vào OpenSearch',
      count: null
    },
    { 
      key: 'planning', 
      label: 'Tạo kế hoạch khóa học', 
      done: item.planning_status === 'done',
      description: `Sinh tiêu đề, mô tả và roadmap học tập${item.planning_roadmap_count ? ` (${item.planning_roadmap_count} modules)` : ''}`,
      count: item.planning_roadmap_count
    },
    { 
      key: 'lessons', 
      label: 'Tạo nội dung bài học', 
      done: item.lessons_status === 'done',
      description: `Sinh nội dung chi tiết cho từng bài học${item.lessons_completed && item.lessons_total ? ` (${item.lessons_completed}/${item.lessons_total} bài hoàn thành)` : ''}`,
      count: item.lessons_completed && item.lessons_total ? `${item.lessons_completed}/${item.lessons_total}` : item.lessons_total
    },
    { 
      key: 'tests', 
      label: 'Tạo câu hỏi kiểm tra', 
      done: item.tests_status === 'done',
      description: `Sinh câu hỏi trắc nghiệm cho từng bài học${item.tests_completed && item.tests_total ? ` (${item.tests_completed}/${item.tests_total} bài)` : ''}`,
      count: item.tests_completed && item.tests_total ? `${item.tests_completed}/${item.tests_total}` : item.tests_total
    },
  ];
  
  const completedSteps = steps.filter(s => s.done).length;
  const isComplete = item.overall_status === 'done';
  const currentStep = steps.find(s => !s.done);
  const progressPercent = (completedSteps / steps.length) * 100;
  const overallStatus = item.overall_status || 'processing';
  
  return { steps, completedSteps, isComplete, currentStep, progressPercent, overallStatus };
}

export default function GenerationDetailModal({
  item,
  isOpen,
  onClose,
}: {
  item: GenerationItem | null;
  isOpen: boolean;
  onClose: () => void;
}) {
  const [isLessonsExpanded, setIsLessonsExpanded] = useState(false);
  
  if (!item) return null;

  const status = getDetailedStatus(item);
  const updated = (item.updated_at || item.last_updated) ? new Date(item.updated_at || item.last_updated || '').toLocaleString('vi-VN') : "Chưa có thông tin";

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-400 via-pink-400 to-purple-500 text-white flex items-center justify-center font-bold text-lg shadow-md">
              {item.course_id?.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <DialogTitle className="text-xl font-bold text-gray-900">
                Chi tiết quá trình tạo khóa học
              </DialogTitle>
              <DialogDescription className="text-gray-600">
                Theo dõi từng bước trong quá trình tạo khóa học
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6">
          {/* Course Info */}
          <div className="space-y-3">
            {item.planning_course_title && (
              <div>
                <h3 className="text-lg font-bold text-gray-900">{item.planning_course_title}</h3>
              </div>
            )}
            {item.description && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-700">{item.description}</p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            {item.planning_roadmap_count && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Roadmap:</span>
                <span className="text-sm font-medium">{item.planning_roadmap_count} modules</span>
              </div>
            )}
            {item.lessons_total && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Số bài học:</span>
                <span className="text-sm font-medium text-orange-600">
                  {item.lessons_completed || 0}/{item.lessons_total} bài
                </span>
              </div>
            )}
            {item.tests_total !== undefined && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Câu hỏi kiểm tra:</span>
                <span className="text-sm font-medium text-purple-600">{item.tests_total} bài</span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Cập nhật:</span>
              <span className="text-sm font-medium">{updated}</span>
            </div>
          </div>

          {/* Overall Progress */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">Tiến độ tổng quan</h3>
              {status.overallStatus === 'done' ? (
                <Badge className="bg-green-500 text-white">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Hoàn thành
                </Badge>
              ) : status.overallStatus === 'error' ? (
                <Badge variant="outline" className="border-red-200 text-red-600">
                  <Clock className="w-3 h-3 mr-1" />
                  Lỗi
                </Badge>
              ) : (
                <Badge variant="outline" className="border-orange-200 text-orange-600">
                  <Clock className="w-3 h-3 mr-1" />
                  Đang xử lý ({status.completedSteps}/{status.steps.length})
                </Badge>
              )}
            </div>
            <div className="space-y-2">
              <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-500 ${
                    status.overallStatus === 'done'
                      ? 'bg-gradient-to-r from-green-500 to-emerald-600' 
                      : status.overallStatus === 'error'
                      ? 'bg-gradient-to-r from-red-500 to-red-600'
                      : 'bg-gradient-to-r from-orange-500 to-orange-600'
                  }`}
                  style={{ width: `${status.progressPercent}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 text-center">
                {status.progressPercent.toFixed(0)}% hoàn thành
              </p>
            </div>
          </div>

          {/* Current Activity */}
          {status.overallStatus === 'processing' && status.currentStep && (
            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-5 h-5 text-orange-600" />
                <h4 className="font-semibold text-orange-800">Đang thực hiện</h4>
              </div>
              <p className="text-orange-700 font-medium">{status.currentStep.label}</p>
              <p className="text-sm text-orange-600 mt-1">{status.currentStep.description}</p>
            </div>
          )}
          {status.overallStatus === 'error' && (
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-5 h-5 text-red-600" />
                <h4 className="font-semibold text-red-800">Lỗi xảy ra</h4>
              </div>
              <p className="text-red-700 font-medium">Quá trình tạo khóa học gặp sự cố</p>
              {item.error_message && (
                <p className="text-sm text-red-600 mt-2 italic">&ldquo;{item.error_message}&rdquo;</p>
              )}
              <p className="text-sm text-red-600 mt-1">Vui lòng thử lại hoặc liên hệ hỗ trợ</p>
            </div>
          )}

          {/* Detailed Steps */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-gray-900">Chi tiết các bước</h3>
            <div className="space-y-3">
              {status.steps.map((step, index) => {
                const isActive = !status.isComplete && status.currentStep?.key === step.key;
                const isLessonsStep = step.key === 'lessons';
                const hasLessons = isLessonsStep && item.lessons_list && item.lessons_list.length > 0;
                
                return (
                  <div
                    key={step.key}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      step.done
                        ? "bg-green-50 border-green-200"
                        : isActive
                        ? "bg-orange-50 border-orange-200 border-dashed"
                        : "bg-gray-50 border-gray-200"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`mt-0.5 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        step.done
                          ? "bg-green-500 text-white"
                          : isActive
                          ? "bg-orange-500 text-white"
                          : "bg-gray-300 text-gray-600"
                      }`}>
                        {step.done ? <CheckCircle className="w-4 h-4" /> : index + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className={`font-semibold ${
                            step.done
                              ? "text-green-800"
                              : isActive
                              ? "text-orange-800"
                              : "text-gray-600"
                          }`}>
                            {step.label}
                          </h4>
                          {step.done && (
                            <Badge variant="outline" className="border-green-300 text-green-700 text-xs">
                              Hoàn thành
                            </Badge>
                          )}
                          {isActive && (
                            <Badge variant="outline" className="border-orange-300 text-orange-700 text-xs">
                              Đang thực hiện
                            </Badge>
                          )}
                        </div>
                        <p className={`text-sm ${
                          step.done
                            ? "text-green-600"
                            : isActive
                            ? "text-orange-600"
                            : "text-gray-500"
                        }`}>
                          {step.description}
                        </p>
                        
                        {/* Lessons List Expandable Section */}
                        {hasLessons && (
                          <div className="mt-3">
                            <button
                              onClick={() => setIsLessonsExpanded(!isLessonsExpanded)}
                              className="flex items-center gap-2 text-sm font-medium text-green-700 hover:text-green-800 transition-colors"
                            >
                              <BookOpen className="w-4 h-4" />
                              <span>
                                Xem danh sách bài học ({item.lessons_list?.length} bài)
                              </span>
                              {isLessonsExpanded ? (
                                <ChevronUp className="w-4 h-4" />
                              ) : (
                                <ChevronDown className="w-4 h-4" />
                              )}
                            </button>
                            
                            {isLessonsExpanded && (
                              <div className="mt-3 space-y-2 pl-2 border-l-2 border-green-300">
                                {item.lessons_list?.map((lesson, idx) => (
                                  <div
                                    key={lesson.id}
                                    className="flex items-start gap-2 p-2 bg-white rounded border border-green-100 hover:border-green-200 transition-colors"
                                  >
                                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-700 flex items-center justify-center text-xs font-bold">
                                      {idx + 1}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <p className="text-sm font-medium text-gray-900 line-clamp-2">
                                        {lesson.title}
                                      </p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
