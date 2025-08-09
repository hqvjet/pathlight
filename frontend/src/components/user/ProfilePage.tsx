'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useProfileData } from './profile/hooks';
import Layout from '@/components/common/Layout';
import { ProfileAvatar } from './profile/ProfileAvatar';
import { ProfileFormData } from './profile/types';

// Simple date picker using native input[type=date] overlay triggered by icon button

export default function ProfilePage() {
  const router = useRouter();
  const { loading, saving, user, uploading, avatarLoading, avatarKey, formData, setFormData, loadUserProfile, updateProfile, uploadAvatar } = useProfileData();
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

  const displayName = user?.family_name && user?.given_name ? `${user.family_name} ${user.given_name}` : (user?.name || user?.email?.split('@')[0] || 'User');

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
    <Layout title="Hồ Sơ Của Tôi" user={{ avatar_url: user?.avatar_url || '', name: displayName, email: user?.email }}>
      <div className="px-8 pt-10 pb-16 bg-[#f7f9fc] min-h-screen">
        <div className="max-w-[1330px] mx-auto">
          <div className="bg-white rounded-md shadow-sm shadow-black/[0.02] p-10">
            <h1 className="text-[26px] font-semibold mb-8">Thông Tin Hồ Sơ</h1>
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
                    <ProfileAvatar user={user!} uploading={uploading} avatarLoading={avatarLoading} avatarKey={avatarKey} onUpload={uploadAvatar} />
                  </div>
                  <p className="text-[11px] leading-relaxed text-center text-gray-600">Ảnh tải lên không được quá 3MB<br/>Nên chọn ảnh có tỉ lệ 1:1</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
