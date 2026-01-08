"use client";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { CheckCircle, Eye, Send } from "lucide-react";
import { useState } from "react";

export type AnswerDisplayMode = 'immediate' | 'after_submit';

interface QuizSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStart: (mode: AnswerDisplayMode) => void;
  quizTitle?: string;
}

export default function QuizSettingsModal({ 
  isOpen, 
  onClose, 
  onStart,
  quizTitle 
}: QuizSettingsModalProps) {
  const [selectedMode, setSelectedMode] = useState<AnswerDisplayMode>('after_submit');

  const handleStart = () => {
    onStart(selectedMode);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader className="space-y-3">
          <DialogTitle className="text-2xl font-bold text-gray-900">
            Cài đặt Quiz
          </DialogTitle>
          <DialogDescription className="text-gray-600">
            {quizTitle && <span className="font-medium">&ldquo;{quizTitle}&rdquo;</span>}
            <br />
            Chọn chế độ hiển thị đáp án phù hợp với bạn
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <h3 className="font-semibold text-gray-900 mb-3">Chế độ hiển thị đáp án</h3>
          
          {/* Option 1: After Submit */}
          <button
            onClick={() => setSelectedMode('after_submit')}
            className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
              selectedMode === 'after_submit'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 ${
                selectedMode === 'after_submit'
                  ? 'border-blue-500 bg-blue-500'
                  : 'border-gray-300'
              }`}>
                {selectedMode === 'after_submit' && (
                  <CheckCircle className="w-3 h-3 text-white" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Send className="w-5 h-5 text-blue-600" />
                  <h4 className="font-semibold text-gray-900">Hiển thị sau khi hoàn thành</h4>
                </div>
                <p className="text-sm text-gray-600">
                  Hoàn thành tất cả câu hỏi và nhấn &ldquo;Nộp bài&rdquo; để xem kết quả. Phù hợp cho kiểm tra đánh giá chính thức.
                </p>
                <ul className="mt-2 space-y-1 text-xs text-gray-500">
                  <li>✓ Tập trung hoàn thành quiz</li>
                  <li>✓ Không bị ảnh hưởng bởi đáp án trước</li>
                  <li>✓ Xem tổng quan kết quả cuối cùng</li>
                </ul>
              </div>
            </div>
          </button>

          {/* Option 2: Immediate */}
          <button
            onClick={() => setSelectedMode('immediate')}
            className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
              selectedMode === 'immediate'
                ? 'border-green-500 bg-green-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 ${
                selectedMode === 'immediate'
                  ? 'border-green-500 bg-green-500'
                  : 'border-gray-300'
              }`}>
                {selectedMode === 'immediate' && (
                  <CheckCircle className="w-3 h-3 text-white" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Eye className="w-5 h-5 text-green-600" />
                  <h4 className="font-semibold text-gray-900">Hiển thị ngay sau mỗi câu</h4>
                </div>
                <p className="text-sm text-gray-600">
                  Xem đáp án đúng và giải thích ngay sau khi chọn. Phù hợp cho học tập và ôn luyện.
                </p>
                <ul className="mt-2 space-y-1 text-xs text-gray-500">
                  <li>✓ Học hỏi ngay lập tức từ sai lầm</li>
                  <li>✓ Đọc giải thích chi tiết</li>
                  <li>✓ Củng cố kiến thức từng bước</li>
                </ul>
              </div>
            </div>
          </button>
        </div>

        <div className="flex items-center justify-between gap-3 pt-4 border-t">
          <Button
            variant="outline"
            onClick={onClose}
            className="flex-1"
          >
            Hủy
          </Button>
          <Button
            onClick={handleStart}
            className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800"
          >
            Bắt đầu Quiz
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
