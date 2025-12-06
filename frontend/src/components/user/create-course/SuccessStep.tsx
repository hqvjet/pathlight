"use client";
import { useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CourseDraftState } from '@/types/create-course';
import { AgenticCourseResponse } from '@/lib/api/agentic';
import { showToast } from '@/utils/toast';

interface SuccessStepProps {
  draft: CourseDraftState;
  result: AgenticCourseResponse | null;
  onRestart: () => void;
  onGoToCourses: () => void;
}

const levelLabel = (level?: number) => {
  if (!level) return 'N/A';
  if (level <= 1) return 'Rất dễ (1)';
  if (level === 2) return 'Dễ (2)';
  if (level === 3) return 'Trung bình (3)';
  if (level === 4) return 'Khó (4)';
  return 'Rất khó (5)';
};

export function SuccessStep({ draft, result, onRestart, onGoToCourses }: SuccessStepProps) {
  const jsonString = useMemo(() => (result ? JSON.stringify(result, null, 2) : ''), [result]);

  const handleCopy = async () => {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(jsonString);
      showToast.success('Đã sao chép dữ liệu khóa học.');
    } catch {
      showToast.error('Không thể sao chép, vui lòng thử lại.');
    }
  };

  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-semibold text-gray-900">Hoàn tất! Đã nhận phản hồi từ hệ thống</h2>
        <p className="text-sm text-gray-600">Khóa học bên dưới được hiển thị trực tiếp từ dữ liệu hệ thống trả về. Bạn không cần biết JSON để xem.</p>
      </div>

      {/* Input recap */}
      <div className="grid gap-4 rounded-xl border border-gray-200 bg-white p-6">
        <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Tóm tắt đầu vào</h3>
        <dl className="grid sm:grid-cols-2 gap-3 text-sm text-gray-800">
          <div>
            <dt className="text-gray-500">User position</dt>
            <dd className="font-medium">{draft.meta.userPosition || '—'}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Course level</dt>
            <dd className="font-medium capitalize">{draft.meta.courseLevel}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Course constraint</dt>
            <dd className="font-medium capitalize">{draft.meta.courseConstraint}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Course duration</dt>
            <dd className="font-medium">{draft.meta.durationDays} ngày</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-gray-500">Short user prompt</dt>
            <dd className="font-medium whitespace-pre-wrap leading-relaxed">{draft.meta.shortPrompt || '—'}</dd>
          </div>
          <div className="sm:col-span-2 flex flex-wrap gap-2 items-center text-xs text-gray-600">
            <span className="font-semibold text-gray-700">Documents:</span>
            {draft.documents.length === 0 && <span>Không đính kèm</span>}
            {draft.documents.map((doc) => (
              <Badge key={doc.id} variant="outline" className="border-gray-200 text-gray-700 bg-gray-50">
                {doc.name}
              </Badge>
            ))}
          </div>
        </dl>
      </div>

      {/* Course output */}
      <div className="space-y-4 rounded-xl border border-gray-200 bg-white p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-wide text-orange-600 font-semibold">Course Output</p>
            <h3 className="text-2xl font-bold text-gray-900">{result?.course_title || 'Đang chờ phản hồi...'}</h3>
            <p className="text-gray-700 leading-relaxed max-w-3xl">{result?.course_overview || 'Hệ thống đang xử lý phản hồi.'}</p>
          </div>
          {result && (
            <div className="flex flex-col items-end gap-2 text-sm text-gray-700">
              <Badge className="bg-orange-500 text-white border-none">Level {result.course_level} · {levelLabel(result.course_level)}</Badge>
              <span className="text-gray-600">Duration: {result.course_duration} ngày</span>
            </div>
          )}
        </div>

        {result && (
          <div className="space-y-4">
            {result.course_lessons.map((lesson, idx) => (
              <div key={lesson.lesson_title + idx} className="rounded-lg border border-gray-200 p-4 bg-gray-50 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs text-gray-500">Lesson {idx + 1}</p>
                    <h4 className="text-lg font-semibold text-gray-900">{lesson.lesson_title}</h4>
                  </div>
                  <Badge variant="outline" className="border-gray-300 text-gray-700">Level {lesson.lesson_level}</Badge>
                </div>
                <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed bg-white border border-gray-200 rounded-lg p-3">
                  {lesson.lesson_content}
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-gray-800">Assessments</p>
                  <div className="space-y-2">
                    {lesson.lesson_assessments.map((q, qIdx) => (
                      <div key={q.assessment_question + qIdx} className="border border-gray-200 rounded-lg p-3 bg-white space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-xs text-gray-500">Câu {qIdx + 1}</p>
                            <p className="text-sm font-semibold text-gray-900">{q.assessment_question}</p>
                          </div>
                          <Badge variant="outline" className="border-gray-300 text-gray-700">Level {q.assessment_level}</Badge>
                        </div>
                        <p className="text-sm text-gray-700">Hint: {q.assessment_hint}</p>
                        <p className="text-sm text-gray-700">Giải thích: {q.assessment_explaination}</p>
                        <div className="grid sm:grid-cols-2 gap-2 text-sm">
                          {q.assessment_options.map((opt, oIdx) => (
                            <div
                              key={oIdx}
                              className={`rounded-md border p-2 ${opt.option_correction ? 'border-emerald-300 bg-emerald-50 text-emerald-800' : 'border-gray-200 bg-gray-50 text-gray-700'}`}
                            >
                              <span className="font-medium">{String.fromCharCode(65 + oIdx)}.</span> {opt.option_content}
                              {opt.option_correction && <span className="ml-2 text-xs font-semibold">(Đúng)</span>}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Structured data (JSON) */}
      <div className="rounded-xl border border-gray-900 bg-gray-950 text-gray-50">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 text-sm">
          <span className="font-semibold">Dữ liệu chi tiết (máy đọc)</span>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">Dữ liệu đã cấu trúc sẵn; hệ thống dùng để hiển thị. Bạn có thể sao chép nếu cần chuyển sang nơi khác.</span>
            <Button size="sm" variant="secondary" onClick={handleCopy} disabled={!result}>
              Sao chép dữ liệu
            </Button>
          </div>
        </div>
        <pre className="p-4 overflow-x-auto text-xs whitespace-pre-wrap">{jsonString || 'Đang chờ phản hồi...'}</pre>
      </div>

      <div className="flex flex-wrap justify-center gap-3">
        <Button onClick={onGoToCourses} className="bg-orange-500 hover:bg-orange-600 text-white">Về trang khóa học</Button>
        <Button variant="outline" onClick={onRestart} className="border-gray-200">Tạo khóa học khác</Button>
      </div>
    </div>
  );
}
