'use client';

import { useEffect, useState } from 'react';
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

  const expPercent = (() => {
    if (!user?.require_exp || user.require_exp <= 0) return 0;
    return Math.min(100, Math.round(((user.current_exp || 0) / user.require_exp) * 100));
  })();

  const remainingExp = Math.max((user?.require_exp || 0) - (user?.current_exp || 0), 0);
  const nextLevelLabel = (user?.level || 1) + 1;

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
              <div className="p-5 md:p-6 rounded-2xl bg-gradient-to-r from-[#ff8a4c] via-[#f05a8a] to-[#7c6ff9] text-white shadow-lg shadow-orange-500/15">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-xl font-semibold text-white/85">Hành trình của bạn</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="px-3 py-1 rounded-full bg-white/20 border border-white/25 text-sm font-semibold">Rank #{user.rank ?? '—'}</div>
                    <div className="px-3 py-1 rounded-full bg-white/25 text-sm font-semibold">Lv {user.level || 1}</div>
                  </div>
                </div>
                <div className="h-3 w-full bg-white/25 rounded-full overflow-hidden ring-1 ring-white/20">
                  <div className="h-full bg-white shadow-sm shadow-black/10" style={{ width: `${expPercent}%` }} />
                </div>
                <div className="mt-2 flex justify-between text-xs text-white/90">
                  <span>{user.current_exp || 0} EXP</span>
                  <span>{remainingExp} EXP nữa lên Lv {nextLevelLabel}</span>
                </div>
              </div>
              <div className="p-5 md:p-6 rounded-2xl bg-white border border-gray-100 shadow-sm flex items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="h-10 w-10 rounded-full bg-orange-50 text-orange-600 flex items-center justify-center shadow-inner">
                    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3a6 6 0 00-6 6v3.5L4 15.5a1 1 0 00.7 1.7h14.6a1 1 0 00.7-1.7L18 12.5V9a6 6 0 00-6-6Z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 19a2 2 0 004 0" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-900">Thời gian nhắc học</div>
                    <div className="text-xs text-gray-600">Chọn giờ để nhận thông báo học tập hằng ngày.</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <input type="time" value={remindTime} onChange={(e)=> setRemindTime(e.target.value)} className="rounded-lg border border-gray-200 px-3 py-2 text-sm shadow-sm bg-white focus:border-orange-200 focus:ring-2 focus:ring-orange-100" />
                  <button type="button" onClick={()=> updateRemindTime(remindTime)} disabled={remindSaving} className="px-3 py-2 bg-orange-500 text-white text-sm rounded-lg shadow hover:bg-orange-600 disabled:opacity-60">{remindSaving ? 'Đang lưu' : 'Lưu'}</button>
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
  );
}
