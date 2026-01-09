'use client';

import { use, useEffect, useState, useRef, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { quizApi } from '@/lib/api/quiz';
import { userApi } from '@/lib/api/user';
import { showToast } from '@/utils/toast';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { RotateCcw, CheckCircle2, Clock, Zap, Snowflake, Eye, X, Award, Target, Lightbulb, SkipForward } from 'lucide-react';

type AnswerDisplayMode = 'immediate' | 'after_submit';

interface QuizCard {
  card_id: string;
  question: string;
  hint: string | null;
  explanation: string | null;
  difficulty: string;
  option1: string;
  option2: string;
  option3: string;
  option4: string;
  answer?: number; // The correct answer index (1-4), only included if requested
}

interface PowerUp {
  id: string;
  name: string;
  description: string;
  iconType: 'zap' | 'snowflake' | 'eye' | 'lightbulb' | 'skip'; // Icon identifier
  cost: number; // EXP cost
  maxUses: number;
  usesLeft: number;
  active: boolean;
}

interface QuizDetail {
  quiz_id: string;
  title: string;
  overview: string;
  level: string;
  duration: number;
  num_questions: number;
  previous_score: number | null;
  finish: boolean;
  publish: boolean;
  cards: QuizCard[];
}

interface QuizSubmitResponse {
  status: number;
  message?: string;
  result?: {
    score: number;
    correct_count: number;
    total: number;
    answers: Array<{
      card_id: string;
      selected_answer: number;
      correct_answer: number;
      is_correct: boolean;
      difficulty: string;
      explanation: string;
    }>;
  };
  experience?: {
    gained_exp?: number;
    total_exp?: number;
    level?: number;
    rank?: string;
  };
}

type PageProps = { params: Promise<{ quizId: string }> };

export default function QuizPlayPage({ params }: PageProps) {
  const { quizId } = use(params);
  const searchParams = useSearchParams();
  const answerDisplayMode = (searchParams.get('mode') as AnswerDisplayMode) || 'after_submit';
  
  const [quiz, setQuiz] = useState<QuizDetail | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<QuizSubmitResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAnswerFeedback, setShowAnswerFeedback] = useState(false);
  
  const [timeLeft, setTimeLeft] = useState(0);
  const [timePerQuestion, setTimePerQuestion] = useState(0);
  const [currentPoints, setCurrentPoints] = useState(100);
  const [totalScore, setTotalScore] = useState(0);
  const [questionScores, setQuestionScores] = useState<Record<string, number>>({});
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const [timerFrozen, setTimerFrozen] = useState(false);
  const freezeTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isProcessingTimeout = useRef(false);
  
  // Power-ups
  const [powerUps, setPowerUps] = useState<PowerUp[]>([
    {
      id: 'double_points',
      name: 'x2 Điểm',
      description: 'Nhân đôi điểm câu hiện tại',
      iconType: 'zap',
      cost: 250,
      maxUses: 2,
      usesLeft: 2,
      active: false,
    },
    {
      id: 'freeze_time',
      name: 'Đóng băng',
      description: 'Dừng đồng hồ 30 giây',
      iconType: 'snowflake',
      cost: 300,
      maxUses: 1,
      usesLeft: 1,
      active: false,
    },
    {
      id: 'fifty_fifty',
      name: '50/50',
      description: 'Loại bỏ 2 đáp án sai',
      iconType: 'eye',
      cost: 200,
      maxUses: 2,
      usesLeft: 2,
      active: false,
    },
    {
      id: 'show_hint',
      name: 'Gợi ý',
      description: 'Hiển thị gợi ý cho câu hỏi',
      iconType: 'lightbulb',
      cost: 150,
      maxUses: 3,
      usesLeft: 3,
      active: false,
    },
    {
      id: 'skip',
      name: 'Bỏ qua',
      description: 'Nhận 50% điểm và qua câu tiếp',
      iconType: 'skip',
      cost: 350,
      maxUses: 1,
      usesLeft: 1,
      active: false,
    },
  ]);
  const [userExp, setUserExp] = useState(0);
  const [eliminatedOptions, setEliminatedOptions] = useState<Record<string, number[]>>({}); // card_id -> [eliminated originalIndex]
  const [showHint, setShowHint] = useState<Record<string, boolean>>({}); // card_id -> show hint
  const [activatingPowerUp, setActivatingPowerUp] = useState<string | null>(null); // Track which power-up is being activated

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!quizId) return;
      setLoading(true);
      setError(null);
      try {
        await quizApi.start(quizId);
        const resp = await quizApi.getById(quizId, { 
          include_hints: false, 
          include_explanations: true,
          include_answers: answerDisplayMode === 'immediate'
        });
        if (cancelled) return;

        const responseData = resp?.data as { status?: number; quiz?: QuizDetail };
        const data = responseData?.quiz;
        
        if (!data || !data.cards || data.cards.length === 0) {
          throw new Error('Quiz không có câu hỏi');
        }

        setQuiz(data);
        
        // Calculate time per question (convert minutes to seconds)
        const timePerQ = Math.floor((data.duration * 60) / data.cards.length);
        setTimePerQuestion(timePerQ);
        setTimeLeft(timePerQ);
        
        // Fetch user EXP from API using userApi client
        try {
          const userInfoResp = await userApi.getInfo();
          // Backend returns { Info: { current_exp, subscription, ... }, message, status } with capital I
          const responseData = userInfoResp?.data as { Info?: { current_exp?: number; subscription?: number }; info?: { current_exp?: number; subscription?: number } } | undefined;
          // Try both Info (capital) and info (lowercase) for compatibility
          const userInfo = responseData?.Info || responseData?.info;
          
          const exp = userInfo?.current_exp || 0;
          const subscription = userInfo?.subscription || 0;
          
          setUserExp(exp);
          
          // Adjust power-ups based on subscription
          // subscription = 0 (free): 1 use per power-up
          // subscription = 1 (premium): 2 uses per power-up
          // subscription = 2 (pro): 3 uses per power-up
          const usesPerPowerUp = subscription === 0 ? 1 : subscription === 1 ? 2 : 3;
          
          setPowerUps(prev => prev.map(p => ({
            ...p,
            maxUses: usesPerPowerUp,
            usesLeft: usesPerPowerUp,
          })));
        } catch (expError) {
          console.error('Failed to fetch user EXP:', expError);
          setUserExp(0); // Fallback
        }
      } catch (e: unknown) {
        if (!cancelled) {
          const msg = e instanceof Error ? e.message : 'Không thể tải quiz';
          setError(msg);
          showToast.error(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quizId]); // answerDisplayMode intentionally omitted

  const handleTimeUp = useCallback(() => {
    // Prevent duplicate execution
    if (isProcessingTimeout.current) {
      return;
    }
    isProcessingTimeout.current = true;
    
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    const currentCard = quiz?.cards[currentIndex];
    if (!currentCard) {
      isProcessingTimeout.current = false;
      return;
    }

    // Show toast after state updates to avoid setState in render
    setTimeout(() => {
      if (!answers[currentCard.card_id]) {
        showToast.warning('Hết giờ! Câu này sẽ được tính là sai.');
      } else {
        showToast.info('Hết giờ! Chuyển sang câu tiếp theo.');
      }
    }, 0);

    // Move to next question or submit
    setTimeout(() => {
      if (quiz && currentIndex < quiz.cards.length - 1) {
        setTimeLeft(timePerQuestion);
        setCurrentPoints(100);
        setCurrentIndex((i) => i + 1);
      } else {
        // Auto submit on last question
        handleSubmit();
      }
      // Reset flag after transition
      isProcessingTimeout.current = false;
    }, 1500);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quiz, currentIndex, answers, timePerQuestion]); // handleSubmit intentionally omitted to avoid circular dependency

  // Timer countdown
  useEffect(() => {
    if (!quiz || submitted || loading || timerFrozen) return;

    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          // Time's up for this question - use ref to avoid dependency issues
          handleTimeUpRef.current();
          return 0;
        }
        
        // Update current points based on time remaining (100 -> 0)
        const timeProgress = prev / timePerQuestion;
        const points = Math.round(timeProgress * 100); // 100 points at start, 0 at end
        setCurrentPoints(points);
        
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [quiz, submitted, loading, currentIndex, timePerQuestion, timerFrozen]);

  const handleTimeUpRef = useRef(handleTimeUp);
  useEffect(() => {
    handleTimeUpRef.current = handleTimeUp;
  }, [handleTimeUp]);

  const currentCard = quiz?.cards[currentIndex];

  const handleAnswer = (originalIndex: number) => {
    if (!currentCard || submitted) return;
    
    // Check if already answered this question
    const alreadyAnswered = !!answers[currentCard.card_id];
    
    setAnswers((prev) => ({ ...prev, [currentCard.card_id]: originalIndex }));
    
    // Store potential score for this answer (will be applied only if correct on submit)
    if (!alreadyAnswered) {
      const difficultyMultiplier = 
        currentCard.difficulty === 'hard' ? 3 :
        currentCard.difficulty === 'medium' ? 2 : 1;
      
      // Check if double points power-up is active
      const doublePointsActive = powerUps.find(p => p.id === 'double_points')?.active;
      const pointsMultiplier = doublePointsActive ? 2 : 1;
      
      const questionScore = Math.round(currentPoints * difficultyMultiplier * pointsMultiplier);
      
      // Store the potential score (will be validated on submit)
      setQuestionScores((prev) => ({ ...prev, [currentCard.card_id]: questionScore }));
      
      // Deactivate double points after use
      if (doublePointsActive) {
        setPowerUps(prev => prev.map(p => 
          p.id === 'double_points' ? { ...p, active: false } : p
        ));
      }
    }
    
    // If immediate mode, show answer feedback right away
    if (answerDisplayMode === 'immediate') {
      setShowAnswerFeedback(true);
    }
  };

  const handleNext = () => {
    if (!quiz || currentIndex >= quiz.cards.length - 1) return;
    
    // Reset answer feedback for next question
    setShowAnswerFeedback(false);
    
    // Reset timer and points for next question
    setTimeLeft(timePerQuestion);
    setCurrentPoints(100);
    setCurrentIndex((i) => i + 1);
  };

  const activatePowerUp = async (powerUpId: string) => {
    // Prevent double-click
    if (activatingPowerUp) {
      return;
    }
    
    const powerUp = powerUps.find(p => p.id === powerUpId);
    if (!powerUp || powerUp.usesLeft <= 0 || userExp < powerUp.cost || !currentCard) {
      if (powerUp && userExp < powerUp.cost) {
        showToast.error('Không đủ EXP để sử dụng item này!');
      }
      return;
    }
    
    // Check if hint already shown for this card
    if (powerUpId === 'show_hint' && showHint[currentCard.card_id]) {
      showToast.info('Gợi ý đã được hiển thị cho câu hỏi này!');
      return;
    }
    
    setActivatingPowerUp(powerUpId);
    
    // For hint, mark as shown immediately to prevent double-click
    if (powerUpId === 'show_hint') {
      setShowHint(prev => ({ ...prev, [currentCard.card_id]: true }));
    }

    // Deduct EXP from backend
    try {
      await fetch('/api/users/experience/deduct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exp: powerUp.cost }),
      });
      
      // Update local state
      setUserExp(prev => prev - powerUp.cost);
      
      // Apply power-up effect
      switch (powerUpId) {
        case 'double_points':
          setPowerUps(prev => prev.map(p => 
            p.id === powerUpId ? { ...p, usesLeft: p.usesLeft - 1, active: true } : p
          ));
          showToast.success('Điểm câu này sẽ được nhân đôi!');
          break;
          
        case 'freeze_time':
          setTimerFrozen(true);
          setPowerUps(prev => prev.map(p => 
            p.id === powerUpId ? { ...p, usesLeft: p.usesLeft - 1 } : p
          ));
          showToast.success('Đã đóng băng thời gian 30 giây!');
          
          // Unfreeze after 30 seconds
          freezeTimeoutRef.current = setTimeout(() => {
            setTimerFrozen(false);
            showToast.info('Thời gian tiếp tục chạy');
          }, 30000);
          break;
          
        case 'fifty_fifty':
          // Eliminate 2 wrong options, keeping the correct answer
          if (currentCard) {
            // Find the correct answer's index
            const correctAnswerIndex = currentCard.answer;
            
            if (!correctAnswerIndex) {
              showToast.error('Không thể sử dụng 50/50 cho câu hỏi này!');
              return;
            }
            
            // Get all option indices (1, 2, 3, 4)
            const allOptionIndices = [1, 2, 3, 4];
            
            // Get wrong answer indices (not the correct answer)
            const wrongOptions = allOptionIndices.filter(idx => idx !== correctAnswerIndex);
            
            // Randomly pick 2 wrong answers to eliminate
            const toEliminate = wrongOptions
              .sort(() => Math.random() - 0.5)
              .slice(0, 2);
            
            setEliminatedOptions(prev => ({ ...prev, [currentCard.card_id]: toEliminate }));
            setPowerUps(prev => prev.map(p => 
              p.id === powerUpId ? { ...p, usesLeft: p.usesLeft - 1 } : p
            ));
            showToast.success('Đã loại bỏ 2 đáp án sai!');
          } else {
            showToast.error('Không thể sử dụng 50/50 cho câu hỏi này!');
            return; // Don't deduct EXP
          }
          break;
          
        case 'show_hint':
          // Fetch and show hint for current question
          try {
            // Fetch quiz with hints enabled to get the hint
            const hintResp = await quizApi.getById(quizId, { include_hints: true, include_explanations: false });
            const hintData = hintResp?.data as { status?: number; quiz?: QuizDetail };
            const quizWithHints = hintData?.quiz;
            
            if (quizWithHints) {
              // Update the current card with hint
              const cardWithHint = quizWithHints.cards.find(c => c.card_id === currentCard.card_id);
              if (cardWithHint?.hint) {
                // Update quiz state with the hint for this card
                setQuiz(prev => {
                  if (!prev) return prev;
                  return {
                    ...prev,
                    cards: prev.cards.map(c => 
                      c.card_id === currentCard.card_id 
                        ? { ...c, hint: cardWithHint.hint }
                        : c
                    )
                  };
                });
                
                // showHint already set at the beginning, just update power-up state
                setPowerUps(prev => prev.map(p => 
                  p.id === powerUpId ? { ...p, usesLeft: p.usesLeft - 1 } : p
                ));
                showToast.success('Đã hiển thị gợi ý!');
              } else {
                showToast.error('Câu hỏi này không có gợi ý!');
                // Clear the hint flag since there's no hint
                setShowHint(prev => ({ ...prev, [currentCard.card_id]: false }));
                // Refund EXP since no hint available
                await fetch('/api/users/experience/deduct', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ exp: -powerUp.cost }), // Negative to add back
                });
                setUserExp(prev => prev + powerUp.cost);
                return;
              }
            }
          } catch (hintError) {
            console.error('Failed to fetch hint:', hintError);
            showToast.error('Không thể tải gợi ý!');
            // Clear hint flag since fetch failed
            setShowHint(prev => ({ ...prev, [currentCard.card_id]: false }));
            // Refund EXP on error
            try {
              await fetch('/api/users/experience/deduct', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ exp: -powerUp.cost }),
              });
              setUserExp(prev => prev + powerUp.cost);
            } catch (refundError) {
              console.error('Failed to refund EXP:', refundError);
            }
            return;
          }
          break;
          
        case 'skip':
          // Calculate 50% of current points with difficulty multiplier
          const difficultyMultiplier = 
            currentCard.difficulty === 'hard' ? 3 :
            currentCard.difficulty === 'medium' ? 2 : 1;
          const skipScore = Math.round(currentPoints * 0.5 * difficultyMultiplier);
          
          // Store the score for this skipped question
          setQuestionScores(prev => ({ ...prev, [currentCard.card_id]: skipScore }));
          setTotalScore(prev => prev + skipScore);
          
          // Mark as skipped with -1 (will be excluded from submission)
          setAnswers(prev => ({ ...prev, [currentCard.card_id]: -1 }));
          
          setPowerUps(prev => prev.map(p => 
            p.id === powerUpId ? { ...p, usesLeft: p.usesLeft - 1 } : p
          ));
          showToast.success(`Đã bỏ qua! Bạn nhận được ${skipScore} điểm.`);
          
          // Move to next question after a short delay
          setTimeout(() => {
            if (quiz && currentIndex < quiz.cards.length - 1) {
              setTimeLeft(timePerQuestion);
              setCurrentPoints(100);
              setCurrentIndex((i) => i + 1);
            } else {
              // Auto submit on last question
              handleSubmit();
            }
          }, 1500);
          break;
      }
    } catch (error) {
      console.error('Failed to deduct EXP:', error);
      showToast.error('Không thể sử dụng item. Vui lòng thử lại!');
    } finally {
      setActivatingPowerUp(null);
    }
  };

  const handleSubmit = async () => {
    if (!quiz || submitting) return;
    
    // Stop timer
    if (timerRef.current) clearInterval(timerRef.current);
    
    setSubmitting(true);
    try {
      // Only submit questions that were actually answered (answer >= 1)
      // Skip questions marked with -1 are excluded
      const payload = quiz.cards
        .filter((card) => answers[card.card_id] && answers[card.card_id] >= 1)
        .map((card) => ({
          card_id: card.card_id,
          answer: answers[card.card_id],
          // Send the actual score earned for this question
          points: questionScores[card.card_id] || 0,
        }));

      const resp = await quizApi.submit(quizId, payload);
      const data = resp?.data as QuizSubmitResponse;
      setResult(data);
      setSubmitted(true);
      
      // Calculate actual total score based on correct answers
      let actualTotalScore = 0;
      data.result?.answers.forEach((answer) => {
        if (answer.is_correct) {
          const cardScore = questionScores[answer.card_id] || 0;
          actualTotalScore += cardScore;
        }
      });
      setTotalScore(actualTotalScore);
      
      // Calculate average score for saving as previous_score
      const avgScore = quiz ? Math.round(actualTotalScore / quiz.cards.length) : 0;
      
      // Update previous_score if this score is higher
      if (avgScore > (quiz.previous_score || 0)) {
        try {
          await quizApi.updatePreviousScore(quizId, avgScore);
        } catch (updateError) {
          console.error('Failed to update previous_score:', updateError);
          // Don't show error to user, just log it
        }
      }
      
      const correctCount = data.result?.correct_count || 0;
      const total = data.result?.total || 1;
      const percentage = Math.round((correctCount / total) * 100);
      
      if (percentage >= 70) {
        showToast.success(`Chúc mừng! Bạn đúng ${correctCount}/${total} câu và nhận được ${data.experience?.gained_exp || 0} EXP`);
      } else {
        showToast.info(`Bạn đúng ${correctCount}/${total} câu. Hãy thử lại để cải thiện!`);
      }
    } catch (e: unknown) {
      showToast.error(e instanceof Error ? e.message : 'Không thể nộp bài');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetry = () => {
    setAnswers({});
    setCurrentIndex(0);
    setSubmitted(false);
    setResult(null);
    setTimeLeft(timePerQuestion);
    setCurrentPoints(100);
    setTotalScore(0);
    setQuestionScores({});
    setTimerFrozen(false);
    setEliminatedOptions({});
    setShowHint({});
    setPowerUps(prev => prev.map(p => ({ ...p, usesLeft: p.maxUses, active: false })));
    isProcessingTimeout.current = false;
    
    if (freezeTimeoutRef.current) {
      clearTimeout(freezeTimeoutRef.current);
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    // Reload to fetch fresh user EXP
    window.location.reload();
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-white rounded-xl p-10 text-center border border-gray-100 shadow-sm">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-sky-500 mx-auto" />
          <p className="mt-4 text-gray-600">Đang tải quiz...</p>
        </div>
      </div>
    );
  }

  if (error || !quiz || !currentCard) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-red-50 text-red-700 rounded-xl p-4 border border-red-200 text-sm">
          {error || 'Không tìm thấy quiz'}
        </div>
        <Link href="/user/my-quizzes" className="inline-block mt-4 text-sky-600 font-semibold hover:text-sky-700">
          ← Quay lại danh sách
        </Link>
      </div>
    );
  }

  if (submitted && result) {
    const avgScore = quiz ? Math.round(totalScore / quiz.cards.length) : 0;
    
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-6">
        {/* Summary Card */}
        <Card className="shadow-lg border-gray-200">
          <CardContent className="p-8 sm:p-12 text-center space-y-6">
            <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto" />
            <div>
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">Hoàn thành Quiz!</h2>
              <p className="text-gray-600">Kết quả của bạn</p>
            </div>

            <div className="grid sm:grid-cols-3 gap-4 py-6">
              <div className="bg-amber-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Tổng điểm</p>
                <p className="text-3xl font-bold text-amber-600">{totalScore}</p>
              </div>
              <div className="bg-sky-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Điểm TB</p>
                <p className="text-3xl font-bold text-sky-600">{avgScore}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Đúng</p>
                <p className="text-3xl font-bold text-green-600">
                  {result.result?.correct_count}/{result.result?.total}
                </p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-6">
              <button
                onClick={handleRetry}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg border border-sky-500 text-sky-600 font-semibold hover:bg-sky-50"
              >
                <RotateCcw className="w-4 h-4" />
                Làm lại
              </button>
              <Link
                href={`/user/my-quizzes/${quizId}`}
                className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-lg bg-sky-500 text-white font-semibold hover:bg-sky-600 shadow-sm"
              >
                Xem chi tiết
              </Link>
              <Link
                href="/user/my-quizzes"
                className="w-full sm:w-auto px-6 py-3 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 text-center"
              >
                Danh sách quiz
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Answers Review */}
        <div className="space-y-4">
          <h3 className="text-xl font-bold text-gray-900">Chi tiết đáp án</h3>
          {quiz?.cards.map((card, idx) => {
            const answerDetail = result.result?.answers.find(a => a.card_id === card.card_id);
            const isCorrect = answerDetail?.is_correct;
            const userAnswer = answerDetail?.selected_answer;
            const correctAnswer = answerDetail?.correct_answer;
            const cardScore = questionScores[card.card_id] || 0;
            
            return (
              <Card key={card.card_id} className={`border-2 ${isCorrect ? 'border-green-200 bg-green-50/30' : 'border-red-200 bg-red-50/30'}`}>
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-sm font-bold text-gray-500">Câu {idx + 1}</span>
                        <Badge className={`${
                          card.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                          card.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {card.difficulty === 'easy' ? 'Dễ (x1)' : card.difficulty === 'medium' ? 'TB (x2)' : 'Khó (x3)'}
                        </Badge>
                        {isCorrect && (
                          <Badge className="bg-amber-100 text-amber-700">
                            +{cardScore} điểm
                          </Badge>
                        )}
                      </div>
                      <h4 className="text-lg font-semibold text-gray-900 mb-3">{card.question}</h4>
                      
                      <div className="space-y-2">
                        {[
                          { num: 1, text: card.option1 },
                          { num: 2, text: card.option2 },
                          { num: 3, text: card.option3 },
                          { num: 4, text: card.option4 },
                        ].map((option) => {
                          const isUserAnswer = option.num === userAnswer;
                          const isCorrectAnswer = option.num === correctAnswer;
                          
                          return (
                            <div
                              key={option.num}
                              className={`p-3 rounded-lg border-2 ${
                                isCorrectAnswer
                                  ? 'border-green-500 bg-green-50'
                                  : isUserAnswer && !isCorrect
                                    ? 'border-red-500 bg-red-50'
                                    : 'border-gray-200 bg-white'
                              }`}
                            >
                              <div className="flex items-center gap-3">
                                <span className={`flex items-center justify-center w-8 h-8 rounded-lg text-sm font-bold ${
                                  isCorrectAnswer
                                    ? 'bg-green-500 text-white'
                                    : isUserAnswer && !isCorrect
                                      ? 'bg-red-500 text-white'
                                      : 'bg-gray-200 text-gray-600'
                                }`}>
                                  {String.fromCharCode(64 + option.num)}
                                </span>
                                <span className="flex-1">{option.text}</span>
                                {isCorrectAnswer && (
                                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                                )}
                                {isUserAnswer && !isCorrect && (
                                  <X className="w-5 h-5 text-red-600" />
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                      
                      {answerDetail?.explanation && (
                        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                          <p className="text-sm font-semibold text-blue-900 mb-1">Giải thích:</p>
                          <p className="text-sm text-blue-800">{answerDetail.explanation}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    );
  }

  const isAnswered = !!answers[currentCard.card_id];
  const timeProgress = (timeLeft / timePerQuestion) * 100;
  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;

  // Determine timer color based on time remaining
  const getTimerColor = () => {
    if (timeProgress > 50) return 'from-green-500 to-emerald-500';
    if (timeProgress > 25) return 'from-yellow-500 to-orange-500';
    return 'from-red-500 to-rose-500';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-50 py-6 sm:py-10">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between bg-white/70 backdrop-blur-sm rounded-xl p-4 shadow-sm border border-gray-100">
          <Link 
            href={`/user/my-quizzes/${quizId}`} 
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 border-gray-300 bg-white hover:bg-gray-50 text-gray-700 font-semibold transition-all text-sm"
          >
            <span>←</span> Thoát
          </Link>
          <div className="flex items-center gap-3">
            <Badge className="bg-gradient-to-r from-sky-500 to-blue-500 text-white border-none shadow-sm px-3 py-1.5">
              Câu {currentIndex + 1} / {quiz.cards.length}
            </Badge>
            <Badge className={`flex items-center gap-1.5 px-3 py-1.5 ${
              timeLeft <= 10 ? 'bg-gradient-to-r from-red-500 to-rose-500 text-white animate-pulse shadow-md' : 'bg-gray-700 text-white'
            } border-none shadow-sm`}>
              <Clock className="w-3.5 h-3.5" />
              {minutes}:{seconds.toString().padStart(2, '0')}
            </Badge>
          </div>
        </div>

        {/* Timer Progress Bar */}
        <div className="space-y-3 bg-white/70 backdrop-blur-sm rounded-xl p-5 shadow-sm border border-gray-100">
          <div className="h-4 bg-gray-200 rounded-full overflow-hidden shadow-inner relative">
            <div
              className={`h-full bg-gradient-to-r ${getTimerColor()} transition-all duration-1000 ease-linear shadow-sm`}
              style={{ width: `${timeProgress}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-sm font-medium">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-sky-600" />
                <span className="text-gray-600">Điểm câu này:</span>
                <span className="text-sky-700 font-bold text-lg">{currentPoints}</span>
              </div>
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-amber-600" />
                <span className="text-gray-600">Tổng điểm:</span>
                <span className="text-amber-700 font-bold text-lg">{totalScore}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Power-ups */}
        <div className="bg-white/70 backdrop-blur-sm rounded-xl p-3 sm:p-4 shadow-sm border border-gray-100">
          <div className="flex items-center gap-1.5 sm:gap-2 mb-2 sm:mb-3">
            <Zap className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-purple-600" />
            <h3 className="font-bold text-gray-900 text-xs sm:text-sm">Items (EXP: {userExp})</h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-1.5 sm:gap-2">
            {powerUps.map((powerUp) => {
              const isActive = powerUp.active;
              const canUse = powerUp.usesLeft > 0 && userExp >= powerUp.cost;
              
              // Render icon based on type
              const PowerUpIcon = 
                powerUp.iconType === 'zap' ? Zap :
                powerUp.iconType === 'snowflake' ? Snowflake :
                powerUp.iconType === 'eye' ? Eye :
                powerUp.iconType === 'lightbulb' ? Lightbulb :
                powerUp.iconType === 'skip' ? SkipForward : Zap;
              
              return (
                <button
                  key={powerUp.id}
                  onClick={() => activatePowerUp(powerUp.id)}
                  disabled={!canUse || isActive}
                  className={`group relative flex flex-col lg:flex-row items-center justify-center lg:justify-start gap-1 sm:gap-1.5 lg:gap-2 px-2 sm:px-3 lg:px-4 py-2 sm:py-2.5 rounded-lg border-2 font-semibold text-[10px] sm:text-xs lg:text-sm transition-all ${
                    isActive
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : canUse
                        ? 'border-purple-300 bg-white hover:border-purple-500 hover:bg-purple-50 text-gray-700'
                        : 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                  }`}
                  title={powerUp.description}
                >
                  <PowerUpIcon className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                  <span className="text-center lg:text-left leading-tight">{powerUp.name}</span>
                  <span className="text-[9px] sm:text-xs opacity-75">({powerUp.usesLeft}/{powerUp.maxUses})</span>
                  {canUse && !isActive && (
                    <span className="absolute -top-1.5 sm:-top-2 -right-1.5 sm:-right-2 bg-purple-600 text-white text-[9px] sm:text-xs px-1 sm:px-1.5 py-0.5 rounded-full">
                      -{powerUp.cost}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Flashcard */}
        <Card className="shadow-2xl border-gray-200 bg-gradient-to-br from-white to-gray-50">
          <CardContent className="p-6 sm:p-10 space-y-8">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-1 h-6 bg-gradient-to-b from-sky-500 to-blue-500 rounded-full"></div>
                  <span className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Câu hỏi</span>
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 leading-tight">
                  {currentCard.question}
                </h2>
              </div>
              <Badge className={`shrink-0 px-3 py-1.5 font-semibold shadow-sm ${
                currentCard.difficulty === 'easy' ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white' :
                currentCard.difficulty === 'medium' ? 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white' :
                'bg-gradient-to-r from-red-500 to-rose-500 text-white'
              } border-none`}>
                {currentCard.difficulty === 'easy' ? 'Dễ' : currentCard.difficulty === 'medium' ? 'TB' : 'Khó'}
              </Badge>
            </div>
            
            {/* Hint Display - Full Width */}
            {showHint[currentCard.card_id] && currentCard.hint && (
              <div className="p-4 bg-amber-50 border-2 border-amber-300 rounded-lg flex items-start gap-3">
                <Lightbulb className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-semibold text-amber-900 mb-1">Gợi ý:</p>
                  <p className="text-sm text-amber-800">{currentCard.hint}</p>
                </div>
              </div>
            )}

            {/* Options */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                { index: 1, text: currentCard.option1, label: 'A' },
                { index: 2, text: currentCard.option2, label: 'B' },
                { index: 3, text: currentCard.option3, label: 'C' },
                { index: 4, text: currentCard.option4, label: 'D' },
              ].map((option) => {
                const isSelected = answers[currentCard.card_id] === option.index;
                const isCorrect = currentCard.answer === option.index;
                const isEliminated = eliminatedOptions[currentCard.card_id]?.includes(option.index);
                const showFeedback = showAnswerFeedback && answerDisplayMode === 'immediate' && !!currentCard.answer;
                
                if (isEliminated) {
                  return (
                    <div
                      key={option.label}
                      className="w-full px-5 py-4 rounded-xl border-2 border-gray-200 bg-gray-100 text-gray-400 opacity-50"
                    >
                      <span className="flex items-center gap-4">
                        <span className="flex items-center justify-center w-10 h-10 rounded-xl text-sm font-bold bg-gray-200 text-gray-400">
                          <X className="w-5 h-5" />
                        </span>
                        <span className="flex-1 text-[15px] leading-relaxed line-through">{option.text}</span>
                      </span>
                    </div>
                  );
                }
                
                // Determine styling based on feedback state
                let buttonClass = 'border-gray-200 bg-white hover:border-sky-400 hover:bg-sky-50/30 text-gray-700';
                let labelClass = 'bg-gray-100 text-gray-600 group-hover:bg-sky-100 group-hover:text-sky-700';
                
                if (showFeedback) {
                  if (isCorrect) {
                    // Correct answer - always green
                    buttonClass = 'border-green-500 bg-gradient-to-r from-green-50 to-emerald-50 text-green-900';
                    labelClass = 'bg-gradient-to-br from-green-500 to-emerald-600 text-white';
                  } else if (isSelected) {
                    // Wrong selected answer - red
                    buttonClass = 'border-red-500 bg-gradient-to-r from-red-50 to-rose-50 text-red-900';
                    labelClass = 'bg-gradient-to-br from-red-500 to-rose-600 text-white';
                  }
                } else if (isSelected) {
                  // Selected but no feedback yet
                  buttonClass = 'border-sky-500 bg-gradient-to-r from-sky-50 to-blue-50 text-sky-900 shadow-md scale-[1.02]';
                  labelClass = 'bg-gradient-to-br from-sky-500 to-blue-600 text-white shadow-md';
                }
                
                return (
                  <button
                    key={option.label}
                    onClick={() => handleAnswer(option.index)}
                    disabled={submitted || showFeedback}
                    className={`group w-full px-5 py-4 rounded-xl border-2 text-left font-medium transition-all duration-200 ${
                      buttonClass
                    } ${(submitted || showFeedback) ? 'cursor-not-allowed' : 'cursor-pointer hover:shadow-lg hover:scale-[1.01]'}`}
                  >
                    <span className="flex items-center gap-4">
                      <span className={`flex items-center justify-center w-10 h-10 rounded-xl text-sm font-bold transition-all ${
                        labelClass
                      }`}>
                        {option.label}
                      </span>
                      <span className="flex-1 text-[15px] leading-relaxed">{option.text}</span>
                    </span>
                  </button>
                );
              })}
            </div>
            
            {/* Explanation - Show immediately if mode is 'immediate' and answer is given */}
            {showAnswerFeedback && answerDisplayMode === 'immediate' && currentCard.explanation && answers[currentCard.card_id] !== undefined && (
              <div className="p-4 bg-blue-50 border-l-4 border-blue-400 rounded mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <p className="text-sm font-semibold text-blue-900 mb-1">Giải thích:</p>
                <p className="text-sm text-blue-800">
                  {currentCard.explanation
                    .replace(/option1/gi, 'A')
                    .replace(/option2/gi, 'B')
                    .replace(/option3/gi, 'C')
                    .replace(/option4/gi, 'D')}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex items-center justify-center gap-3 pt-2">
          {currentIndex < quiz.cards.length - 1 ? (
            <button
              onClick={handleNext}
              disabled={!isAnswered}
              className="px-10 py-3.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 text-white font-bold hover:from-sky-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transition-all hover:scale-105 disabled:hover:scale-100"
            >
              Tiếp theo →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!isAnswered || submitting}
              className="px-10 py-3.5 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl inline-flex items-center gap-2 transition-all hover:scale-105 disabled:hover:scale-100"
            >
              {submitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  Đang nộp...
                </>
              ) : (
                <>Nộp bài</>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
