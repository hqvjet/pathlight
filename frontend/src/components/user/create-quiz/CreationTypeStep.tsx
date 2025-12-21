"use client";
import { FileUp, PenTool } from 'lucide-react';

interface CreationTypeStepProps {
  onSelectType: (type: 'ai' | 'manual') => void;
  onCancel: () => void;
}

export function CreationTypeStep({ onSelectType, onCancel }: CreationTypeStepProps) {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100 space-y-6">
        <div className="text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">Chọn cách tạo Quiz</h2>
          <p className="text-gray-600">Bạn muốn AI tạo quiz từ tài liệu hay tự tạo câu hỏi?</p>
        </div>

        <div className="grid sm:grid-cols-2 gap-6 pt-4">
          {/* AI Generation Option */}
          <button
            onClick={() => onSelectType('ai')}
            className="group p-8 rounded-xl border-2 border-gray-200 hover:border-sky-500 hover:bg-sky-50/50 transition-all text-left"
          >
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-sky-100 group-hover:bg-sky-500 flex items-center justify-center transition-colors">
                <FileUp className="w-8 h-8 text-sky-600 group-hover:text-white transition-colors" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">AI Tạo Quiz</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  Upload tài liệu và để AI tự động tạo câu hỏi trắc nghiệm từ nội dung.
                </p>
                <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-100 text-green-700 text-xs font-semibold">
                  ✓ Nhận EXP khi hoàn thành
                </div>
              </div>
            </div>
          </button>

          {/* Manual Creation Option */}
          <button
            onClick={() => onSelectType('manual')}
            className="group p-8 rounded-xl border-2 border-gray-200 hover:border-orange-500 hover:bg-orange-50/50 transition-all text-left"
          >
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-orange-100 group-hover:bg-orange-500 flex items-center justify-center transition-colors">
                <PenTool className="w-8 h-8 text-orange-600 group-hover:text-white transition-colors" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Tự Tạo Quiz</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  Tự tạo câu hỏi, đáp án, gợi ý và giải thích cho từng câu hỏi.
                </p>
                <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 text-xs font-semibold">
                  Không tính EXP
                </div>
              </div>
            </div>
          </button>
        </div>
      </div>

      <div className="flex justify-center">
        <button
          type="button"
          onClick={onCancel}
          className="px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 text-sm"
        >
          Huỷ
        </button>
      </div>
    </div>
  );
}
