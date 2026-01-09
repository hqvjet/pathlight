"use client";
import { useMemo, useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { CourseDraftState } from '@/types/create-course';
import { AgenticCourseResponse, AgenticCreateCourseResponse } from '@/lib/api/agentic';
import { courseApi } from '@/lib/api/course';
import { CheckCircle, Clock, Zap, FileText, Hash } from 'lucide-react';

interface SuccessStepProps {
  draft: CourseDraftState;
  result: AgenticCreateCourseResponse | null;
  onRestart: () => void;
  onGoToCourses: () => void;
}

type GenerationStatus = {
  course_id: string;
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

function getGenerationStatus(status: GenerationStatus | null) {
  // Always show 4 steps with default values, update when API returns
  const steps = [
    { 
      key: 'vectorized', 
      label: 'Phân tích tài liệu', 
      done: status?.vectorized || false,
      description: 'Vectorize và index tài liệu vào OpenSearch',
      count: null,
      icon: FileText
    },
    { 
      key: 'title_ready', 
      label: 'Tạo kế hoạch', 
      done: status?.title_ready || false,
      description: 'Sinh tiêu đề, mô tả và roadmap học tập',
      count: status?.roadmap_count,
      icon: Zap
    },
    { 
      key: 'lesson_planned', 
      label: 'Lập kế hoạch bài học', 
      done: (status?.title_ready && status?.lessons_planned) || false,
      description: `Xác định số lượng bài học cần tạo${status?.lessons_planned ? ` (${status.lessons_planned} bài)` : ''}`,
      count: status?.lessons_planned,
      icon: Clock
    },
    { 
      key: 'lessons_ready', 
      label: 'Tạo nội dung bài học', 
      done: status?.lessons_ready || false,
      description: `Sinh nội dung chi tiết cho từng bài học${status?.lessons_count ? ` (${status.lessons_count}/${status.lessons_planned || 0} bài)` : ''}`,
      count: status?.lessons_count,
      icon: CheckCircle
    },
  ];
  
  const completedSteps = steps.filter(s => s.done).length;
  const isComplete = completedSteps === steps.length;
  const currentStep = steps.find(s => !s.done);
  const progressPercent = (completedSteps / steps.length) * 100;
  
  let overallStatus: 'done' | 'processing' | 'error' = 'processing';
  if (status) {
    if (isComplete || status.final_ready === true) {
      overallStatus = 'done';
    } else if (status.final_ready === false && status.progress?.includes('error')) {
      overallStatus = 'error';
    }
  }
  
  return { steps, completedSteps, isComplete, currentStep, progressPercent, overallStatus };
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
  const [generationStatus, setGenerationStatus] = useState<GenerationStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  
  const lessons = useMemo(() => (isCourseResponse(result) ? result.course_lessons : []), [result]);
  const hasResult = isCourseResponse(result);
  const isPending = !hasResult || lessons.length === 0;
  const courseTitle = hasResult ? result.course_title : 'Đang chờ phản hồi...';
  const courseOverview = hasResult ? result.course_overview : 'Hệ thống đang xử lý phản hồi.';
  const courseLevel = hasResult ? result.course_level : undefined;
  const courseDuration = hasResult ? result.course_duration : undefined;

  const status = getGenerationStatus(generationStatus);
  const courseId = draft.courseId;

  // Fetch generation status
  const fetchGenerationStatus = async () => {
    if (!courseId) return;
    try {
      const resp = await courseApi.getStatus(courseId);
      if (resp?.data?.body && typeof resp.data.body === 'object') {
        setGenerationStatus(resp.data.body as GenerationStatus);
      }
    } catch (error) {
      console.error('[SuccessStep] Failed to fetch generation status:', error);
    }
  };

  // Polling effect - fetch every 5 seconds if processing
  useEffect(() => {
    if (!courseId) return;
    
    // Initial fetch
    fetchGenerationStatus();
    
    // Start polling if not complete
    if (status.overallStatus === 'processing') {
      setIsPolling(true);
      const interval = setInterval(fetchGenerationStatus, 5000);
      return () => {
        clearInterval(interval);
        setIsPolling(false);
      };
    } else {
      setIsPolling(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId, status.overallStatus]); // fetchGenerationStatus intentionally omitted to prevent re-creation loop


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

      {/* Generation Tracking Section - NEW */}
      {courseId && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Quá trình tạo khóa học</h3>
              <p className="text-xs text-gray-500">Theo dõi chi tiết từng bước</p>
            </div>
            <Badge className={
              status.overallStatus === 'done' 
                ? 'bg-emerald-500 text-white border-none' 
                : status.overallStatus === 'error'
                ? 'bg-red-500 text-white border-none'
                : 'bg-orange-500 text-white border-none'
            }>
              {status.overallStatus === 'done' 
                ? 'Hoàn thành' 
                : status.overallStatus === 'error'
                ? 'Lỗi'
                : isPolling ? 'Đang xử lý...' : 'Đang xử lý'}
            </Badge>
          </div>

          {/* Course Info - only show if loaded */}
          {generationStatus?.title && (
            <div className="space-y-2">
              <h4 className="font-bold text-gray-900">{generationStatus.title}</h4>
              {generationStatus.description && (
                <p className="text-sm text-gray-600">{generationStatus.description}</p>
              )}
            </div>
          )}

          {/* Loading state when no data yet */}
          {!generationStatus && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="w-4 h-4 border-2 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
              <span>Đang tải thông tin khóa học...</span>
            </div>
          )}

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Tiến độ</span>
              <span className="font-semibold text-gray-900">{status.completedSteps}/{status.steps.length} bước</span>
            </div>
            <Progress 
              value={status.progressPercent} 
              className="h-2" 
            />
          </div>

          {/* Detailed Steps */}
          <div className="space-y-3">
            {status.steps.map((step) => {
              const Icon = step.icon;
              return (
                <div 
                  key={step.key}
                  className={`flex items-start gap-3 p-3 rounded-lg border ${
                    step.done 
                      ? 'border-emerald-200 bg-emerald-50' 
                      : status.currentStep?.key === step.key
                      ? 'border-orange-200 bg-orange-50'
                      : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    step.done 
                      ? 'bg-emerald-500 text-white' 
                      : status.currentStep?.key === step.key
                      ? 'bg-orange-500 text-white'
                      : 'bg-gray-300 text-gray-600'
                  }`}>
                    {step.done ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : status.currentStep?.key === step.key ? (
                      <Clock className="w-5 h-5 animate-pulse" />
                    ) : (
                      <Icon className="w-5 h-5" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h5 className={`text-sm font-semibold ${
                        step.done ? 'text-emerald-900' : 'text-gray-900'
                      }`}>
                        {step.label}
                      </h5>
                      {step.count !== null && step.count !== undefined && (
                        <Badge variant="outline" className="text-xs">
                          {step.count}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{step.description}</p>
                  </div>
                  <div className="flex-shrink-0">
                    {step.done ? (
                      <span className="text-xs font-medium text-emerald-700">Hoàn thành</span>
                    ) : status.currentStep?.key === step.key ? (
                      <span className="text-xs font-medium text-orange-700">Đang xử lý</span>
                    ) : (
                      <span className="text-xs text-gray-500">Chờ</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Additional Info */}
          {generationStatus && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-3 border-t border-gray-200">
              <div className="flex items-center gap-2 text-sm">
                <Hash className="w-4 h-4 text-gray-500" />
                <span className="text-gray-600">Course ID:</span>
                <code className="text-xs font-mono bg-white px-2 py-1 rounded border truncate" title={courseId}>
                  {courseId}
                </code>
              </div>
              {generationStatus.roadmap_count && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-600">Roadmap:</span>
                  <span className="font-medium">{generationStatus.roadmap_count} bước</span>
                </div>
              )}
              {generationStatus.lessons_planned && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-600">Số bài học:</span>
                  <span className="font-medium text-orange-600">
                    {generationStatus.lessons_count || 0}/{generationStatus.lessons_planned} bài
                  </span>
                </div>
              )}
              {generationStatus.final_count && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-600">Tổng nội dung:</span>
                  <span className="font-medium">{generationStatus.final_count} items</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

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
