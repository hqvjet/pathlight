"use client";
import { Card } from "@/components/ui/card";
import { CheckCircle, Clock, FileText, AlertCircle } from "lucide-react";
import { QuizGenerationItem } from "./QuizGenerationList";

interface QuizGenerationCardProps {
  item: QuizGenerationItem;
  onClick: () => void;
}

export default function QuizGenerationCard({ item, onClick }: QuizGenerationCardProps) {
  const getProgressPercentage = () => {
    let completed = 0;
    if (item.title_ready) completed++;
    if (item.cards_ready) completed++;
    if (item.final_ready) completed++;
    return Math.round((completed / 3) * 100);
  };

  const getStatusInfo = () => {
    if (item.final_ready) {
      return { text: "Hoàn thành", color: "text-green-600", bgColor: "bg-green-50", icon: CheckCircle };
    }
    if (item.cards_ready) {
      return { text: "Đang hoàn thiện", color: "text-blue-600", bgColor: "bg-blue-50", icon: Clock };
    }
    if (item.title_ready) {
      return { text: "Đang tạo câu hỏi", color: "text-yellow-600", bgColor: "bg-yellow-50", icon: Clock };
    }
    return { text: "Đang khởi tạo", color: "text-gray-600", bgColor: "bg-gray-50", icon: AlertCircle };
  };

  const status = getStatusInfo();
  const StatusIcon = status.icon;
  const progress = getProgressPercentage();

  return (
    <Card 
      onClick={onClick}
      className="p-5 hover:shadow-lg transition-shadow cursor-pointer border border-gray-200 hover:border-green-300"
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="w-14 h-14 rounded-xl bg-green-100 text-green-600 flex items-center justify-center font-bold text-lg shadow-sm shrink-0">
            <FileText className="w-6 h-6" />
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-semibold ${status.bgColor} ${status.color} flex items-center gap-1.5`}>
            <StatusIcon className="w-3.5 h-3.5" />
            {status.text}
          </div>
        </div>

        {/* Quiz ID */}
        <div>
          <p className="text-sm font-semibold text-gray-900 truncate">
            Quiz #{item.quiz_id.slice(0, 12)}...
          </p>
          {item.updated_at && (
            <p className="text-xs text-gray-500 mt-1">
              Cập nhật: {new Date(item.updated_at).toLocaleString('vi-VN')}
            </p>
          )}
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">Tiến độ</span>
            <span className="font-semibold text-green-600">{progress}%</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-green-500 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Checkpoints */}
        <div className="flex items-center gap-2 text-xs">
          <div className={`flex items-center gap-1 ${item.title_ready ? 'text-green-600' : 'text-gray-400'}`}>
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Tiêu đề</span>
          </div>
          <div className={`flex items-center gap-1 ${item.cards_ready ? 'text-green-600' : 'text-gray-400'}`}>
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Câu hỏi</span>
          </div>
          <div className={`flex items-center gap-1 ${item.final_ready ? 'text-green-600' : 'text-gray-400'}`}>
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Hoàn thiện</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
