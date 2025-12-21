"use client";
import { useCallback } from 'react';
import { Upload, FileText, X, AlertCircle, RotateCw } from 'lucide-react';
import type { UploadingFile, QuizDraftDocument } from '@/types/create-quiz';

interface UploadStepProps {
  documents: QuizDraftDocument[];
  uploading: UploadingFile[];
  onUpload: (files: FileList | File[] | null) => void;
  onRemoveDoc: (id: string) => void;
  onRemoveUploading: (id: string) => void;
  onRetry: (file: File, id?: string) => void;
  onNext: () => void;
  onBack: () => void;
}

export function UploadStep({ 
  documents, 
  uploading, 
  onUpload, 
  onRemoveDoc,
  onRemoveUploading,
  onRetry,
  onNext, 
  onBack 
}: UploadStepProps) {
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    onUpload(e.dataTransfer.files);
  }, [onUpload]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100 space-y-6">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">Upload Tài Liệu</h2>
          <p className="text-sm text-gray-600">
            Tải lên các file PDF, DOCX, TXT để AI tạo câu hỏi trắc nghiệm
          </p>
        </div>

        {/* Upload Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed border-gray-300 rounded-xl p-8 sm:p-12 text-center hover:border-sky-400 hover:bg-sky-50/30 transition-colors cursor-pointer"
        >
          <input
            type="file"
            id="file-upload"
            multiple
            accept=".pdf,.docx,.doc,.txt"
            onChange={(e) => onUpload(e.target.files)}
            className="hidden"
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-base font-semibold text-gray-900 mb-1">
              Kéo thả file hoặc click để chọn
            </p>
            <p className="text-sm text-gray-500">
              Hỗ trợ: PDF, DOCX, TXT (tối đa 10MB/file)
            </p>
          </label>
        </div>

        {/* Uploading Files */}
        {uploading.length > 0 && (
          <div className="space-y-3">
            <p className="text-sm font-semibold text-gray-700">Đang tải lên...</p>
            {uploading.map((file) => (
              <div key={file.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                <FileText className="w-5 h-5 text-gray-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{file.file.name}</p>
                  {file.status === 'uploading' && (
                    <div className="mt-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-sky-500 transition-all duration-300"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                  )}
                  {file.status === 'error' && (
                    <div className="flex items-center gap-2 mt-1">
                      <AlertCircle className="w-3 h-3 text-red-500" />
                      <p className="text-xs text-red-600">{file.error || 'Tải lên thất bại'}</p>
                    </div>
                  )}
                </div>
                {file.status === 'error' ? (
                  <button
                    onClick={() => onRetry(file.file, file.id)}
                    className="p-1.5 rounded-md hover:bg-gray-200 text-gray-600"
                  >
                    <RotateCw className="w-4 h-4" />
                  </button>
                ) : (
                  <button
                    onClick={() => onRemoveUploading(file.id)}
                    className="p-1.5 rounded-md hover:bg-gray-200 text-gray-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Uploaded Documents */}
        {documents.length > 0 && (
          <div className="space-y-3">
            <p className="text-sm font-semibold text-gray-700">Đã tải lên ({documents.length})</p>
            {documents.map((doc) => (
              <div key={doc.id} className="flex items-center gap-3 p-3 bg-green-50 rounded-lg border border-green-200">
                <FileText className="w-5 h-5 text-green-600 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{doc.name}</p>
                  <p className="text-xs text-gray-500">{formatFileSize(doc.size)}</p>
                </div>
                <button
                  onClick={() => onRemoveDoc(doc.id)}
                  className="p-1.5 rounded-md hover:bg-red-100 text-red-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between gap-4">
        <button
          type="button"
          onClick={onBack}
          className="px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 text-sm"
        >
          Quay lại
        </button>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onNext}
            className="px-6 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 text-sm"
          >
            Bỏ qua
          </button>
          <button
            type="button"
            onClick={onNext}
            className="px-6 py-2.5 rounded-lg bg-green-500 text-white font-semibold hover:bg-green-600 shadow-sm text-sm"
          >
            Tiếp theo →
          </button>
        </div>
      </div>
    </div>
  );
}
