'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useProfileData } from './profile/hooks';
import { ProfileAvatar } from './profile/ProfileAvatar';
import { ProfileFormData } from './profile/types';

export default function ProfilePage() {
  const { loading, saving, user, uploading, avatarLoading, avatarKey, formData, setFormData, loadUserProfile, updateProfile, uploadAvatar, remindTime, setRemindTime, updateRemindTime, remindSaving } = useProfileData();
  const [showNativeDate, setShowNativeDate] = useState(false);
  const [nativeDateValue, setNativeDateValue] = useState('');

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
        <div className="max-w-[1330px] mx-auto px-6 md:px-8 py-12">
          <div className="bg-white/90 backdrop-blur rounded-2xl border border-gray-100 shadow-[0_8px_30px_rgba(15,23,42,0.05)] p-8 md:p-10">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">
              <div>
                <h1 className="text-[26px] font-semibold text-gray-900 leading-tight">Thông Tin Hồ Sơ</h1>
              </div>
            </div>

          {user && (
            <div className="mb-8 grid grid-cols-1 lg:grid-cols-[1.25fr_0.75fr] gap-4">
              <div className="p-5 md:p-6 rounded-2xl bg-white border border-gray-100 shadow-sm text-gray-900">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-lg font-semibold text-gray-900">Hành trình của bạn</p>
                  </div>
                  <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                    <div className="px-3 py-1 rounded-full bg-gray-100 border border-gray-200">Rank #{user.rank ?? '—'}</div>
                    <div className="px-3 py-1 rounded-full bg-gray-100 border border-gray-200">Lv {user.level || 1}</div>
                  </div>
                </div>
                <div className="h-3 w-full bg-gray-100 rounded-full overflow-hidden border border-gray-200">
                  <div className="h-full bg-orange-500" style={{ width: `${expPercent}%` }} />
                </div>
                <div className="mt-2 flex justify-between text-xs text-gray-600">
                  <span>{currentExp} / {requireExp || 0} EXP</span>
                  <span>Còn {remainingExp} EXP lên Lv {nextLevelLabel}</span>
                </div>
                <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm text-gray-800">
                  <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
                    <div className="text-[11px] text-gray-500">Khóa học</div>
                    <div className="font-semibold text-gray-900">{courseCount}</div>
                  </div>
                  <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
                    <div className="text-[11px] text-gray-500">Bài học</div>
                    <div className="font-semibold text-gray-900">{lessonCount}</div>
                  </div>
                  <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
                    <div className="text-[11px] text-gray-500">Khóa đã hoàn thành</div>
                    <div className="font-semibold text-gray-900">{completedCourses}</div>
                  </div>
                </div>
              </div>
              <div className="p-5 md:p-6 rounded-2xl bg-white border border-gray-100 shadow-sm flex items-center gap-4">
                <div className="h-10 w-10 shrink-0 rounded-full bg-gray-100 text-gray-700 flex items-center justify-center border border-gray-200">
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3a6 6 0 00-6 6v3.5L4 15.5a1 1 0 00.7 1.7h14.6a1 1 0 00.7-1.7L18 12.5V9a6 6 0 00-6-6Z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10 19a2 2 0 004 0" />
                  </svg>
                </div>
                <div className="flex-1 flex flex-col gap-4">
                  <div className="flex items-baseline gap-2">
                    <div className="text-sm font-semibold text-gray-900">Nhắc giờ học:</div>
                    <div className="text-xs text-gray-600">Chọn giờ nhắc hằng ngày</div>
                  </div>
                  <div className="flex flex-col lg:flex-row items-start lg:items-center gap-4 w-full justify-end">
                    <div className="flex gap-2" style={{ overscrollBehavior: 'contain' }}>
                      {[
                        { label: 'Giờ', baseList: HOURS, idx: hourIdx, setIdx: setHourIdx, setter: setHour, drag: hourDrag, kind: 'hour' as const },
                        { label: 'Phút', baseList: MINUTES, idx: minuteIdx, setIdx: setMinuteIdx, setter: setMinute, drag: minuteDrag, kind: 'minute' as const },
                      ].map(({ label, baseList, idx, setIdx, setter, drag, kind }) => (
                        <div
                          key={label}
                          className="relative w-16 time-wheel"
                          data-kind={kind}
                          style={{ height: '150px', overscrollBehavior: 'contain' }}
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
                          <div className="h-full overflow-hidden border border-gray-200 rounded-xl bg-white shadow-sm">
                            <div className="absolute inset-0 pointer-events-none" style={{ boxShadow: 'inset 0 36px 36px -36px rgba(0,0,0,0.06), inset 0 -36px 36px -36px rgba(0,0,0,0.06)' }} />
                            <div className="absolute left-0 right-0 border-y border-orange-200/70 pointer-events-none" style={{ top: '50%', height: `${rowHeight}px`, marginTop: `-${rowHeight/2}px` }} />
                            <div className="h-full select-none">
                              <div className="relative" style={{ height: '150px' }}>
                                {renderWindow(baseList, idx, 3).map(({ val, key, rel }) => {
                                  const isCenter = rel === 0;
                                  return (
                                    <div
                                      key={key}
                                      className={`absolute left-0 right-0 flex items-center justify-center text-sm font-semibold cursor-pointer select-none ${isCenter ? 'text-gray-900' : 'text-gray-500 opacity-60'}`}
                                      style={{ height: `${rowHeight}px`, top: '50%', transform: `translateY(${rel * rowHeight - rowHeight / 2}px)` }}
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
                          <input
                            type="number"
                            min={0}
                            max={baseList.length - 1}
                            className="absolute left-0 right-0 mx-auto text-center text-sm font-semibold text-gray-900 rounded-md"
                            style={{ width: '100%', top: '50%', height: `${rowHeight}px`, transform: 'translateY(-50%)', opacity: 0 }}
                            onFocus={(e) => e.target.select()}
                            onChange={(e) => {
                              const raw = Number(e.target.value);
                              if (Number.isNaN(raw)) return;
                              const clamped = Math.min(baseList.length - 1, Math.max(0, raw));
                              const formatted = String(clamped).padStart(2, '0');
                              setIdx(clamped);
                              setter(formatted);
                            }}
                            aria-label={label}
                          />
                        </div>
                      ))}
                    </div>
                    <div className="flex-1 flex flex-col gap-3 min-w-[240px]">
                      <div className="flex flex-wrap gap-2">
                        {presetTimes.map((t) => (
                          <button
                            key={t}
                            type="button"
                            onClick={() => setRemindTime(t)}
                            className={`px-3 py-2 rounded-lg text-sm border transition ${remindTime === t ? 'bg-orange-50 border-orange-200 text-orange-700 shadow-sm' : 'bg-white border-gray-200 text-gray-700 hover:border-orange-200 hover:text-orange-700'}`}
                          >
                            {t}
                          </button>
                        ))}
                      </div>
                      <div className="flex gap-2 items-center flex-wrap">
                        <input
                          type="time"
                          value={remindTime}
                          onChange={(e)=> setRemindTime(e.target.value)}
                          className="rounded-lg border border-gray-200 px-3 py-2 text-sm shadow-sm bg-white focus:border-orange-200 focus:ring-2 focus:ring-orange-100"
                        />
                        <button type="button" onClick={()=> updateRemindTime(remindTime)} disabled={remindSaving} className="px-4 py-2 bg-orange-500 text-white text-sm rounded-lg shadow-sm hover:bg-orange-600 disabled:opacity-60 min-w-[72px]">{remindSaving ? 'Đang lưu' : 'Lưu'}</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="flex flex-col xl:flex-row gap-10">
            <div className="flex-1">
              <form onSubmit={handleSubmit} className="space-y-6 bg-white rounded-xl border border-gray-100 shadow-sm p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                      <input id="hidden-native-date" type="date" value={nativeDateValue} onChange={handleNativeDateChange} onBlur={()=> setShowNativeDate(false)} className="absolute opacity-0 pointer-events-none" />
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
            <div className="w-full max-w-[280px]">
              <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 flex flex-col items-center gap-4">
                <div className="w-full aspect-[1/1.02] min-h-[240px] rounded-lg bg-gray-50/60 border border-dashed border-gray-200 relative">
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
        </div>
      </div>
    </div>
      <style jsx global>{`
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        .no-scrollbar::-webkit-scrollbar { display: none; }
      `}</style>
    </>
  );
}
