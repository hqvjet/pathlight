"use client";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Clock, FileText, Zap, User, CalendarClock } from "lucide-react";
import { QuizGenerationItem } from "./QuizGenerationList";

export interface QuizGenerationCardProps {
  item: QuizGenerationItem;
  onClick: () => void;
}

function getQuizStatus(item: QuizGenerationItem) {
  const steps = [
    { 
      key: 'vectorized', 
      label: 'Vectorized', 
      done: Boolean(item.vectorized),
      count: null
    },
    { 
      key: 'plan_ready', 
      label: 'Plan', 
      done: Boolean(item.plan_ready),
      count: item.ideas_count
    },
    { 
      key: 'questions_ready', 
      label: 'Questions', 
      done: Boolean(item.questions_ready),
      count: item.questions_count
    },
  ];
  
  const completedSteps = steps.filter(s => s.done).length;
  const isComplete = item.status === 'completed' || item.progress_percentage === 100;
  const currentStep = steps.find(s => !s.done);
  const progressPercent = item.progress_percentage ?? (completedSteps / steps.length) * 100;
  
  let overallStatus: 'done' | 'processing' | 'error' = 'processing';
  if (isComplete || item.final_ready === true) {
    overallStatus = 'done';
  } else if (item.status === 'error' || item.status === 'failed') {
    overallStatus = 'error';
  }
  
  return { steps, completedSteps, isComplete, currentStep, progressPercent, overallStatus };
}

function truncateText(text: string, maxLength: number) {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}

function getTimeElapsed(dateStr?: string): string {
  if (!dateStr) return "Không rõ";
  
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return "Vừa xong";
    if (diffMins < 60) return `${diffMins} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    if (diffDays < 7) return `${diffDays} ngày trước`;
    
    return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return "Không rõ";
  }
}

function getUserDisplayName(userId?: string): string {
  if (!userId) return "Không rõ";
  if (userId.includes('@')) {
    return userId.split('@')[0];
  }
  return userId.substring(0, 8) + "...";
}

export default function QuizGenerationCard({ item, onClick, userNames }: { 
  item: QuizGenerationItem; 
  onClick: () => void;
  userNames?: Record<string, string>;
}) {
  const status = getQuizStatus(item);
  const displayTitle = item.title || "Đang tạo quiz...";
  const displayDesc = item.overview ? truncateText(item.overview, 120) : null;
  const timeElapsed = getTimeElapsed(item.updated_at);
  const creatorName = item.user_id && userNames?.[item.user_id] ? userNames[item.user_id] : getUserDisplayName(item.user_id);
  const questionsInfo = item.questions_count ? `${item.questions_count}` : null;

  return (
    <Card 
      className="group p-4 sm:p-6 hover:shadow-xl transition-all duration-300 border-gray-200 cursor-pointer hover:border-green-300 bg-white h-full flex flex-col"
      onClick={onClick}
    >
      <div className="space-y-3 sm:space-y-4 flex-1 flex flex-col">
        {/* Header with Status Badge */}
        <div className="flex items-start justify-between gap-2 sm:gap-3">
          <div className="flex-1 min-w-0">
            <h3 
              className="font-bold text-base sm:text-lg text-gray-900 group-hover:text-green-600 transition-colors leading-tight mb-1 line-clamp-1" 
              title={item.title}
            >
              {displayTitle}
            </h3>
            {questionsInfo && (
              <div className="flex items-center gap-1.5 mb-2">
                <FileText className="w-4 h-4 text-green-500" />
                <span className="text-sm font-semibold text-green-600">{questionsInfo} câu hỏi</span>
              </div>
            )}
            {displayDesc && (
              <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed" title={item.overview}>
                {displayDesc}
              </p>
            )}
          </div>
          {status.overallStatus === 'done' ? (
            <Badge className="bg-green-500 text-white shadow-sm shrink-0">
              <CheckCircle className="w-3 h-3 mr-1" />
              Hoàn thành
            </Badge>
          ) : status.overallStatus === 'error' ? (
            <Badge variant="outline" className="border-red-300 text-red-600 bg-red-50 shrink-0">
              <Clock className="w-3 h-3 mr-1" />
              Lỗi
            </Badge>
          ) : (
            <Badge variant="outline" className="border-green-300 text-green-600 bg-green-50 shrink-0">
              <Clock className="w-3 h-3 mr-1" />
              Đang xử lý ({status.completedSteps}/{status.steps.length})
            </Badge>
          )}
        </div>

        {/* Meta Information */}
        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600 pb-3 border-b border-gray-100">
          <div className="flex items-center gap-1.5 truncate" title="Người tạo">
            <User className="w-3.5 h-3.5 text-gray-500 shrink-0" />
            <span className="truncate">{creatorName}</span>
          </div>
          <div className="flex items-center gap-1.5 shrink-0" title="Cập nhật lần cuối">
            <CalendarClock className="w-3.5 h-3.5 text-gray-500" />
            <span className="whitespace-nowrap">{timeElapsed}</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-700 font-medium">Tiến độ</span>
            <span className="text-gray-900 font-semibold">{status.completedSteps}/{status.steps.length} bước</span>
          </div>
          <div className="relative h-2.5 bg-gray-200 rounded-full overflow-hidden">
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
        </div>

        {/* Current Status Alert */}
        {status.overallStatus === 'processing' && status.currentStep && (
          <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
            <Zap className="w-4 h-4 text-green-600 shrink-0" />
            <span className="text-sm text-green-800">
              <strong>Đang thực hiện:</strong> {status.currentStep.label}
            </span>
          </div>
        )}
        {status.overallStatus === 'error' && (
          <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-red-50 to-red-50 rounded-lg border border-red-200">
            <Zap className="w-4 h-4 text-red-600 shrink-0" />
            <span className="text-sm text-red-800">
              <strong>Lỗi:</strong> Quá trình tạo quiz gặp sự cố
            </span>
          </div>
        )}

        {/* Todo List Style Steps */}
        <div className="grid grid-cols-3 gap-2 sm:gap-3 md:gap-4 lg:gap-5">
          {status.steps.map((step) => (
            <div key={step.key} className="flex flex-col items-center gap-1 sm:gap-1.5">
              <div className={`w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 rounded-full flex items-center justify-center text-xs font-semibold transition-all ${
                step.done 
                  ? 'bg-green-500 text-white shadow-md scale-105' 
                  : 'bg-gray-200 text-gray-600'
              }`}>
                {step.done ? <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5" /> : <Clock className="w-3.5 h-3.5 sm:w-4 sm:h-4" />}
              </div>
              <span className={`text-[10px] sm:text-xs text-center leading-tight ${
                step.done ? 'text-green-700 font-medium' : 'text-gray-600'
              }`}>
                {step.label}
              </span>
              {step.count !== null && step.count !== undefined && (
                <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                  step.done 
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {step.count}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
