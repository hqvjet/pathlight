"use client";

import { use, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { courseApi } from '@/lib/api/course';
import { userApi } from '@/lib/api/user';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { showToast } from '@/utils/toast';
import { Lightbulb } from 'lucide-react';
import { JSX } from 'react/jsx-runtime';
import { MathRenderer } from '@/components/common/MathRenderer';

interface LessonDetailApi {
  lesson_id: string;
  course_id: string;
  title: string;
  overview: string;
  content: string;
  duration: number;
  finish: boolean;
  locked?: boolean;
}

interface AssessmentItemApi {
  assessment_id: string;
  lesson_id: string;
  question: string;
  hint?: string | null;
  has_hint?: boolean;  // Flag from backend to show hint button
  explanation?: string | null;
  difficulty?: string | number | null;
  option1: string;
  option2: string;
  option3: string;
  option4: string;
  answer?: number;
}

interface AssessmentListResponseApi {
  status: number;
  assessments?: AssessmentItemApi[];
  message?: string;
}

interface LessonTestSubmitResultItemApi {
  assessment_id: string;
  selected_answer: number;
  correct_answer: number;
  is_correct: boolean;
  difficulty?: number | null;
  gained_exp: number;
  penalty_exp: number;
}

interface LessonTestSubmitResultApi {
  score: number;
  correct_count: number;
  total: number;
  earned_exp: number;
  penalty_exp: number;
  applied_exp: number;
  passed: boolean;
  pass_threshold: number;
  answers: LessonTestSubmitResultItemApi[];
}

interface ExperienceSnapshotApi {
  gained_exp: number;
  new_level?: number | null;
  new_exp?: number | null;
  require_exp?: number | null;
  exp_needed_for_next?: number | null;
  rank?: number | null;
}

interface LessonTestSubmitResponseApi {
  status: number;
  result?: LessonTestSubmitResultApi;
  message?: string;
  experience?: ExperienceSnapshotApi;
}

interface LessonListItemApi {
  lesson_id: string;
  title: string;
  finish: boolean;
  locked?: boolean;
  order?: number;
}

type ContentBlock =
  | { type: 'heading'; level: number; text: string; id: string }
  | { type: 'paragraph'; text: string }
  | { type: 'code'; text: string; lang: string };

interface LessonListResponseApi {
  status: number;
  lessons?: LessonListItemApi[];
  message?: string;
}

interface UserInfoApi {
  status: number;
  Info?: {
    level?: number;
    current_exp?: number;
    require_exp?: number;
  };
  message?: string;
}

type PageProps = { params: Promise<{ courseId: string; lessonId: string }> };

type NormalizedOption = {
  id: string;
  content: string;
  isCorrect: boolean;
};

type NormalizedQuestion = {
  id: string;
  question: string;
  options: NormalizedOption[];
  hint?: string;
  has_hint?: boolean;  // Flag to show hint button
  explanation?: string;
  level?: number;
  difficult_level_id?: number;
};

const HINT_COST = 50;
const requiredExpForLevel = (level: number) => 200 + 75 * Math.max(0, level - 1);

export default function LessonDetailPage({ params }: PageProps) {
  const { courseId, lessonId } = use(params);
  const router = useRouter();
  const [lesson, setLesson] = useState<LessonDetailApi | null>(null);
  const [assessments, setAssessments] = useState<AssessmentItemApi[]>([]);
  const [lessons, setLessons] = useState<LessonListItemApi[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [score, setScore] = useState<number | null>(null);
  const [passed, setPassed] = useState(false);
  const [earnedExp, setEarnedExp] = useState<number | null>(null);
  const [submissionResult, setSubmissionResult] = useState<LessonTestSubmitResultApi | null>(null);
  const [experience, setExperience] = useState<ExperienceSnapshotApi | null>(null);
  const [showTest, setShowTest] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const contentRef = useRef<HTMLDivElement | null>(null);
  const [reviewMode, setReviewMode] = useState(false);
  const [tocOpen, setTocOpen] = useState(true);
  const [visibleHints, setVisibleHints] = useState<Record<string, boolean>>({});
  const [visibleExplanations, setVisibleExplanations] = useState<Record<string, boolean>>({});
  const [playerLevel, setPlayerLevel] = useState(1);
  const [playerExp, setPlayerExp] = useState(0);
  const [requireExp, setRequireExp] = useState(() => requiredExpForLevel(1));

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!courseId || !lessonId) {
        setError('Thiếu tham số khóa học hoặc bài học');
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const [detailResp, assessResp, listResp, userResp] = await Promise.all([
          courseApi.getLessonDetail(courseId, lessonId),
          courseApi.listAssessments(courseId, lessonId, { include_hints: false, include_explanations: false }),
          courseApi.listLessons(courseId),
          userApi.getInfo(),
        ]);

        const detailData = detailResp.data as LessonDetailApi & { status?: number; message?: string };
        const assessData = assessResp.data as AssessmentListResponseApi;
        const listData = listResp.data as LessonListResponseApi;

        if (detailData.status && detailData.status !== 200) {
          throw new Error(detailData.message || 'Không thể tải bài học');
        }
        
        // Check if lesson is locked
        if (detailData.locked) {
          throw new Error('Bạn cần hoàn thành các bài học trước đó trước khi truy cập bài học này');
        }
        
        if (assessData?.status !== 200 || !assessData.assessments || assessData.assessments.length === 0) {
          throw new Error(assessData?.message || 'Không thể tải bài kiểm tra');
        }

        if (!cancelled) {
          const parseOrder = (title: string, idx: number) => {
            const match = title.match(/^(\d+)/);
            return match ? Number(match[1]) : idx + 1;
          };
          const sortedLessons = (listData?.lessons || []).map((l, idx) => ({
            ...l,
            order: parseOrder(l.title, idx),
          })).sort((a, b) => (a.order || 0) - (b.order || 0));

          const userInfoPayload = (userResp?.data as UserInfoApi | undefined)?.Info || null;
          const initialLevel = userInfoPayload?.level ?? 1;
          const initialExp = Math.max(0, userInfoPayload?.current_exp ?? 0);
          const initialRequireExp = Math.max(1, userInfoPayload?.require_exp ?? requiredExpForLevel(initialLevel));

          setPlayerLevel(initialLevel);
          setPlayerExp(initialExp);
          setRequireExp(initialRequireExp);

          setLesson(detailData as LessonDetailApi);
          setAssessments(assessData.assessments || []);
          setLessons(sortedLessons);
        }
      } catch (e: unknown) {
        const message = e instanceof Error ? e.message : 'Không thể tải dữ liệu bài học';
        if (!cancelled) setError(message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [courseId, lessonId]);

  const nextLessonId = useMemo(() => {
    const idx = lessons.findIndex((l) => l.lesson_id === lessonId);
    if (idx === -1) return null;
    return lessons[idx + 1]?.lesson_id || null;
  }, [lessons, lessonId]);

  const questions = useMemo<NormalizedQuestion[]>(() => {
    if (!assessments?.length) return [];
    return assessments.map((a, idx) => ({
      id: a.assessment_id || `assessment-${idx}`,
      question: a.question,
      hint: a.hint || undefined,
      has_hint: a.has_hint || false,  // Flag from backend
      explanation: a.explanation || undefined,
      level: typeof a.difficulty === 'number' ? a.difficulty : undefined,
      difficult_level_id: typeof a.difficulty === 'number' ? a.difficulty : undefined,
      options: [a.option1, a.option2, a.option3, a.option4]
        .map((content, oIdx) => ({ id: String(oIdx + 1), content, isCorrect: false }))
        .filter((opt) => Boolean(opt.content)),
    }));
  }, [assessments]);

  const totalQuestions = questions.length;

  const answeredCount = useMemo(
    () => questions.reduce((acc, q) => acc + (answers[q.id] ? 1 : 0), 0),
    [answers, questions],
  );

  const answerMap = useMemo(() => {
    if (!submissionResult) return {} as Record<string, LessonTestSubmitResultItemApi>;
    return submissionResult.answers.reduce((acc, item) => {
      acc[item.assessment_id] = item;
      return acc;
    }, {} as Record<string, LessonTestSubmitResultItemApi>);
  }, [submissionResult]);

  const hintCount = useMemo(() => Object.values(visibleHints).filter(Boolean).length, [visibleHints]);
  const hintSpent = useMemo(() => hintCount * HINT_COST, [hintCount]);
  const availableExp = useMemo(() => Math.max(0, playerExp - hintSpent), [playerExp, hintSpent]);

  const handleAnswer = (qaId: string, option: string) => {
    setAnswers((prev) => ({ ...prev, [qaId]: option }));
  };

  const handleSubmit = async () => {
    if (!questions.length) {
      showToast.info('Bài học này chưa có câu hỏi');
      return;
    }
    if (answeredCount < questions.length) {
      showToast.info('Vui lòng trả lời hết các câu hỏi');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        answers: questions.map((q) => ({ assessment_id: q.id, answer: Number(answers[q.id]) || 0 })),
      };
      const resp = await courseApi.submitAssessments(courseId, lessonId, payload);
      const data = resp.data as LessonTestSubmitResponseApi;
      if (data.status !== 200 || !data.result) {
        throw new Error(data.message || 'Chấm bài không thành công');
      }
      const result = data.result;
      const snapshot = data.experience || null;
      setSubmissionResult(result);
      setExperience(snapshot);
      setScore(result.score);
      setPassed(result.passed);
      const awardedExp = Math.max(0, (snapshot?.gained_exp ?? result.applied_exp ?? 0));
      const adjustedExp = Math.max(0, awardedExp - hintSpent);
      setEarnedExp(adjustedExp);
      setReviewMode(true);
      showToast.success(result.passed ? 'Đạt yêu cầu 80%. Bạn có thể sang bài tiếp theo.' : 'Chưa đạt 80%. Hãy thử lại.');
      if (result.passed) {
        try {
          await userApi.logActivity('complete_lesson');
          if (!nextLessonId) {
            await userApi.logActivity('complete_course');
          }
        } catch {
          // ignore activity log errors
        }
      }

      if (snapshot) {
        if (typeof snapshot.new_exp === 'number') {
          setPlayerExp(Math.max(0, snapshot.new_exp));
        }
        if (typeof snapshot.new_level === 'number' && snapshot.new_level > 0) {
          setPlayerLevel(snapshot.new_level);
        }
        if (typeof snapshot.require_exp === 'number' && snapshot.require_exp > 0) {
          setRequireExp(snapshot.require_exp);
        }
      } else {
        // Fallback to local progression if server does not provide experience snapshot
        let expPool = playerExp + adjustedExp;
        let nextLevel = playerLevel;
        let nextRequireExp = requireExp;
        while (expPool >= nextRequireExp) {
          expPool -= nextRequireExp;
          nextLevel += 1;
          nextRequireExp = requiredExpForLevel(nextLevel);
        }
        setPlayerExp(expPool);
        setPlayerLevel(nextLevel);
        setRequireExp(nextRequireExp);
      }

      if (result.passed) {
        setShowTest(true);
      }
    } catch (e: unknown) {
      showToast.error(e instanceof Error ? e.message : 'Không thể chấm bài');
    } finally {
      setSubmitting(false);
    }
  };

  const goNext = () => {
    if (!nextLessonId) return;
    router.push(`/user/my-courses/${courseId}/lessons/${nextLessonId}`);
  };

  const handleOpenTest = () => {
    if (!questions.length) {
      showToast.info('Bài học này chưa có câu hỏi');
      return;
    }
    setReviewMode(false);
    setSubmissionResult(null);
    setExperience(null);
    setScore(null);
    setPassed(false);
    setEarnedExp(null);
    setVisibleHints({});
    setVisibleExplanations({});
    setCurrentQuestion(0);
    setShowTest(true);
  };

  const handleReset = () => {
    setAnswers({});
    setScore(null);
    setEarnedExp(null);
    setPassed(false);
    setReviewMode(false);
    setSubmissionResult(null);
    setExperience(null);
    setVisibleHints({});
    setVisibleExplanations({});
    setCurrentQuestion(0);
  };

  const handleShowHint = async (questionId: string) => {
    if (visibleHints[questionId]) return;
    
    const target = assessments.find((a) => (a.assessment_id || a.question) === questionId || a.assessment_id === questionId);
    if (!target || !target.has_hint) {
      showToast.info('Câu hỏi này không có gợi ý.');
      return;
    }

    try {
      // Call hint API - this will deduct exp on server side
      const resp = await courseApi.getHint(courseId, lessonId, target.assessment_id);
      const data = resp.data;
      
      if (data.status !== 200 || !data.hint) {
        showToast.error(data.message || 'Không thể lấy gợi ý');
        return;
      }

      // Update assessment with hint text
      setAssessments((prev) => 
        prev.map((a) => 
          a.assessment_id === target.assessment_id 
            ? { ...a, hint: data.hint } 
            : a
        )
      );
      
      // Show hint in UI
      setVisibleHints((prev) => ({ ...prev, [questionId]: true }));
      
      // Show penalty notification
      if (data.exp_penalty && data.exp_penalty > 0) {
        showToast.info(`Đã trừ ${data.exp_penalty} EXP để xem gợi ý`);
      }
      
      // Refresh user info to get updated exp
      try {
        const userResp = await userApi.getInfo();
        const userData = userResp.data as UserInfoApi;
        if (userData?.Info?.current_exp !== undefined) {
          setPlayerExp(userData.Info.current_exp);
        }
        if (userData?.Info?.level !== undefined) {
          setPlayerLevel(userData.Info.level);
        }
        if (userData?.Info?.require_exp !== undefined) {
          setRequireExp(userData.Info.require_exp);
        }
      } catch {
        // Ignore if can't refresh user info
      }
    } catch (e: unknown) {
      showToast.error(e instanceof Error ? e.message : 'Không thể lấy gợi ý');
    }
  };

  const handleShowExplanation = (questionId: string) => {
    if (!submissionResult) {
      showToast.info('Nộp bài để xem giải thích');
      return;
    }
    if (visibleExplanations[questionId]) return;
    const ensureExplanation = async () => {
      const target = assessments.find((a) => (a.assessment_id || a.question) === questionId || a.assessment_id === questionId);
      if (target?.explanation) return true;
      try {
        const resp = await courseApi.listAssessments(courseId, lessonId, { include_hints: true, include_explanations: true });
        const data = resp.data as AssessmentListResponseApi;
        if (data?.assessments?.length) {
          setAssessments((prev) => {
            const map = new Map<string, AssessmentItemApi>();
            prev.forEach((a) => map.set(a.assessment_id || a.question, a));
            data.assessments?.forEach((a) => {
              const key = a.assessment_id || a.question;
              map.set(key, { ...(map.get(key) || {}), ...a });
            });
            return Array.from(map.values());
          });
          const updated = data.assessments.find((a) => (a.assessment_id || a.question) === questionId || a.assessment_id === questionId);
          return Boolean(updated?.explanation);
        }
      } catch {
        /* ignore */
      }
      return false;
    };

    ensureExplanation().then((hasExplanation) => {
      if (!hasExplanation) {
        showToast.info('Không có lời giải cho câu này.');
        return;
      }
      setVisibleExplanations((prev) => ({ ...prev, [questionId]: true }));
    });
  };

  const applyFormat = (mode: 'bold' | 'highlight' | 'italic' | 'underline') => {
    if (typeof window === 'undefined') return;
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return;
    const range = selection.getRangeAt(0);
    if (range.collapsed) {
      showToast.info('Chọn đoạn nội dung để bôi');
      return;
    }
    if (contentRef.current && !contentRef.current.contains(range.commonAncestorContainer)) {
      showToast.info('Chỉ áp dụng cho nội dung bài học');
      return;
    }
    const classMap: Record<'bold' | 'highlight' | 'italic' | 'underline', string[]> = {
      bold: ['font-semibold'],
      italic: ['italic'],
      underline: ['underline', 'decoration-2', 'decoration-orange-400', 'underline-offset-4'],
      highlight: ['bg-yellow-200', 'px-0.5'],
    };

    const ancestor = range.commonAncestorContainer instanceof Element
      ? range.commonAncestorContainer
      : range.commonAncestorContainer.parentElement;
    const existingWrapper = ancestor?.closest?.('[data-format-wrapper="true"]') || null;

    const addClasses = (el: Element) => {
      classMap[mode].forEach((cls) => el.classList.add(cls));
    };

    if (existingWrapper && contentRef.current?.contains(existingWrapper)) {
      addClasses(existingWrapper);
      return;
    }

    const wrapper = document.createElement('span');
    wrapper.setAttribute('data-format-wrapper', 'true');
    addClasses(wrapper);
    try {
      range.surroundContents(wrapper);
      selection.removeAllRanges();
      selection.addRange(range);
    } catch (e) {
      console.error(e);
      showToast.info('Không thể áp dụng định dạng cho vùng chọn này');
    }
  };

  const contentBlocks = useMemo<ContentBlock[]>(() => {
    const raw = lesson?.content || '';
    if (!raw.trim()) return [{ type: 'paragraph', text: 'Nội dung sẽ được cập nhật.' }];

    const parts: ContentBlock[] = [];
    const segments = raw.split(/```/);
    segments.forEach((seg, idx) => {
      if (idx % 2 === 1) {
        const trimmed = seg.trim();
        const [firstLine, ...rest] = trimmed.split('\n');
        const isLang = /^(json|xml|html|yaml|yml)$/i.test(firstLine.trim());
        const lang = isLang ? firstLine.trim().toUpperCase() : 'CODE';
        const code = isLang ? rest.join('\n') : trimmed;
        parts.push({ type: 'code', text: code, lang });
      } else {
        const lines = seg.split('\n');
        lines.forEach((line, lineIdx) => {
          const trimmed = line.trim();
          if (!trimmed) return;
          if (trimmed.startsWith('#')) {
            const level = trimmed.match(/^#+/)?.[0].length || 1;
            const text = trimmed.replace(/^#+\s*/, '') || `Mục ${lineIdx + 1}`;
            const id = `section-${idx}-${lineIdx}-${text.toLowerCase().replace(/\s+/g, '-')}`;
            parts.push({ type: 'heading', level, text, id });
          } else {
            parts.push({ type: 'paragraph', text: line });
          }
        });
      }
    });
    return parts.length ? parts : [{ type: 'paragraph', text: raw }];
  }, [lesson?.content]);

  const tocHeadings = useMemo(
    () => contentBlocks.filter((b) => b.type === 'heading') as Array<{ type: 'heading'; level: number; text: string; id: string }>,
    [contentBlocks],
  );

  const tocEntries = useMemo(() => {
    const counters: number[] = [];
    return tocHeadings.map((h) => {
      const level = Math.min(Math.max(h.level, 1), 6);
      counters.length = level;
      counters[level - 1] = (counters[level - 1] || 0) + 1;
      for (let i = level; i < counters.length; i += 1) {
        if (counters[i] === undefined) counters[i] = 0;
      }
      const number = counters.join('.');
      return { ...h, number };
    });
  }, [tocHeadings]);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-white rounded-xl p-10 text-center border border-gray-100 shadow-sm">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-orange-500 mx-auto" />
          <p className="mt-4 text-gray-600">Đang tải bài học...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-red-50 text-red-700 rounded-xl p-4 border border-red-200 text-sm">{error}</div>
      </div>
    );
  }

  if (!lesson) return null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex items-center gap-3 text-sm text-gray-600">
        <Link href={`/user/my-courses/${courseId}`} className="text-orange-600 font-semibold hover:text-orange-700">← Quay lại khóa học</Link>
        <span className="text-gray-400">/</span>
        <span className="font-semibold text-gray-800">{lesson.title}</span>
      </div>

      <Card className="shadow-sm border-gray-100">
        <CardHeader className="pb-3">
          <CardTitle className="text-xl text-gray-900">{lesson.title}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-gray-800 leading-6">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div className="text-sm text-gray-600 whitespace-pre-wrap max-w-3xl">
              {lesson.overview || 'Chưa có mô tả'}
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="flex items-center gap-1 px-2 py-1 rounded-md border border-gray-200 bg-white shadow-sm">
                <span className="text-[11px] uppercase text-gray-500">Định dạng</span>
                <button
                  type="button"
                  onClick={() => applyFormat('bold')}
                  className="h-8 w-8 rounded-md border border-gray-200 bg-gray-50 text-gray-800 font-bold hover:border-orange-200"
                  title="Bôi đậm"
                >
                  B
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('italic')}
                  className="h-8 w-8 rounded-md border border-gray-200 bg-gray-50 italic text-gray-800 font-semibold hover:border-orange-200"
                  title="In nghiêng"
                >
                  I
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('underline')}
                  className="h-8 w-8 rounded-md border border-gray-200 bg-gray-50 text-gray-800 font-semibold underline decoration-2 underline-offset-4 hover:border-orange-200"
                  title="Gạch dưới"
                >
                  U
                </button>
                <button
                  type="button"
                  onClick={() => applyFormat('highlight')}
                  className="h-8 w-8 rounded-md border border-gray-200 bg-gray-50 text-yellow-600 font-semibold hover:border-orange-200"
                  title="Bôi vàng"
                >
                  ⬒
                </button>
              </div>
              <button
                type="button"
                onClick={() => setTocOpen((v) => !v)}
                className="h-9 w-9 rounded-md border border-gray-200 bg-white shadow-sm flex items-center justify-center text-gray-700 hover:border-orange-200"
                title={tocOpen ? 'Ẩn mục trong bài' : 'Hiện mục trong bài'}
              >
                <span className="font-semibold text-sm" aria-hidden="true">|||</span>
              </button>
            </div>
          </div>

          <div className={cn('grid gap-4', tocOpen ? 'lg:grid-cols-[220px,1fr]' : 'grid-cols-1')}> 
            {tocOpen && (
              <aside className="rounded-xl border border-gray-100 bg-gray-50 p-3 space-y-2 text-xs text-gray-700 h-fit sticky top-4 self-start">
                <p className="font-semibold text-gray-900 text-sm">Mục trong bài</p>
                <div className="space-y-2 max-h-[720px] overflow-auto pr-1">
                  {tocEntries.map((h) => (
                    <button
                      key={h.id}
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        const el = document.getElementById(h.id);
                        el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                      }}
                      className="w-full text-left flex items-start gap-2 rounded-md px-2 py-1 hover:bg-white hover:border hover:border-orange-200"
                    >
                      <span className="text-sm font-semibold text-gray-700 min-w-[32px]">{h.number}</span>
                      <span className="text-sm text-gray-800 leading-5">{h.text}</span>
                    </button>
                  ))}
                </div>
              </aside>
            )}

            <div
              ref={contentRef}
              className="prose prose-slate max-w-none bg-white border border-gray-100 rounded-xl p-6 max-h-[720px] overflow-auto shadow-sm"
            >
              {contentBlocks.map((block, idx) => {
                if (block.type === 'heading') {
                  const tagLevel = Math.min(block.level + 2, 6);
                  const Tag = (`h${tagLevel}` as keyof JSX.IntrinsicElements);
                  const number = tocEntries.find((h) => h.id === block.id)?.number;
                  return (
                    <Tag key={block.id + idx} id={block.id} className="scroll-mt-24 font-bold text-gray-900 flex items-center gap-2">
                      {number && <span className="text-sm text-gray-500 font-semibold">{number}</span>}
                      <span>{block.text}</span>
                    </Tag>
                  );
                }
                if (block.type === 'code') {
                  return (
                    <pre
                      key={`code-${idx}`}
                      className="mt-4 rounded-lg border border-gray-200 bg-gray-900 text-gray-100 text-sm overflow-x-auto"
                    >
                      <div className="px-3 py-2 text-xs uppercase tracking-wide text-gray-400 border-b border-gray-800">{block.lang}</div>
                      <code className="block px-3 py-3 whitespace-pre">{block.text}</code>
                    </pre>
                  );
                }
                return (
                  <p key={idx} className="leading-7 text-gray-800 whitespace-pre-wrap">
                    <MathRenderer text={block.text} />
                  </p>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="shadow-sm border-gray-100">
        <CardHeader className="pb-3 flex items-center justify-between">
          <CardTitle className="text-lg text-gray-900">Bài test trắc nghiệm</CardTitle>
          <div className="flex items-center gap-2">
            <Badge className="bg-orange-500 text-white border-none">Yêu cầu ≥ 80%</Badge>
            <button
              type="button"
              onClick={handleOpenTest}
              className="px-3 py-1.5 rounded-md bg-orange-500 text-white text-sm font-semibold hover:bg-orange-600"
            >
              Bắt đầu test
            </button>
          </div>
        </CardHeader>
        <CardContent className="text-sm text-gray-600">
          Nhấn &quot;Bắt đầu test&quot; để mở bài kiểm tra ở chế độ toàn màn hình. Kết quả sẽ được dùng để mở khóa bài tiếp theo.
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-700">
            <span className="px-2 py-1 rounded-md bg-orange-50 text-orange-700 font-semibold">EXP hiện có: {availableExp}</span>
            <span className="px-2 py-1 rounded-md bg-slate-100 text-slate-700">Lv {playerLevel}</span>
            <span className="px-2 py-1 rounded-md bg-slate-100 text-slate-700">Cần {requireExp} EXP lên Lv {playerLevel + 1}</span>
            <span className="px-2 py-1 rounded-md bg-amber-50 text-amber-700">Gợi ý: -50 EXP/lần</span>
          </div>
        </CardContent>
      </Card>

      {showTest && questions.length > 0 && (
        <div className="fixed inset-0 z-50 bg-gray-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative w-full max-w-5xl max-h-[90vh] bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-wide text-orange-600 font-semibold">Bài test</p>
                <p className="text-lg font-semibold text-gray-900">{lesson?.title || 'Bài kiểm tra'}</p>
                <p className="text-xs text-gray-500">Yêu cầu ≥ 80% để qua bài · Đã trả lời {answeredCount}/{totalQuestions}</p>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-600">
                {score !== null && (
                  <button
                    type="button"
                    onClick={() => setReviewMode((v) => !v)}
                    className="px-3 py-1.5 rounded-md border border-gray-200 bg-white hover:border-orange-200 font-semibold"
                  >
                    {reviewMode ? 'Đóng xem lại' : 'Xem lại kết quả'}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setShowTest(false)}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Đóng
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-hidden">
              <div className="grid lg:grid-cols-[220px,1fr] h-full">
                <aside className="border-r border-gray-200 bg-gray-50 p-4 overflow-auto space-y-3">
                  <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Danh sách câu</p>
                  <div className="grid grid-cols-4 sm:grid-cols-5 gap-2">
                    {questions.map((q, idx) => {
                      const answered = Boolean(answers[q.id]);
                      const isCurrent = currentQuestion === idx;
                      const serverItem = answerMap[q.id];
                      const isIncorrect = reviewMode && serverItem && serverItem.is_correct === false;
                      return (
                        <button
                          key={q.id}
                          type="button"
                          onClick={() => setCurrentQuestion(idx)}
                          className={cn(
                            'h-10 rounded-md border text-sm font-semibold flex items-center justify-center',
                            isCurrent ? 'border-orange-400 bg-orange-50 text-orange-700' : 'border-gray-200 bg-white text-gray-700',
                            answered && 'border-green-200 bg-green-50 text-green-700',
                            isIncorrect && 'border-red-200 bg-red-50 text-red-700'
                          )}
                        >
                          {idx + 1}
                        </button>
                      );
                    })}
                  </div>
                </aside>
                <main className="overflow-auto p-6 space-y-4">
                  {questions[currentQuestion] && (
                    <div className="rounded-lg border border-gray-200 bg-white p-5 space-y-4 shadow-sm">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-2 flex-1">
                          <span className="text-sm font-semibold text-orange-600">Câu {currentQuestion + 1}.</span>
                          <div className="space-y-1">
                            <p className="text-base font-semibold text-gray-900 leading-6">{questions[currentQuestion].question}</p>
                            {(questions[currentQuestion].level || questions[currentQuestion].difficult_level_id) && (
                              <Badge variant="outline" className="border-orange-200 text-orange-700">
                                Độ khó {questions[currentQuestion].level ? `${questions[currentQuestion].level}/5` : questions[currentQuestion].difficult_level_id}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {questions[currentQuestion].has_hint && (
                            <button
                              type="button"
                              onClick={() => handleShowHint(questions[currentQuestion].id)}
                              disabled={Boolean(visibleHints[questions[currentQuestion].id])}
                              className={cn(
                                'px-3 py-1.5 rounded-md border text-sm font-semibold flex items-center gap-2',
                                visibleHints[questions[currentQuestion].id]
                                  ? 'border-amber-200 bg-amber-50 text-amber-700'
                                  : 'border-gray-200 bg-white text-gray-700 hover:border-orange-200'
                              )}
                            >
                              <Lightbulb className="w-4 h-4" />
                              {visibleHints[questions[currentQuestion].id] ? 'Đã xem gợi ý' : 'Gợi ý'}
                            </button>
                          )}
                          {submissionResult && (
                            <button
                              type="button"
                              onClick={() => handleShowExplanation(questions[currentQuestion].id)}
                              disabled={Boolean(visibleExplanations[questions[currentQuestion].id])}
                              className={cn(
                                'px-3 py-1.5 rounded-md border text-sm font-semibold flex items-center gap-2',
                                visibleExplanations[questions[currentQuestion].id]
                                  ? 'border-sky-200 bg-sky-50 text-sky-700'
                                  : 'border-gray-200 bg-white text-gray-700 hover:border-orange-200'
                              )}
                            >
                              <span aria-hidden="true">ℹ️</span>
                              {visibleExplanations[questions[currentQuestion].id] ? 'Đã hiện giải thích' : 'Hiện giải thích'}
                            </button>
                          )}
                        </div>
                      </div>

                      {visibleHints[questions[currentQuestion].id] && questions[currentQuestion].hint && (
                        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 space-y-1">
                          <div className="font-semibold">Gợi ý</div>
                          <div>{questions[currentQuestion].hint}</div>
                        </div>
                      )}

                      {visibleExplanations[questions[currentQuestion].id] && questions[currentQuestion].explanation && (
                        <div className="rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-800 space-y-1">
                          <div className="font-semibold">Giải thích</div>
                          <div>{questions[currentQuestion].explanation}</div>
                        </div>
                      )}

                      <div className="grid sm:grid-cols-2 gap-3">
                          {questions[currentQuestion].options.map((opt) => {
                          const q = questions[currentQuestion];
                          const userChoice = answers[q.id];
                          const isSelected = userChoice === opt.id;
                          const showReview = reviewMode;
                            const serverItem = answerMap[q.id];
                            const serverCorrectId = serverItem?.correct_answer;
                            const isCorrectOption = serverCorrectId ? String(serverCorrectId) === opt.id : opt.isCorrect;
                            const isIncorrectChoice = showReview && isSelected && !isCorrectOption;
                          return (
                            <label
                              key={opt.id}
                              className={cn(
                                'flex items-start gap-2 rounded-md border px-3 py-2 text-sm cursor-pointer transition',
                                isSelected ? 'border-orange-300 bg-orange-50' : 'border-gray-200 bg-gray-50',
                                isIncorrectChoice && 'border-red-200 bg-red-50 text-red-700',
                                !reviewMode && 'hover:border-orange-200'
                              )}
                            >
                              <input
                                type="radio"
                                name={q.id}
                                className="mt-1"
                                checked={isSelected}
                                onChange={() => handleAnswer(q.id, opt.id)}
                                disabled={reviewMode}
                              />
                              <div className="space-y-1">
                                <span>{opt.content}</span>
                                {reviewMode && isSelected && (
                                  <span className={cn('text-xs font-semibold', isIncorrectChoice ? 'text-red-600' : 'text-gray-700')}>
                                    {isIncorrectChoice ? 'Bạn chọn (sai)' : 'Bạn chọn'}
                                  </span>
                                )}
                              </div>
                            </label>
                          );
                        })}
                      </div>
                      <div className="flex items-center justify-between pt-2 text-sm text-gray-600">
                        <span>
                          Đã trả lời {answeredCount}/{totalQuestions}
                          {hintSpent > 0 && ` · Đã dùng ${hintSpent} EXP cho gợi ý (còn ${availableExp})`}
                        </span>
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => questions[currentQuestion]?.id && handleShowHint(questions[currentQuestion].id)}
                            disabled={
                              !questions[currentQuestion]?.hint ||
                              Boolean(questions[currentQuestion] && visibleHints[questions[currentQuestion].id])
                            }
                            className={cn(
                              'px-3 py-1.5 rounded-md border border-gray-200 bg-white text-gray-700 hover:border-orange-200 flex items-center gap-1',
                              (!questions[currentQuestion]?.hint || visibleHints[questions[currentQuestion]?.id || '']) && 'opacity-60 cursor-not-allowed'
                            )}
                          >
                            <Lightbulb className="h-4 w-4" />
                            Gợi ý
                          </button>
                          <button
                            type="button"
                            onClick={() => setCurrentQuestion((prev) => Math.max(0, prev - 1))}
                            className="px-3 py-1.5 rounded-md border border-gray-200 bg-white text-gray-700 hover:border-orange-200"
                          >
                            Trước
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              if (currentQuestion === totalQuestions - 1) {
                                handleSubmit();
                              } else {
                                setCurrentQuestion((prev) => Math.min(totalQuestions - 1, prev + 1));
                              }
                            }}
                            className="px-3 py-1.5 rounded-md border border-orange-200 bg-orange-50 text-orange-700 hover:border-orange-300"
                          >
                            {currentQuestion === totalQuestions - 1 ? 'Nộp bài' : 'Tiếp'}
                          </button>
                        </div>
                      </div>
                      {questions[currentQuestion].explanation && (reviewMode || visibleHints[questions[currentQuestion].id]) && (
                        <div className="rounded-md border border-blue-100 bg-blue-50 px-3 py-2 text-sm text-blue-800">
                          <p className="font-semibold">Giải thích</p>
                          <p className="leading-6">{questions[currentQuestion].explanation}</p>
                        </div>
                      )}
                      {reviewMode && (
                        <p className="text-xs text-gray-500">Chế độ xem lại: hiển thị đúng/sai và đánh dấu đáp án đúng.</p>
                      )}
                    </div>
                  )}
                </main>
              </div>
            </div>
            <div className="flex items-center gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
              <button
                type="button"
                onClick={handleSubmit}
                disabled={submitting}
                className="px-5 py-2 rounded-md bg-orange-500 text-white text-sm font-semibold hover:bg-orange-600 disabled:opacity-50"
              >
                Nộp bài
              </button>
              <button
                type="button"
                onClick={handleReset}
                className="px-4 py-2 rounded-md border border-gray-200 bg-white text-sm font-semibold text-gray-700 hover:border-orange-200"
              >
                Làm lại
              </button>
              {score !== null && (
                <div className="flex flex-wrap items-center gap-3 text-sm font-semibold">
                  <span className={passed ? 'text-emerald-700' : 'text-red-600'}>
                    Điểm: {score}% {passed ? '(Đạt yêu cầu)' : '(Chưa đạt)'}
                  </span>
                  {submissionResult && (
                    <span className="text-blue-700">EXP hệ thống: {experience?.gained_exp ?? submissionResult.applied_exp}</span>
                  )}
                  <span className="text-blue-700">EXP sau gợi ý: {earnedExp ?? 0}</span>
                  {hintSpent > 0 && <span className="text-gray-500 font-normal">(-{hintSpent} EXP do mở gợi ý)</span>}
                  <span className="text-gray-700">Lv {playerLevel} · Còn {requireExp - playerExp} EXP để lên Lv {playerLevel + 1}</span>
                </div>
              )}
              {passed && nextLessonId && (
                <button
                  type="button"
                  onClick={goNext}
                  className="ml-auto px-5 py-2 rounded-md bg-emerald-500 text-white text-sm font-semibold hover:bg-emerald-600"
                >
                  Sang bài tiếp theo
                </button>
              )}
              {passed && !nextLessonId && (
                <span className="text-sm text-emerald-700 font-semibold">Đã hoàn thành bài cuối cùng.</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
