"use client";
import { useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CourseDraftState } from '@/types/create-course';
import { AgenticCourseResponse, AgenticCreateCourseResponse } from '@/lib/api/agentic';

interface SuccessStepProps {
  draft: CourseDraftState;
  result: AgenticCreateCourseResponse | null;
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

const isCourseResponse = (value: AgenticCreateCourseResponse | null): value is AgenticCourseResponse => {
  return Boolean(value && 'course_title' in value && 'course_lessons' in value);
};

export function SuccessStep({ draft, result, onRestart, onGoToCourses }: SuccessStepProps) {
  const lessons = useMemo(() => (isCourseResponse(result) ? result.course_lessons : []), [result]);
  const hasResult = isCourseResponse(result);
  const isPending = !hasResult || lessons.length === 0;
  const courseTitle = hasResult ? result.course_title : 'Đang chờ phản hồi...';
  const courseOverview = hasResult ? result.course_overview : 'Hệ thống đang xử lý phản hồi.';
  const courseLevel = hasResult ? result.course_level : undefined;
  const courseDuration = hasResult ? result.course_duration : undefined;

  const renderContent = (content: string) => {
    const segments = content.split(/```/);
    return segments.map((seg, idx) => {
      const key = `${idx}-${seg.slice(0, 10)}`;
      if (idx % 2 === 1) {
        const trimmed = seg.trim();
        const [firstLine, ...rest] = trimmed.split('\n');
        const isLang = /^(json|xml|html|yaml|yml)$/i.test(firstLine.trim());
        const lang = isLang ? firstLine.trim().toUpperCase() : 'CODE';
        const code = isLang ? rest.join('\n') : trimmed;
        return (
          <pre key={key} className="rounded-lg border border-gray-200 bg-gray-900 text-gray-100 text-sm overflow-x-auto">
            <div className="px-3 py-2 text-xs uppercase tracking-wide text-gray-400 border-b border-gray-800">{lang}</div>
            <code className="block px-3 py-3 whitespace-pre">{code}</code>
          </pre>
        );
      }
      const paragraphs = seg.split(/\n\n+/).map((p) => p.trim()).filter(Boolean);
      return paragraphs.map((p, pIdx) => (
        <p key={`${key}-p-${pIdx}`} className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
          {p}
        </p>
      ));
    });
  };

  const levelLabelMeta: Record<CourseDraftState['meta']['courseLevel'], string> = {
    overview: 'Tổng quan',
    intermediate: 'Trung cấp',
    advance: 'Nâng cao',
  };

  const constraintLabel: Record<CourseDraftState['meta']['courseConstraint'], string> = {
    professional: 'Chuyên nghiệp',
    academic: 'Học thuật',
    friendly: 'Gần gũi',
    humorous: 'Dí dỏm',
  };

  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-semibold text-gray-900">Hoàn tất! {hasResult ? 'Khóa học đã sẵn sàng' : 'Đã gửi yêu cầu'}</h2>
        <p className="text-sm text-gray-600">{hasResult ? 'Dưới đây là bản tóm tắt và nội dung khóa học.' : 'Hệ thống đang xử lý, bạn có thể ở lại trang này hoặc quay lại sau.'}</p>
      </div>

      {/* Input recap */}
      <div className="grid gap-4 rounded-xl border border-gray-200 bg-white p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Tóm tắt đầu vào</h3>
            <p className="text-xs text-gray-500">Thông tin bạn đã cung cấp để sinh khóa học.</p>
          </div>
          <Badge className={hasResult ? 'bg-emerald-500 text-white border-none' : 'bg-orange-100 text-orange-700 border-none'}>
            {hasResult ? 'Đã tạo khóa học' : 'Đang xử lý'}
          </Badge>
        </div>
        <dl className="grid sm:grid-cols-2 gap-3 text-sm text-gray-800">
          <div>
            <dt className="text-gray-500">Vị trí người học</dt>
            <dd className="font-medium">{draft.meta.userPosition || '—'}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Trình độ khóa học</dt>
            <dd className="font-medium">{levelLabelMeta[draft.meta.courseLevel]}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Văn phong khóa học</dt>
            <dd className="font-medium">{constraintLabel[draft.meta.courseConstraint]}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Thời lượng</dt>
            <dd className="font-medium">{draft.meta.durationDays} ngày</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-gray-500">Prompt ngắn</dt>
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
            <p className="text-xs uppercase tracking-wide text-orange-600 font-semibold">Kết quả khóa học</p>
            <h3 className="text-2xl font-bold text-gray-900">{courseTitle}</h3>
            <p className="text-gray-700 leading-relaxed max-w-3xl">{courseOverview}</p>
          </div>
          <div className="flex flex-col items-end gap-2 text-sm text-gray-700">
            <Badge className={hasResult ? 'bg-orange-500 text-white border-none' : 'bg-gray-200 text-gray-700 border-none'}>
              {hasResult && courseLevel ? `Level ${courseLevel} · ${levelLabel(courseLevel)}` : 'Đang tạo' }
            </Badge>
            <span className="text-gray-600">Thời lượng: {courseDuration ? `${courseDuration} ngày` : 'Đang tính toán'}</span>
          </div>
        </div>

        {isPending && (
          <div className="flex items-center justify-center gap-3 rounded-lg border border-dashed border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-700">
            <span className="inline-flex h-3 w-3 rounded-full bg-orange-500 animate-pulse" aria-hidden />
            Hệ thống đang xử lý khóa học của bạn. Bạn có thể ở lại trang này hoặc quay lại sau.
          </div>
        )}

        {lessons.length > 0 && (
          <div className="space-y-4">
            {lessons.map((lesson, idx) => (
              <div key={lesson.lesson_title + idx} className="rounded-lg border border-gray-200 p-4 bg-gray-50 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs text-gray-500">Lesson {idx + 1}</p>
                    <h4 className="text-lg font-semibold text-gray-900">{lesson.lesson_title}</h4>
                  </div>
                  <Badge variant="outline" className="border-gray-300 text-gray-700">Level {lesson.lesson_level}</Badge>
                </div>
                <div className="space-y-3 bg-white border border-gray-200 rounded-lg p-3">
                  {renderContent(lesson.lesson_content || '')}
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
                        <p className="text-sm text-gray-700">Giải thích: {q.assessment_explanation}</p>
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
      <div className="flex flex-wrap justify-center gap-3">
        <Button onClick={onGoToCourses} className="bg-orange-500 hover:bg-orange-600 text-white">Về trang khóa học</Button>
        <Button variant="outline" onClick={onRestart} className="border-gray-200">Tạo khóa học khác</Button>
      </div>
    </div>
  );
}
