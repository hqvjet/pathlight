'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useProfileData } from './profile/hooks';
import { ProfileAvatar } from './profile/ProfileAvatar';
import { ProfileFormData } from './profile/types';
import SubscriptionModal from './subscription/SubscriptionModal';

export default function ProfilePage() {
  const { loading, saving, user, uploading, avatarLoading, avatarKey, formData, setFormData, loadUserProfile, updateProfile, uploadAvatar, remindTime, setRemindTime, updateRemindTime, remindSaving } = useProfileData();
  const [showNativeDate, setShowNativeDate] = useState(false);
  const [nativeDateValue, setNativeDateValue] = useState('');
  const [showSubscriptionModal, setShowSubscriptionModal] = useState(false);

  useEffect(() => { loadUserProfile(); }, [loadUserProfile]);

  useEffect(() => {
    // Convert dd/mm/yyyy -> yyyy-mm-dd for native input
    if (formData.birth_date && formData.birth_date.includes('/')) {
      const [d,m,y] = formData.birth_date.split('/');
      if (d && m && y) setNativeDateValue(`${y}-${m.padStart(2,'0')}-${d.padStart(2,'0')}`);
    }
  }, [formData.birth_date]);

  const handleSubmit = async (e: React.FormEvent) => { e.preventDefault(); await updateProfile(formData as ProfileFormData); };

  const currentExp = user?.current_exp ?? (user as { experience?: number } | undefined)?.experience ?? 0;
  const requireExp = user?.require_exp ?? (user as { exp_needed_for_next?: number; required_exp?: number } | undefined)?.exp_needed_for_next ?? (user as { required_exp?: number } | undefined)?.required_exp ?? 0;
  const expPercent = (() => {
    if (!requireExp || requireExp <= 0) return 0;
    return Math.min(100, Math.round((currentExp / requireExp) * 100));
  })();
  const remainingExp = Math.max(requireExp - currentExp, 0);
  const nextLevelLabel = (user?.level || 1) + 1;
  const courseCount = user?.course_num ?? user?.total_courses ?? 0;
  const lessonCount = user?.lesson_num ?? 0;
  const completedCourses = user?.completed_courses ?? 0;
  const HOURS = useMemo(() => Array.from({ length: 24 }).map((_, i) => String(i).padStart(2, '0')), []);
  const MINUTES = useMemo(() => Array.from({ length: 60 }).map((_, i) => String(i).padStart(2, '0')), []);
  const presetTimes = useMemo(() => ['06:30', '07:00', '08:00', '12:00', '19:00', '21:30'], []);
  const [hourIdx, setHourIdx] = useState(0);
  const [minuteIdx, setMinuteIdx] = useState(0);
  const hourIdxRef = useRef(0);
  const minuteIdxRef = useRef(0);
  const hourDrag = useRef({ active: false, startY: 0, startIdx: 0 });
  const minuteDrag = useRef({ active: false, startY: 0, startIdx: 0, startHourIdx: 0 });
  const rowHeight = 50;

  const parseTime = (value: string) => {
    const [h, m] = value.split(':');
    const hour = Math.min(23, Math.max(0, Number(h) || 0));
    const minute = Math.min(59, Math.max(0, Number(m) || 0));
    return { hour, minute };
  };

  useEffect(() => {
    const { hour, minute } = parseTime(remindTime || '00:00');
    setHourIdx(hour);
    setMinuteIdx(minute);
    hourIdxRef.current = hour;
    minuteIdxRef.current = minute;
  }, [remindTime]);

  const normalizedIndex = (idx: number, length: number) => ((idx % length) + length) % length;
  const renderWindow = (list: string[], centerIdx: number, size = 3) => {
    const half = Math.floor(size / 2);
    return Array.from({ length: size }).map((_, offset) => {
      const rel = offset - half;
      const idx = normalizedIndex(centerIdx + rel, list.length);
      return { val: list[idx], key: `${idx}-${rel}`, rel };
    });
  };

  const normalizeHM = (h: number, m: number) => {
    let total = h * 60 + m;
    total = ((total % (24 * 60)) + (24 * 60)) % (24 * 60);
    const hh = Math.floor(total / 60);
    const mm = total % 60;
    return { h: hh, m: mm };
  };

  const setTimeSafe = useCallback((hIdx: number, mIdx: number) => {
    const { h, m } = normalizeHM(hIdx, mIdx);
    setHourIdx(h);
    setMinuteIdx(m);
    hourIdxRef.current = h;
    minuteIdxRef.current = m;
    setRemindTime(`${HOURS[h]}:${MINUTES[m]}`);
  }, [HOURS, MINUTES, setRemindTime]);

  const handleStepHour = useCallback((delta: number) => {
    const step = delta > 0 ? 1 : -1;
    setTimeSafe(hourIdxRef.current + step, minuteIdxRef.current);
  }, [setTimeSafe]);

  const handleStepMinute = useCallback((delta: number) => {
    const step = delta > 0 ? 1 : -1;
    setTimeSafe(hourIdxRef.current, minuteIdxRef.current + step);
  }, [setTimeSafe]);

  useEffect(() => {
    const options: AddEventListenerOptions = { passive: false, capture: true };
    const handleWheel = (e: WheelEvent) => {
      const target = e.target as HTMLElement | null;
      if (!target) return;
      const wheelEl = target.closest('[data-kind]');
      if (!wheelEl) return;
      const kind = (wheelEl.getAttribute('data-kind') || '').toLowerCase();
      if (kind !== 'hour' && kind !== 'minute') return;
      e.preventDefault();
      e.stopPropagation();
      if (kind === 'hour') {
        handleStepHour(e.deltaY);
      } else {
        handleStepMinute(e.deltaY);
      }
    };

    window.addEventListener('wheel', handleWheel, options);
    return () => window.removeEventListener('wheel', handleWheel, options);
  }, [handleStepHour, handleStepMinute]);

  const startDrag = (
    dragRef: React.MutableRefObject<{ active: boolean; startY: number; startIdx: number; startHourIdx?: number }>,
    currentIdx: number,
    clientY: number,
    startHourIdx?: number,
  ) => {
    dragRef.current = { active: true, startY: clientY, startIdx: currentIdx, startHourIdx };
  };

  const moveDrag = (
    dragRef: React.MutableRefObject<{ active: boolean; startY: number; startIdx: number; startHourIdx?: number }>,
    list: string[],
    clientY: number,
    kind: 'hour' | 'minute',
  ) => {
    if (!dragRef.current.active) return;
    const delta = clientY - dragRef.current.startY;
    const steps = Math.round(delta / rowHeight);
    if (kind === 'hour') {
      const nextIdx = normalizedIndex(dragRef.current.startIdx + steps, list.length);
      setTimeSafe(nextIdx, minuteIdxRef.current);
    } else {
      const startHour = dragRef.current.startHourIdx ?? hourIdxRef.current;
      const totalStart = startHour * 60 + dragRef.current.startIdx;
      const total = totalStart + steps;
      const { h, m } = normalizeHM(0, total);
      setTimeSafe(h, m);
    }
  };

  const endDrag = (dragRef: React.MutableRefObject<{ active: boolean; startY: number; startIdx: number; startHourIdx?: number }>) => {
    dragRef.current.active = false;
  };

  const setHour = (v: string) => {
    const { minute } = parseTime(remindTime || '00:00');
    setRemindTime(`${v}:${String(minute).padStart(2, '0')}`);
  };
  const setMinute = (v: string) => {
    const { hour } = parseTime(remindTime || '00:00');
    setRemindTime(`${String(hour).padStart(2, '0')}:${v}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4" />
          <p className="text-gray-600">Đang tải...</p>
        </div>
      </div>
    );
  }

  const openDatePicker = () => {
    setShowNativeDate(true);
    setTimeout(() => {
      const el = document.getElementById('hidden-native-date');
      (el as HTMLInputElement | null)?.showPicker?.();
    }, 0);
  };

  const handleNativeDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const iso = e.target.value; // yyyy-mm-dd
    if (!iso) return;
    const [y,m,d] = iso.split('-');
    const display = `${d.padStart(2,'0')}/${m.padStart(2,'0')}/${y}`;
    setFormData({ ...formData, birth_date: display });
  };

  return (
    <>
      <div className="min-h-screen bg-[#f5f7fb]">
        <div className="max-w-[1330px] mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-4 sm:py-6 md:py-8 lg:py-12">
          <div className="bg-white/90 backdrop-blur rounded-xl sm:rounded-2xl border border-gray-100 shadow-[0_8px_30px_rgba(15,23,42,0.05)] p-3 sm:p-4 md:p-6 lg:p-8">
            <div className="flex flex-col gap-2 sm:gap-3 mb-4 sm:mb-6">
              <div>
                <h1 className="text-lg sm:text-xl md:text-2xl font-semibold text-gray-900 leading-tight">Thông Tin Hồ Sơ</h1>
              </div>
            </div>

          {user && (
            <div className="mb-4 sm:mb-6 md:mb-8 grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-3 sm:gap-4">
              {/* Avatar section - shows first on mobile */}
              <div className="w-full lg:hidden flex justify-center">
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-3 sm:p-4 md:p-6 flex flex-col items-center gap-3 sm:gap-4 w-full max-w-[280px]">
                  <div className="w-full aspect-[1/1.02] min-h-[180px] sm:min-h-[200px] md:min-h-[240px] rounded-lg bg-gray-50/60 border border-dashed border-gray-200 relative">
                    <ProfileAvatar user={user} uploading={uploading} avatarLoading={avatarLoading} avatarKey={avatarKey} onUpload={uploadAvatar} />
                    {!user && (
                      <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-400">Đang tải ảnh...</div>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-600">
                    <span className="px-2 py-1 rounded-full bg-orange-50 text-orange-600 font-semibold">Lv {user?.level || 1}</span>
                    <span className="px-2 py-1 rounded-full bg-slate-100 text-slate-700 font-semibold"># {user?.rank ?? '—'}</span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-center text-gray-600">Ảnh tải lên không được quá 3MB<br/>Nên chọn ảnh có tỉ lệ 1:1</p>
                </div>
              </div>

              {/* Stats card */}
              <div className="p-3 sm:p-4 md:p-5 lg:p-6 rounded-xl sm:rounded-2xl bg-white border border-gray-100 shadow-sm text-gray-900 lg:col-span-1">
                <div className="flex items-center justify-between mb-3 sm:mb-4 gap-2">
                  <div>
                    <p className="text-sm sm:text-base md:text-lg font-semibold text-gray-900">Hành trình của bạn</p>
                  </div>
                  <div className="flex items-center gap-1 sm:gap-1.5 md:gap-2 text-xs sm:text-sm font-semibold text-gray-700">
                    <div className="px-1.5 sm:px-2 md:px-3 py-0.5 sm:py-1 rounded-full bg-gray-100 border border-gray-200 text-[10px] sm:text-xs">Rank #{user.rank ?? '—'}</div>
                    <div className="px-1.5 sm:px-2 md:px-3 py-0.5 sm:py-1 rounded-full bg-gray-100 border border-gray-200 text-[10px] sm:text-xs">Lv {user.level || 1}</div>
                  </div>
                </div>
                <div className="h-2.5 sm:h-3 w-full bg-gray-100 rounded-full overflow-hidden border border-gray-200">
                  <div className="h-full bg-orange-500" style={{ width: `${expPercent}%` }} />
                </div>
                <div className="mt-1.5 sm:mt-2 flex justify-between text-[10px] sm:text-xs text-gray-600">
                  <span>{currentExp} / {requireExp || 0} EXP</span>
                  <span className="hidden sm:inline">Còn {remainingExp} EXP lên Lv {nextLevelLabel}</span>
                  <span className="sm:hidden">{remainingExp} EXP</span>
                </div>
                <div className="mt-3 sm:mt-4 grid grid-cols-3 gap-1.5 sm:gap-2 md:gap-3 text-xs sm:text-sm text-gray-800">
                  <div className="rounded-lg border border-gray-200 bg-gray-50 px-2 sm:px-3 py-1.5 sm:py-2">
                    <div className="text-[10px] sm:text-[11px] text-gray-500">Khóa học</div>
                    <div className="font-semibold text-gray-900 text-xs sm:text-sm">{courseCount}</div>
                  </div>
                  <div className="rounded-lg border border-gray-200 bg-gray-50 px-2 sm:px-3 py-1.5 sm:py-2">
                    <div className="text-[10px] sm:text-[11px] text-gray-500">Bài học</div>
                    <div className="font-semibold text-gray-900 text-xs sm:text-sm">{lessonCount}</div>
                  </div>
                  <div className="rounded-lg border border-gray-200 bg-gray-50 px-2 sm:px-3 py-1.5 sm:py-2">
                    <div className="text-[10px] sm:text-[11px] text-gray-500 leading-tight">Khóa đã hoàn thành</div>
                    <div className="font-semibold text-gray-900 text-xs sm:text-sm">{completedCourses}</div>
                  </div>
                </div>

                {/* Subscription Section */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <svg className="h-4 w-4 text-purple-500" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                      </svg>
                      <span className="text-sm font-semibold text-gray-900">Gói đăng ký</span>
                    </div>
                  </div>
                  
                  {(() => {
                    const subscription = user?.subscription ?? 0;
                    const tierInfo = subscription === 2 
                      ? { name: 'Pro', color: 'from-purple-500 to-pink-500', bgColor: 'bg-gradient-to-br from-purple-50 via-fuchsia-50 to-pink-50', borderColor: 'border-purple-200', textColor: 'text-purple-700', features: ['60 câu hỏi/quiz', '3 lần dùng power-up', 'Tất cả tính năng'] }
                      : subscription === 1 
                      ? { name: 'Premium', color: 'from-sky-500 to-blue-500', bgColor: 'bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-50', borderColor: 'border-sky-200', textColor: 'text-sky-700', features: ['45 câu hỏi/quiz', '2 lần dùng power-up', 'Nhiều tính năng'] }
                      : { name: 'Free', color: 'from-gray-400 to-gray-500', bgColor: 'bg-gradient-to-br from-gray-50 to-slate-50', borderColor: 'border-gray-200', textColor: 'text-gray-700', features: ['30 câu hỏi/quiz', '1 lần dùng power-up', 'Tính năng cơ bản'] };
                    
                    return (
                      <>
                        <div className={`rounded-xl border-2 ${tierInfo.borderColor} ${tierInfo.bgColor} p-5 relative overflow-hidden`}>
                          <div className="absolute top-0 right-0 w-32 h-32 opacity-30 -mr-16 -mt-16">
                            <div className={`w-full h-full rounded-full bg-gradient-to-br ${tierInfo.color}`}></div>
                          </div>
                          
                          <div className="relative">
                            <div className="flex items-center justify-between mb-4">
                              <div className="flex items-center gap-3">
                                <div className={`px-4 py-2 rounded-lg bg-gradient-to-r ${tierInfo.color} text-white font-bold text-lg shadow-lg`}>
                                  {tierInfo.name}
                                </div>
                                {subscription > 0 && (
                                  <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                  </svg>
                                )}
                              </div>
                            </div>
                            
                            <div className="space-y-2 mb-4">
                              {tierInfo.features.map((feature, index) => (
                                <div key={index} className="flex items-center gap-2">
                                  <svg className={`w-4 h-4 ${tierInfo.textColor} flex-shrink-0`} fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                  </svg>
                                  <span className={`text-sm ${tierInfo.textColor} font-medium`}>{feature}</span>
                                </div>
                              ))}
                            </div>
                            
                            {subscription < 2 && (
                              <button 
                                onClick={() => setShowSubscriptionModal(true)}
                                className="w-full py-2.5 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold text-sm shadow-lg transition-all flex items-center justify-center gap-2"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                                </svg>
                                {subscription === 0 ? 'Nâng cấp lên Premium' : 'Nâng cấp lên Pro'}
                              </button>
                            )}
                          </div>
                        </div>

                        {subscription < 2 && (
                          <div className="mt-3 p-3 rounded-lg bg-amber-50 border border-amber-200">
                            <div className="flex items-start gap-2">
                              <svg className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                              </svg>
                              <div className="text-[11px] leading-relaxed text-amber-800">
                                <span className="font-semibold">Mở khóa nhiều tính năng hơn!</span><br />
                                {subscription === 0 ? 'Nâng cấp lên Premium để tạo quiz với nhiều câu hỏi hơn và sử dụng power-up hiệu quả hơn.' : 'Nâng cấp lên Pro để trải nghiệm tối đa với 60 câu hỏi và 3 lần dùng mỗi power-up!'}
                              </div>
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>

                {/* Streak Section */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center gap-2 mb-3">
                    <svg className="h-4 w-4 text-orange-500" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C12 2 8 6 8 10c0 2.21 1.79 4 4 4s4-1.79 4-4c0-4-4-8-4-8zm0 18c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.5 9.5C4.56 11.13 4 13 4 15c0 4.42 3.58 8 8 8s8-3.58 8-8c0-2-.56-3.87-1.5-5.5l-1.2 1.7c.45.83.7 1.79.7 2.8 0 3.31-2.69 6-6 6z"/>
                    </svg>
                    <span className="text-sm font-semibold text-gray-900">Chuỗi học liên tục</span>
                  </div>
                  
                  {(() => {
                    const currentStreak = user?.streak ?? 0;
                    // Calculate fire size based on streak (min 32px, max 96px)
                    const minSize = 32;
                    const maxSize = 96;
                    const fireSize = Math.min(maxSize, minSize + Math.floor(currentStreak * 2));
                    
                    return (
                      <>
                        <div className="rounded-xl border-2 border-orange-200 bg-gradient-to-br from-orange-50 via-amber-50 to-red-50 p-6 relative overflow-hidden">
                          <div className="absolute top-0 right-0 w-24 h-24 bg-orange-100/40 rounded-full -mr-12 -mt-12"></div>
                          <div className="absolute bottom-0 left-0 w-20 h-20 bg-red-100/30 rounded-full -ml-10 -mb-10"></div>
                          
                          <div className="relative flex items-center justify-between">
                            <div className="flex-1">
                              <div className="text-xs uppercase tracking-wide text-orange-600 font-semibold mb-2">Streak hiện tại</div>
                              <div className="flex items-baseline gap-2 mb-3">
                                <span className="text-4xl font-bold text-orange-600">{currentStreak}</span>
                                <span className="text-lg text-orange-500 font-semibold">ngày</span>
                              </div>
                              <div className="flex items-center gap-1 flex-wrap">
                                {currentStreak > 0 && [...Array(Math.min(currentStreak, 15))].map((_, i) => (
                                  <div 
                                    key={i} 
                                    className="w-2 h-2 rounded-full bg-orange-400 animate-pulse"
                                    style={{ animationDelay: `${i * 0.1}s` }}
                                  ></div>
                                ))}
                                {currentStreak > 15 && (
                                  <span className="text-xs text-orange-500 font-bold ml-1">+{currentStreak - 15}</span>
                                )}
                              </div>
                            </div>
                            
                            <div className="flex items-center justify-center ml-4">
                              <svg 
                                viewBox="0 0 24 24" 
                                fill="currentColor"
                                className="text-orange-500 transition-all duration-300 drop-shadow-lg"
                                style={{ 
                                  width: `${fireSize}px`, 
                                  height: `${fireSize}px`,
                                  filter: currentStreak > 20 ? 'drop-shadow(0 0 12px rgba(249, 115, 22, 0.6))' : 'drop-shadow(0 0 6px rgba(249, 115, 22, 0.4))'
                                }}
                              >
                                <path d="M12 2C12 2 8 6 8 10c0 2.21 1.79 4 4 4s4-1.79 4-4c0-4-4-8-4-8zm0 18c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.5 9.5C4.56 11.13 4 13 4 15c0 4.42 3.58 8 8 8s8-3.58 8-8c0-2-.56-3.87-1.5-5.5l-1.2 1.7c.45.83.7 1.79.7 2.8 0 3.31-2.69 6-6 6z"/>
                                {currentStreak > 10 && (
                                  <circle cx="12" cy="12" r="2" className="text-yellow-400 animate-ping" opacity="0.6"/>
                                )}
                              </svg>
                            </div>
                          </div>
                        </div>

                        <div className="mt-3 p-3 rounded-lg bg-blue-50 border border-blue-100">
                          <div className="flex items-start gap-2">
                            <svg className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <circle cx="12" cy="12" r="10"/>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2"/>
                            </svg>
                            <div className="text-[11px] leading-relaxed text-blue-700">
                              {currentStreak > 0 ? (
                                <>
                                  <span className="font-semibold">Học hôm nay để giữ streak!</span> Bạn đang có chuỗi {currentStreak} ngày học liên tục. {currentStreak >= 30 ? '🏆 Tuyệt vời!' : currentStreak >= 14 ? '💪 Tiếp tục phát huy!' : 'Tiếp tục nhé! 🔥'}
                                </>
                              ) : (
                                <>
                                  <span className="font-semibold">Bắt đầu streak của bạn!</span> Học mỗi ngày để xây dựng thói quen học tập tốt. 💪
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </>
                    );
                  })()}
                </div>

                {/* Notification time picker - compact version */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center gap-2 mb-3">
                    <svg className="h-4 w-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3a6 6 0 00-6 6v3.5L4 15.5a1 1 0 00.7 1.7h14.6a1 1 0 00.7-1.7L18 12.5V9a6 6 0 00-6-6Z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 19a2 2 0 004 0" />
                    </svg>
                    <span className="text-sm font-semibold text-gray-900">Nhắc giờ học</span>
                  </div>
                  
                  <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                    {/* Time picker column */}
                    <div className="flex-shrink-0">
                      <div className="flex gap-2 items-center mb-2">
                    <div className="flex gap-2">
                      {[
                        { label: 'Giờ', baseList: HOURS, idx: hourIdx, setIdx: setHourIdx, setter: setHour, drag: hourDrag, kind: 'hour' as const },
                        { label: 'Phút', baseList: MINUTES, idx: minuteIdx, setIdx: setMinuteIdx, setter: setMinute, drag: minuteDrag, kind: 'minute' as const },
                      ].map(({ label, baseList, idx, drag, kind }) => (
                        <div
                          key={label}
                          className="relative w-14 time-wheel"
                          data-kind={kind}
                          style={{ height: '100px', overscrollBehavior: 'contain' }}
                          onMouseDown={(e) => {
                            e.preventDefault();
                            if (kind === 'hour') {
                              startDrag(drag, idx, e.clientY);
                            } else {
                              startDrag(drag, idx, e.clientY, hourIdxRef.current);
                            }
                          }}
                          onMouseMove={(e) => {
                            if (!drag.current.active) return;
                            e.preventDefault();
                            moveDrag(drag, baseList, e.clientY, kind);
                          }}
                          onMouseUp={() => endDrag(drag)}
                          onMouseLeave={() => endDrag(drag)}
                        >
                          <div className="h-full overflow-hidden border border-gray-200 rounded-lg bg-white shadow-sm">
                            <div className="absolute inset-0 pointer-events-none" style={{ boxShadow: 'inset 0 24px 24px -24px rgba(0,0,0,0.06), inset 0 -24px 24px -24px rgba(0,0,0,0.06)' }} />
                            <div className="absolute left-0 right-0 border-y border-orange-200/70 pointer-events-none" style={{ top: '50%', height: '33px', marginTop: '-16.5px' }} />
                            <div className="h-full select-none">
                              <div className="relative" style={{ height: '100px' }}>
                                {renderWindow(baseList, idx, 3).map(({ val, key, rel }) => {
                                  const isCenter = rel === 0;
                                  return (
                                    <div
                                      key={key}
                                      className={`absolute left-0 right-0 flex items-center justify-center text-xs font-semibold cursor-pointer select-none ${isCenter ? 'text-gray-900' : 'text-gray-500 opacity-60'}`}
                                      style={{ height: '33px', top: '50%', transform: `translateY(${rel * 33 - 16.5}px)` }}
                                      onClick={() => {
                                        const step = rel;
                                        if (kind === 'hour') {
                                          setTimeSafe(hourIdxRef.current + step, minuteIdxRef.current);
                                        } else {
                                          const total = hourIdxRef.current * 60 + minuteIdxRef.current + step;
                                          const { h, m } = normalizeHM(0, total);
                                          setTimeSafe(h, m);
                                        }
                                      }}
                                    >
                                      {val}
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    <input
                      type="time"
                      value={remindTime}
                      onChange={(e)=> setRemindTime(e.target.value)}
                      className="rounded-lg border border-gray-200 px-2 py-1.5 text-xs shadow-sm bg-white focus:border-orange-200 focus:ring-1 focus:ring-orange-100 w-20"
                    />
                        <button type="button" onClick={()=> updateRemindTime(remindTime)} disabled={remindSaving} className="px-3 py-1.5 bg-orange-500 text-white text-xs rounded-lg shadow-sm hover:bg-orange-600 disabled:opacity-60 font-medium">{remindSaving ? 'Lưu...' : 'Lưu'}</button>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                    {presetTimes.map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setRemindTime(t)}
                        className={`px-2 py-1 rounded text-[11px] border transition ${remindTime === t ? 'bg-orange-50 border-orange-200 text-orange-700' : 'bg-white border-gray-200 text-gray-600 hover:border-orange-200'}`}
                      >
                        {t}
                        </button>
                      ))}
                      </div>
                    </div>
                    
                    {/* Tips/Motivation column */}
                    <div className="flex-1 hidden sm:block">
                      <div className="h-full bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg p-3 border border-orange-100">
                        <div className="flex items-start gap-2">
                          <svg className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                          <div>
                            <p className="text-xs font-semibold text-orange-800 mb-1">Mẹo học tập</p>
                            <p className="text-[11px] leading-relaxed text-orange-700">Học đều đặn mỗi ngày sẽ giúp bạn ghi nhớ tốt hơn. Hãy chọn khung giờ phù hợp nhất!</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Avatar section - desktop only (right column) */}
              <div className="hidden lg:flex justify-center">
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 sm:p-6 flex flex-col items-center gap-3 sm:gap-4 w-full">
                  <div className="w-full aspect-[1/1.02] min-h-[200px] sm:min-h-[240px] rounded-lg bg-gray-50/60 border border-dashed border-gray-200 relative">
                    <ProfileAvatar user={user} uploading={uploading} avatarLoading={avatarLoading} avatarKey={avatarKey} onUpload={uploadAvatar} />
                    {!user && (
                      <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-400">Đang tải ảnh...</div>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-600">
                    <span className="px-2 py-1 rounded-full bg-orange-50 text-orange-600 font-semibold">Lv {user?.level || 1}</span>
                    <span className="px-2 py-1 rounded-full bg-slate-100 text-slate-700 font-semibold"># {user?.rank ?? '—'}</span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-center text-gray-600">Ảnh tải lên không được quá 3MB<br/>Nên chọn ảnh có tỉ lệ 1:1</p>
                </div>
              </div>
            </div>
          )}

          {/* Form section */}
          <div className="mb-6 sm:mb-8">
            <form onSubmit={handleSubmit} className="space-y-5 sm:space-y-6 bg-white rounded-xl border border-gray-100 shadow-sm p-4 sm:p-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-800 mb-2">Họ Và Tên (*)</label>
                    <input name="family_name" value={formData.family_name} onChange={(e)=> setFormData({ ...formData, family_name: e.target.value })} placeholder="Nhập họ và tên đệm của bạn" className="w-full h-11 px-4 border border-gray-200 focus:border-orange-200 focus:ring-2 focus:ring-orange-100 bg-gray-50 hover:bg-white rounded-lg text-sm transition" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-800 mb-2">&nbsp;</label>
                    <input name="given_name" value={formData.given_name} onChange={(e)=> setFormData({ ...formData, given_name: e.target.value })} placeholder="Nhập tên của bạn" className="w-full h-11 px-4 border border-gray-200 focus:border-orange-200 focus:ring-2 focus:ring-orange-100 bg-gray-50 hover:bg-white rounded-lg text-sm transition" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-800 mb-2">Email (*)</label>
                  <input value={user?.email || ''} disabled className="w-full h-11 px-4 border border-gray-200 bg-gray-100 text-sm text-gray-600 rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-800 mb-2">Ngày Sinh</label>
                  <div className="relative">
                    <input name="birth_date" value={formData.birth_date} onChange={(e)=> setFormData({ ...formData, birth_date: e.target.value })} placeholder="DD / MM / YYYY" className="w-full h-11 px-4 pr-10 border border-gray-200 focus:border-orange-200 focus:ring-2 focus:ring-orange-100 bg-gray-50 hover:bg-white rounded-lg text-sm transition" />
                    <button type="button" onClick={openDatePicker} className="absolute inset-y-0 right-0 w-11 flex items-center justify-center text-gray-500 hover:text-gray-700">
                      <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M8 2v4M16 2v4M3 10h18M5 6h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2z" /></svg>
                    </button>
                    {showNativeDate && (
                      <input id="hidden-native-date" type="date" value={nativeDateValue} onChange={handleNativeDateChange} onBlur={()=> setShowNativeDate(false)} className="absolute left-0 top-0 w-full h-full opacity-0 cursor-pointer z-10" />
                    )}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-800 mb-2">Tiểu Sử</label>
                  <textarea name="bio" value={formData.bio} onChange={(e)=> setFormData({ ...formData, bio: e.target.value })} placeholder="Nhập tiểu sử của bạn tại đây" className="w-full h-[180px] px-4 py-3 border border-gray-200 focus:border-orange-200 focus:ring-2 focus:ring-orange-100 bg-gray-50 hover:bg-white rounded-lg text-sm transition resize-none" />
                </div>
                <button type="submit" disabled={saving} className="mt-2 px-8 h-11 bg-orange-500 hover:bg-orange-600 text-white rounded-lg text-sm font-semibold tracking-wide disabled:opacity-60 shadow-sm shadow-orange-500/20">{saving ? 'Đang lưu...' : 'LƯU'}</button>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* Subscription Modal */}
      <SubscriptionModal
        open={showSubscriptionModal}
        onClose={() => setShowSubscriptionModal(false)}
        currentSubscription={user?.subscription ?? 0}
        onSuccess={() => loadUserProfile()}
      />
    </>
  );
}
