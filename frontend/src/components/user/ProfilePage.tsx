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
    <div className="px-8 pt-10 pb-16 bg-[#f7f9fc] min-h-screen">
      <div className="max-w-[1330px] mx-auto">
        <div className="bg-white rounded-md shadow-sm shadow-black/[0.02] p-10">
          <h1 className="text-[26px] font-semibold mb-8">Thông Tin Hồ Sơ</h1>
          {user && (
            <div className="mb-8 grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-gradient-to-r from-orange-500/90 to-violet-600 text-white shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-lg font-semibold">Cấp độ</div>
                  <div className="px-3 py-1 rounded-full bg-white/20 text-sm font-semibold">Lv {user.level || 1}</div>
                </div>
                <div className="h-3 w-full bg-white/25 rounded-full overflow-hidden">
                  <div className="h-full bg-white shadow-sm" style={{ width: `${expPercent}%` }} />
                </div>
                <div className="mt-2 flex justify-between text-xs text-white/90">
                  <span>{user.current_exp || 0} EXP</span>
                  <span>{user.require_exp || 0} EXP</span>
                </div>
              </div>
              <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 shadow-sm flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-gray-900">Thời gian nhắc học</div>
                  <div className="text-xs text-gray-600">Chọn giờ để nhận thông báo học tập hằng ngày</div>
                </div>
                <div className="flex items-center gap-2">
                  <input type="time" value={remindTime} onChange={(e)=> setRemindTime(e.target.value)} className="rounded border border-gray-200 px-3 py-2 text-sm shadow-sm" />
                  <button type="button" onClick={()=> updateRemindTime(remindTime)} disabled={remindSaving} className="px-3 py-2 bg-orange-500 text-white text-sm rounded shadow hover:bg-orange-600 disabled:opacity-60">{remindSaving ? 'Đang lưu' : 'Lưu'}</button>
                </div>
              </div>
            </div>
          )}
          <div className="flex flex-col xl:flex-row gap-12">
            <div className="flex-1">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-800 mb-2">Họ Và Tên (*)</label>
                    <input name="family_name" value={formData.family_name} onChange={(e)=> setFormData({ ...formData, family_name: e.target.value })} placeholder="Nhập họ và tên đệm của bạn" className="w-full h-11 px-4 border border-transparent focus:border-gray-300 focus:ring-0 bg-[#f9fafb] hover:bg-white rounded-sm text-sm transition" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-800 mb-2">&nbsp;</label>
                    <input name="given_name" value={formData.given_name} onChange={(e)=> setFormData({ ...formData, given_name: e.target.value })} placeholder="Nhập tên của bạn" className="w-full h-11 px-4 border border-transparent focus:border-gray-300 focus:ring-0 bg-[#f9fafb] hover:bg-white rounded-sm text-sm transition" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-800 mb-2">Email (*)</label>
                  <input value={user?.email || ''} disabled className="w-full h-11 px-4 border border-transparent bg-[#f0f1f2] text-sm text-gray-600 rounded-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-800 mb-2">Ngày Sinh</label>
                  <div className="relative">
                    <input name="birth_date" value={formData.birth_date} onChange={(e)=> setFormData({ ...formData, birth_date: e.target.value })} placeholder="DD / MM / YYYY" className="w-full h-11 px-4 pr-10 border border-transparent focus:border-gray-300 focus:ring-0 bg-[#f9fafb] hover:bg-white rounded-sm text-sm transition" />
                    <button type="button" onClick={openDatePicker} className="absolute inset-y-0 right-0 w-11 flex items-center justify-center text-gray-500 hover:text-gray-700">
                      <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M8 2v4M16 2v4M3 10h18M5 6h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2z" /></svg>
                    </button>
                    {showNativeDate && (
                      <input id="hidden-native-date" type="date" value={nativeDateValue} onChange={handleNativeDateChange} onBlur={()=> setShowNativeDate(false)} className="absolute opacity-0 pointer-events-none" />
                    )}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-800 mb-2">Tiểu Sử</label>
                  <textarea name="bio" value={formData.bio} onChange={(e)=> setFormData({ ...formData, bio: e.target.value })} placeholder="Nhập tiểu sử của bạn tại đây" className="w-full h-[180px] px-4 py-3 border border-transparent focus:border-gray-300 focus:ring-0 bg-[#f9fafb] hover:bg-white rounded-sm text-sm transition resize-none" />
                </div>
                <button type="submit" disabled={saving} className="mt-2 px-8 h-11 bg-orange-500 hover:bg-orange-600 text-white rounded-sm text-sm font-semibold tracking-wide disabled:opacity-60 shadow-sm shadow-orange-500/20">{saving ? 'Đang lưu...' : 'LƯU'}</button>
              </form>
            </div>
            <div className="w-full max-w-[255px]">
              <div className="bg-[#f5f6f8] rounded-sm pt-8 pb-6 px-6 flex flex-col items-center shadow-sm shadow-black/[0.04]">
                <div className="w-full aspect-[1/1.05] min-h-[240px] mb-6 relative">
                  <ProfileAvatar user={user} uploading={uploading} avatarLoading={avatarLoading} avatarKey={avatarKey} onUpload={uploadAvatar} />
                  {!user && (
                    <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-400">Đang tải ảnh...</div>
                  )}
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
