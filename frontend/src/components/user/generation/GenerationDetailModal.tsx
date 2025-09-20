"use client";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle, Clock, Zap, Calendar, User, Hash } from "lucide-react";
import { GenerationItem } from "./GenerationCard";

function getDetailedStatus(item: GenerationItem) {
  const steps = [
    { 
      key: 'vectorized', 
      label: 'Phân tích tài liệu', 
      done: item.vectorized,
      description: 'Vectorize và index tài liệu vào OpenSearch'
    },
    { 
      key: 'title_ready', 
      label: 'Tạo kế hoạch khóa học', 
      done: item.title_ready,
      description: 'Sinh tiêu đề, mô tả và roadmap học tập'
    },
    { 
      key: 'lessons_ready', 
      label: 'Tạo nội dung bài học', 
      done: item.lessons_ready,
      description: 'Sinh nội dung chi tiết cho từng bài học'
    },
    { 
      key: 'final_ready', 
      label: 'Tạo bài kiểm tra cuối', 
      done: item.final_ready,
      description: 'Sinh câu hỏi và bài kiểm tra tổng kết'
    },
  ];
  
  const completedSteps = steps.filter(s => s.done).length;
  const isComplete = completedSteps === steps.length;
  const currentStep = steps.find(s => !s.done);
  const progressPercent = (completedSteps / steps.length) * 100;
  
  return { steps, completedSteps, isComplete, currentStep, progressPercent };
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
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Hash className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Course ID:</span>
              <code className="text-sm font-mono bg-white px-2 py-1 rounded border">
                {item.course_id}
              </code>
            </div>
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">User ID:</span>
              <span className="text-sm font-medium">{item.user_id || "N/A"}</span>
            </div>
            <div className="flex items-center gap-2 md:col-span-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Cập nhật lần cuối:</span>
              <span className="text-sm font-medium">{updated}</span>
            </div>
          </div>

          {/* Overall Progress */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">Tiến độ tổng quan</h3>
              {status.isComplete ? (
                <Badge className="bg-emerald-500 text-white">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Hoàn thành
                </Badge>
              ) : (
                <Badge variant="outline" className="border-orange-200 text-orange-600">
                  <Clock className="w-3 h-3 mr-1" />
                  Đang xử lý ({status.completedSteps}/{status.steps.length})
                </Badge>
              )}
            </div>
            <div className="space-y-2">
              <Progress value={status.progressPercent} className="h-3" />
              <p className="text-sm text-gray-600 text-center">
                {status.progressPercent.toFixed(0)}% hoàn thành
              </p>
            </div>
          </div>

          {/* Current Activity */}
          {!status.isComplete && status.currentStep && (
            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-5 h-5 text-orange-500" />
                <h4 className="font-semibold text-orange-800">Đang thực hiện</h4>
              </div>
              <p className="text-orange-700 font-medium">{status.currentStep.label}</p>
              <p className="text-sm text-orange-600 mt-1">{status.currentStep.description}</p>
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
                        ? "bg-emerald-50 border-emerald-200"
                        : isActive
                        ? "bg-orange-50 border-orange-200 border-dashed"
                        : "bg-gray-50 border-gray-200"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`mt-0.5 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        step.done
                          ? "bg-emerald-500 text-white"
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
                              ? "text-emerald-800"
                              : isActive
                              ? "text-orange-800"
                              : "text-gray-600"
                          }`}>
                            {step.label}
                          </h4>
                          {step.done && (
                            <Badge variant="outline" className="border-emerald-300 text-emerald-700 text-xs">
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
                            ? "text-emerald-600"
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
