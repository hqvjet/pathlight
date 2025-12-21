"use client";
import { X, CheckCircle, Clock, FileText } from "lucide-react";
import { QuizGenerationItem } from "./QuizGenerationList";

interface QuizGenerationDetailModalProps {
  item: QuizGenerationItem;
  isOpen: boolean;
  onClose: () => void;
}

export default function QuizGenerationDetailModal({ 
  item, 
  isOpen, 
  onClose 
}: QuizGenerationDetailModalProps) {
  if (!isOpen) return null;

  const getProgressPercentage = () => {
    let completed = 0;
    if (item.title_ready) completed++;
    if (item.cards_ready) completed++;
    if (item.final_ready) completed++;
    return Math.round((completed / 3) * 100);
  };

  const progress = getProgressPercentage();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={onClose}>
      <div 
        className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-green-100 text-green-600 flex items-center justify-center">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Chi tiết tiến trình</h2>
              <p className="text-sm text-gray-500">Quiz #{item.quiz_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Overall Progress */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-gray-700">Tiến độ tổng thể</span>
              <span className="text-lg font-bold text-green-600">{progress}%</span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-green-500 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Checkpoints */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-700">Các bước xử lý</h3>
            
            <div className={`flex items-start gap-3 p-3 rounded-lg ${item.title_ready ? 'bg-green-50' : 'bg-gray-50'}`}>
              <CheckCircle className={`w-5 h-5 mt-0.5 ${item.title_ready ? 'text-green-600' : 'text-gray-400'}`} />
              <div className="flex-1">
                <p className={`font-medium ${item.title_ready ? 'text-green-900' : 'text-gray-600'}`}>
                  Khởi tạo và tạo tiêu đề
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {item.title_ready ? 'Đã hoàn thành' : 'Đang xử lý...'}
                </p>
              </div>
            </div>

            <div className={`flex items-start gap-3 p-3 rounded-lg ${item.cards_ready ? 'bg-green-50' : 'bg-gray-50'}`}>
              <CheckCircle className={`w-5 h-5 mt-0.5 ${item.cards_ready ? 'text-green-600' : 'text-gray-400'}`} />
              <div className="flex-1">
                <p className={`font-medium ${item.cards_ready ? 'text-green-900' : 'text-gray-600'}`}>
                  Tạo câu hỏi và đáp án
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {item.cards_ready ? 'Đã hoàn thành' : item.title_ready ? 'Đang xử lý...' : 'Chờ bước trước'}
                </p>
              </div>
            </div>

            <div className={`flex items-start gap-3 p-3 rounded-lg ${item.final_ready ? 'bg-green-50' : 'bg-gray-50'}`}>
              <CheckCircle className={`w-5 h-5 mt-0.5 ${item.final_ready ? 'text-green-600' : 'text-gray-400'}`} />
              <div className="flex-1">
                <p className={`font-medium ${item.final_ready ? 'text-green-900' : 'text-gray-600'}`}>
                  Hoàn thiện và xuất bản
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {item.final_ready ? 'Đã hoàn thành' : item.cards_ready ? 'Đang xử lý...' : 'Chờ bước trước'}
                </p>
              </div>
            </div>
          </div>

          {/* Metadata */}
          {item.updated_at && (
            <div className="pt-4 border-t border-gray-200">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Clock className="w-4 h-4" />
                <span>Cập nhật lần cuối: {new Date(item.updated_at).toLocaleString('vi-VN')}</span>
              </div>
            </div>
          )}

          {/* Status Message */}
          {item.final_ready && (
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-sm text-green-800">
                ✓ Quiz đã được tạo thành công! Bạn có thể xem trong danh sách quiz của mình.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
