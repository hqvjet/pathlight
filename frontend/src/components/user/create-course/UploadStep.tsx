"use client";
import { useCallback, useRef } from 'react';
import React from 'react';
import { CourseDraftDocumentMeta, UploadingFile } from '@/fake/courses';
import { cn } from '@/lib/utils';

interface UploadStepProps {
  documents: CourseDraftDocumentMeta[];
  uploading: UploadingFile[];
  onFiles: (files: FileList | null) => void;
  onRemove: (id: string) => void;
  onNext: () => void;
  onCancel: () => void;
}

export function UploadStep({ documents, uploading, onFiles, onRemove, onNext, onCancel }: UploadStepProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handleBrowse = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const hasFiles = documents.length > 0 || uploading.length > 0;
  const totalSize = documents.reduce((a, d) => a + d.size, 0);
  const maxTotalMB = 25;

  const validateAndSend = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const maxTotalBytes = maxTotalMB * 1024 * 1024;
    const newTotal = totalSize + Array.from(files).reduce((a,f)=>a+f.size,0);
    if (newTotal > maxTotalBytes) {
      setError(`Tổng dung lượng vượt ${maxTotalMB}MB`);
      return;
    }
    for (const f of Array.from(files)) {
      if (!/(pdf|docx?|pptx?)$/i.test(f.name)) {
        setError('Định dạng chỉ hỗ trợ: pdf, doc, docx, ppt, pptx');
        return;
      }
    }
    setError(null);
    onFiles(files);
  };

  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-lg font-semibold text-gray-800">Tải tài liệu lên</h2>
        <p className="text-sm text-gray-500">Hỗ trợ định dạng: pdf, docx, pptx</p>
      </div>

      <div
        className={cn(
          'relative border-2 border-dashed rounded-xl flex flex-col items-center justify-center bg-white transition-colors',
          'min-h-[260px] p-6 text-center',
          'border-gray-300 hover:border-orange-400 hover:bg-orange-50/40'
        )}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          if (e.dataTransfer.files) validateAndSend(e.dataTransfer.files);
        }}
        role="button"
        tabIndex={0}
        onKeyDown={(e)=> { if (e.key==='Enter' || e.key===' ') handleBrowse(); }}
        aria-label="Kéo thả hoặc chọn tập tin"
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.ppt,.pptx"
          className="hidden"
          onChange={(e) => validateAndSend(e.target.files)}
        />
        {!hasFiles && (
          <div className="space-y-4">
            <div className="mx-auto text-orange-500">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 16V4m0 0l4 4m-4-4L8 8m12 4v6a2 2 0 01-2 2H6a2 2 0 01-2-2v-6" />
              </svg>
            </div>
            <p className="text-sm text-gray-700">Kéo thả hoặc <button onClick={handleBrowse} className="text-orange-600 font-medium hover:underline" type="button">Browse Files</button></p>
            <p className="text-xs text-gray-400">Hỗ trợ định dạng: pdf, docx, pptx</p>
          </div>
        )}
        {hasFiles && (
          <div className="w-full space-y-4">
            <ul className="space-y-2 text-left max-h-60 overflow-y-auto pr-1">
              {uploading.map(f => (
                <li key={f.id} className="p-3 rounded-lg bg-gray-50 border border-gray-200 flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-700 truncate">{f.file.name}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="h-1.5 bg-gray-200 rounded-full w-full overflow-hidden">
                        <div className="h-full bg-orange-500 rounded-full transition-all" style={{ width: `${f.progress}%` }} />
                      </div>
                      <span className="text-xs text-gray-500 w-10 text-right tabular-nums">{Math.round(f.progress)}%</span>
                    </div>
                  </div>
                  {f.status === 'uploading' && (
                    <span className="text-[10px] uppercase tracking-wide text-orange-600 font-semibold">Đang tải</span>
                  )}
                  {f.status === 'error' && (
                    <span className="text-[10px] uppercase tracking-wide text-red-600 font-semibold">Lỗi</span>
                  )}
                </li>
              ))}
              {documents.map(doc => (
                <li key={doc.id} className="p-3 rounded-lg bg-white border border-gray-200 flex items-center gap-3 shadow-sm">
                  <div className="w-10 h-10 flex items-center justify-center rounded-md bg-orange-50 text-orange-600 font-semibold text-[11px] uppercase tracking-wide flex-shrink-0">
                    {(() => { const ext = doc.name.split('.').pop()?.toLowerCase(); if (ext === 'pdf') return 'PDF'; if (ext === 'doc' || ext === 'docx') return 'DOCX'; if (ext === 'ppt' || ext === 'pptx') return 'PPTX'; return 'FILE'; })()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate" title={doc.name}>{doc.name}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{(doc.size/1024/1024).toFixed(2)} MB</p>
                  </div>
                  <button onClick={() => onRemove(doc.id)} className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600" aria-label="Xóa">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </li>
              ))}
            </ul>
            <div className="flex flex-wrap gap-3 justify-between items-center text-xs text-gray-500">
              <div>{documents.length} file(s) &bull; Tổng: {(totalSize/1024/1024).toFixed(2)} MB (≤ {maxTotalMB}MB)</div>
              <button type="button" onClick={handleBrowse} className="px-3 py-1.5 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium">Thêm tài liệu</button>
            </div>
          </div>
        )}
        {error && <p className="text-sm text-red-600 -mt-4">{error}</p>}
      </div>
      <p className="text-xs text-gray-500">Note: Toàn bộ files không được vượt quá 25MB</p>
      <div className="flex justify-end gap-3 pt-2">
        <button onClick={onCancel} className="px-6 py-2 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium">Hủy</button>
        <button disabled={!documents.length} onClick={onNext} className={cn('px-6 py-2 rounded-md text-white font-semibold shadow-sm disabled:opacity-40 disabled:cursor-not-allowed', documents.length ? 'bg-orange-500 hover:bg-orange-600' : 'bg-orange-400')}>Bước Tiếp</button>
      </div>
    </div>
  );
}
