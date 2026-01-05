"use client";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Clock, Zap, FileText, User, CalendarClock } from "lucide-react";

export type GenerationItem = {
  course_id: string;
  user_id?: string;
  title?: string;
  description?: string;
  progress?: string;
  title_ready?: boolean;
  lessons_ready?: boolean;
  final_ready?: boolean;
  vectorized?: boolean;
  lessons_count?: number;
  lessons_planned?: number;
  roadmap_count?: number;
  final_count?: number;
  updated_at?: string;
};

function getGenerationStatus(item: GenerationItem) {
  const steps = [
    { key: 'vectorized', label: 'Docs', done: item.vectorized, count: null },
    { key: 'title_ready', label: 'Plan', done: item.title_ready, count: item.roadmap_count },
    { key: 'lesson_planned', label: 'Lessons Plan', done: item.title_ready && item.lessons_planned, count: item.lessons_planned },
    { key: 'lessons_ready', label: 'Lessons', done: item.lessons_ready, count: item.lessons_count },
  ];
  
  const completedSteps = steps.filter(s => s.done).length;
  const isComplete = completedSteps === steps.length;
  const currentStep = steps.find(s => !s.done);
  const progressPercent = (completedSteps / steps.length) * 100;
  
  // Use final_ready as overall status indicator, but also check if all steps are done
  let overallStatus: 'done' | 'processing' | 'error' = 'processing';
  if (isComplete || item.final_ready === true) {
    overallStatus = 'done';
  } else if (item.final_ready === false && item.progress?.includes('error')) {
    overallStatus = 'error';
  }
  
  return { steps, completedSteps, isComplete, currentStep, progressPercent, overallStatus };
}

// Truncate text for display
function truncateText(text: string, maxLength: number) {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}

// Format time difference
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

// Get user display name from user_id
function getUserDisplayName(userId?: string): string {
  if (!userId) return "Không rõ";
  // Extract email prefix if it's an email-like ID, otherwise truncate
  if (userId.includes('@')) {
    return userId.split('@')[0];
  }
  // For UUID format, show first 8 chars
  return userId.substring(0, 8) + "...";
}

export default function GenerationCard({ 
  item, 
  onClick 
}: { 
  item: GenerationItem; 
  onClick?: () => void;
}) {
  const status = getGenerationStatus(item);
  const displayTitle = item.title || "Đang tạo khóa học...";
  const displayDesc = item.description ? truncateText(item.description, 120) : null;
  const timeElapsed = getTimeElapsed(item.updated_at);
  const creatorName = getUserDisplayName(item.user_id);
  const lessonsInfo = item.lessons_planned 
    ? `${item.lessons_count || 0}/${item.lessons_planned}` 
    : null;

  return (
    <Card 
      className="group p-6 hover:shadow-xl transition-all duration-300 border-gray-200 cursor-pointer hover:border-orange-300 bg-white"
      onClick={onClick}
    >
      <div className="space-y-4">
        {/* Header with Status Badge */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3 
              className="font-bold text-lg text-gray-900 group-hover:text-orange-600 transition-colors leading-tight mb-1" 
              title={item.title}
            >
              {displayTitle}
            </h3>
            {lessonsInfo && (
              <div className="flex items-center gap-1.5 mb-2">
                <FileText className="w-4 h-4 text-orange-500" />
                <span className="text-sm font-semibold text-orange-600">{lessonsInfo} bài học</span>
              </div>
            )}
            {displayDesc && (
              <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed" title={item.description}>
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
            <Badge variant="outline" className="border-orange-300 text-orange-600 bg-orange-50 shrink-0">
              <Clock className="w-3 h-3 mr-1" />
              Đang xử lý ({status.completedSteps}/{status.steps.length})
            </Badge>
          )}
        </div>

        {/* Meta Information */}
        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600 pb-3 border-b border-gray-100">
          <div className="flex items-center gap-1.5" title="Người tạo">
            <User className="w-3.5 h-3.5 text-gray-500" />
            <span>{creatorName}</span>
          </div>
          <div className="flex items-center gap-1.5" title="Cập nhật lần cuối">
            <CalendarClock className="w-3.5 h-3.5 text-gray-500" />
            <span>{timeElapsed}</span>
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
                  : 'bg-gradient-to-r from-orange-500 to-orange-600'
              }`}
              style={{ width: `${status.progressPercent}%` }}
            />
          </div>
        </div>

        {/* Current Status Alert */}
        {status.overallStatus === 'processing' && status.currentStep && (
          <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg border border-orange-200">
            <Zap className="w-4 h-4 text-orange-600 shrink-0" />
            <span className="text-sm text-orange-800">
              <strong>Đang thực hiện:</strong> {status.currentStep.label}
            </span>
          </div>
        )}
        {status.overallStatus === 'error' && (
          <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-red-50 to-red-50 rounded-lg border border-red-200">
            <Zap className="w-4 h-4 text-red-600 shrink-0" />
            <span className="text-sm text-red-800">
              <strong>Lỗi:</strong> Quá trình tạo khóa học gặp sự cố
            </span>
          </div>
        )}

        {/* Todo List Style Steps */}
        <div className="grid grid-cols-4 gap-3">
          {status.steps.map((step) => (
            <div key={step.key} className="flex flex-col items-center gap-1.5">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-xs font-semibold transition-all ${
                step.done 
                  ? 'bg-green-500 text-white shadow-md scale-105' 
                  : 'bg-gray-200 text-gray-600'
              }`}>
                {step.done ? <CheckCircle className="w-5 h-5" /> : <Clock className="w-4 h-4" />}
              </div>
              <span className={`text-xs text-center leading-tight ${
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
