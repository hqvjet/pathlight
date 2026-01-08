"use client";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Clock, Zap, Calendar, Hash, Target } from "lucide-react";
import { QuizGenerationItem } from "./QuizGenerationList";

function getDetailedStatus(item: QuizGenerationItem) {
  const steps = [
    { 
      key: 'khoi_tao', 
      label: 'Khởi tạo Quiz', 
      done: item.plan_ready ?? item.title_ready ?? false,
      description: 'Tạo tiêu đề, tổng quan và lập kế hoạch quiz',
      count: item.ideas_count
    },
    { 
      key: 'questions', 
      label: 'Tạo câu hỏi', 
      done: item.questions_ready ?? item.cards_ready ?? false,
      description: `Sinh câu hỏi và đáp án chi tiết${item.questions_count ? ` (${item.questions_count} câu)` : ''}`,
      count: item.questions_count
    },
    { 
      key: 'hoan_thien', 
      label: 'Hoàn thiện và xuất bản', 
      done: item.status === 'completed',
      description: 'Kiểm tra chất lượng và xuất bản quiz',
      count: null
    },
  ];
  
  const completedSteps = steps.filter(s => s.done).length;
  const isComplete = completedSteps === steps.length;
  const currentStep = steps.find(s => !s.done);
  const progressPercent = item.progress_percentage ?? (completedSteps / steps.length) * 100;
  
  let overallStatus: 'done' | 'processing' | 'error' = 'processing';
  if (isComplete || item.status === 'completed' || item.progress_percentage === 100) {
    overallStatus = 'done';
  } else if (item.status === 'error' || item.status === 'failed') {
    overallStatus = 'error';
  }
  
  return { steps, completedSteps, isComplete, currentStep, progressPercent, overallStatus };
}

interface QuizGenerationDetailModalProps {
  item: QuizGenerationItem | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function QuizGenerationDetailModal({ 
  item, 
  isOpen, 
  onClose 
}: QuizGenerationDetailModalProps) {
  if (!item) return null;

  const status = getDetailedStatus(item);
  const updated = item.updated_at ? new Date(item.updated_at).toLocaleString('vi-VN') : "Chưa có thông tin";

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-400 via-emerald-400 to-teal-500 text-white flex items-center justify-center font-bold text-lg shadow-md">
              {item.quiz_id?.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <DialogTitle className="text-xl font-bold text-gray-900">
                Chi tiết quá trình tạo Quiz
              </DialogTitle>
              <DialogDescription className="text-gray-600">
                Theo dõi từng bước trong quá trình tạo quiz
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6">
          {/* Quiz Info */}
          <div className="space-y-3">
            {item.title && (
              <div>
                <h3 className="text-lg font-bold text-gray-900">{item.title}</h3>
              </div>
            )}
            {item.overview && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-700">{item.overview}</p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Hash className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Quiz ID:</span>
              <code className="text-xs font-mono bg-white px-2 py-1 rounded border truncate max-w-[200px]" title={item.quiz_id}>
                {item.quiz_id}
              </code>
            </div>
            {item.questions_count !== undefined && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Số câu hỏi:</span>
                <span className="text-sm font-medium text-green-600">
                  {item.questions_count} câu
                </span>
              </div>
            )}
            {item.ideas_count !== undefined && (
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-600">Ý tưởng:</span>
                <span className="text-sm font-medium">{item.ideas_count} ý tưởng</span>
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
                <Badge variant="outline" className="border-green-200 text-green-600">
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
                      : 'bg-gradient-to-r from-green-500 to-green-600'
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
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-5 h-5 text-green-600" />
                <h4 className="font-semibold text-green-800">Đang thực hiện</h4>
              </div>
              <p className="text-green-700 font-medium">{status.currentStep.label}</p>
              <p className="text-sm text-green-600 mt-1">{status.currentStep.description}</p>
            </div>
          )}
          {status.overallStatus === 'error' && (
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-5 h-5 text-red-600" />
                <h4 className="font-semibold text-red-800">Lỗi xảy ra</h4>
              </div>
              <p className="text-red-700 font-medium">Quá trình tạo quiz gặp sự cố</p>
              <p className="text-sm text-red-600 mt-1">Vui lòng thử lại hoặc liên hệ hỗ trợ</p>
            </div>
          )}

          {/* Current Step Detail */}
          {item.current_step_detail && (
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-blue-800 mb-2">Trạng thái hiện tại</h4>
              <p className="text-blue-700 italic">&ldquo;{item.current_step_detail}&rdquo;</p>
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
                        ? "bg-green-50 border-green-200 border-dashed"
                        : "bg-gray-50 border-gray-200"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`mt-0.5 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        step.done
                          ? "bg-green-500 text-white"
                          : isActive
                          ? "bg-green-500 text-white"
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
                              ? "text-green-800"
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
                            <Badge variant="outline" className="border-green-300 text-green-700 text-xs">
                              Đang thực hiện
                            </Badge>
                          )}
                        </div>
                        <p className={`text-sm ${
                          step.done
                            ? "text-green-600"
                            : isActive
                            ? "text-green-600"
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
