"use client";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Clock, Zap, Calendar, Hash } from "lucide-react";
import { GenerationItem } from "./GenerationCard";

function getDetailedStatus(item: GenerationItem) {
  const steps = [
    { 
      key: 'vectorized', 
      label: 'Phân tích tài liệu', 
      done: item.vectorized,
      description: 'Vectorize và index tài liệu vào OpenSearch',
      count: null
    },
    { 
      key: 'title_ready', 
      label: 'Tạo kế hoạch khóa học', 
      done: item.title_ready,
      description: 'Sinh tiêu đề, mô tả và roadmap học tập',
      count: item.roadmap_count
    },
    { 
      key: 'lesson_planned', 
      label: 'Lập kế hoạch bài học', 
      done: item.title_ready && item.lessons_planned,
      description: `Xác định số lượng bài học cần tạo${item.lessons_planned ? ` (${item.lessons_planned} bài)` : ''}`,
      count: item.lessons_planned
    },
    { 
      key: 'lessons_ready', 
      label: 'Tạo nội dung bài học', 
      done: item.lessons_ready,
      description: `Sinh nội dung chi tiết cho từng bài học${item.lessons_count ? ` (${item.lessons_count}/${item.lessons_planned || 0} bài hoàn thành)` : ''}`,
      count: item.lessons_count
    },
  ];
  
  const completedSteps = steps.filter(s => s.done).length;
  const isComplete = completedSteps === steps.length;
  const currentStep = steps.find(s => !s.done);
  const progressPercent = (completedSteps / steps.length) * 100;
  
  // Use final_ready as overall status, but also check if all steps are done
  let overallStatus: 'done' | 'processing' | 'error' = 'processing';
  if (isComplete || item.final_ready === true) {
    overallStatus = 'done';
  } else if (item.final_ready === false && item.progress?.includes('error')) {
    overallStatus = 'error';
  }
  
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
  if (!item) return null;

  const status = getDetailedStatus(item);
  const updated = item.updated_at ? new Date(item.updated_at).toLocaleString('vi-VN') : "Chưa có thông tin";

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
            {item.title && (
              <div>
                <h3 className="text-lg font-bold text-gray-900">{item.title}</h3>
              </div>
            )}
            {item.description && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-700">{item.description}</p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Hash className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Course ID:</span>
              <code className="text-xs font-mono bg-white px-2 py-1 rounded border truncate max-w-[200px]" title={item.course_id}>
                {item.course_id}
              </code>
            </div>
            {item.lessons_planned && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Số bài học:</span>
                <span className="text-sm font-medium text-orange-600">
                  {item.lessons_count || 0}/{item.lessons_planned} bài
                </span>
              </div>
            )}
            {item.roadmap_count && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Roadmap:</span>
                <span className="text-sm font-medium">{item.roadmap_count} bước</span>
              </div>
            )}
            {item.final_count !== undefined && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Câu hỏi kiểm tra:</span>
                <span className="text-sm font-medium text-purple-600">{item.final_count} câu</span>
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
              <p className="text-sm text-red-600 mt-1">Vui lòng thử lại hoặc liên hệ hỗ trợ</p>
            </div>
          )}

          {/* Progress Text */}
          {item.progress && (
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-blue-800 mb-2">Trạng thái hiện tại</h4>
              <p className="text-blue-700 italic">&ldquo;{item.progress}&rdquo;</p>
            </div>
          )}

          {/* Detailed Steps */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-gray-900">Chi tiết các bước</h3>
            <div className="space-y-3">
              {status.steps.map((step, index) => {
                const isActive = !status.isComplete && status.currentStep?.key === step.key;
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
