import { useCallback, useState } from 'react';
import { showToast } from '@/utils/toast';
import { storage } from '@/utils/api';
import { api } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { ProfileFormData, UserProfile } from './types';

export function useProfileData() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [editMode, setEditMode] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [avatarLoading, setAvatarLoading] = useState(false);
  const [avatarKey, setAvatarKey] = useState(0);
  const [formData, setFormData] = useState<ProfileFormData>({ given_name: '', family_name: '', birth_date: '', sex: '', bio: '' });
  const [remindTime, setRemindTime] = useState('');
  const [remindSaving, setRemindSaving] = useState(false);

  const normalizeAvatarUrl = useCallback((id?: string, avatarUrl?: string) => {
    if (id) return `/api/users/avatar?user-id=${encodeURIComponent(id)}`;
    return '/assets/images/default_avatar.png';
  }, []);

  const loadUserProfile = useCallback(async () => {
    try {
      let response = await api.user.getInfo();
      if (response.status === 401) { storage.removeToken(); router.push('/auth/signin'); return; }
      if (response.status !== 200) {
        response = await api.user.getDashboard();
        if (response.status === 401) { storage.removeToken(); router.push('/auth/signin'); return; }
      }
      if (response.status === 200) {
        const responseData = response.data as unknown;
        let userData: unknown = responseData;
        if (responseData && typeof responseData === 'object') {
          if ('info' in responseData) userData = (responseData as { info: UserProfile }).info;
          else if ('Info' in responseData) userData = (responseData as { Info: UserProfile }).Info;
        }
        const userObj = userData as UserProfile;
        if (!userObj || (!userObj.email && !userObj.id)) { showToast.authError('Dữ liệu người dùng không hợp lệ'); return; }
        const googleAvatar = (userObj as { google_avatar_url?: string }).google_avatar_url || userObj.avatar_url;
        // Normalize avatar_url for profile page through the Next.js proxy
        userObj.avatar_url = normalizeAvatarUrl(userObj.id, userObj.avatar_url);
        userObj.google_avatar_url = googleAvatar;
        setUser(userObj);
        setRemindTime(userObj.remind_time || '');
        setFormData({
          given_name: userObj.given_name || '',
          family_name: userObj.family_name || '',
          birth_date: formatInitialBirthDate(userObj),
          sex: userObj.sex || '',
          bio: userObj.bio || ''
        });
        setAvatarKey(k=>k); // keep current key (no change unless upload)
      } else showToast.authError('Không thể tải thông tin hồ sơ');
    } catch { showToast.authError('Không thể tải thông tin hồ sơ'); }
    finally { setLoading(false); }
  }, [router, normalizeAvatarUrl]);

  const updateProfile = async (form: ProfileFormData) => {
    setSaving(true);
    try {
      const payload = buildProfilePayload(form);
      const response = await api.user.updateProfile(payload);
      if (response.status === 200) {
        showToast.authSuccess('Cập nhật hồ sơ thành công!');
        setEditMode(false);
        await loadUserProfile();
      } else {
        const data = response.data as { message?: string } | undefined;
        let errorMsg = response.error || 'Cập nhật hồ sơ thất bại';
        if (data?.message) errorMsg = data.message;
        showToast.authError(errorMsg);
      }
    } catch { showToast.authError('Lỗi kết nối. Vui lòng thử lại.'); }
    finally { setSaving(false); }
  };

  const uploadAvatar = async (file: File) => {
    if (file.size > 3 * 1024 * 1024) { showToast.authError('Ảnh không được vượt quá 3MB'); return; }
    if (!file.type.startsWith('image/')) { showToast.authError('Vui lòng chọn file ảnh'); return; }
    setUploading(true); setAvatarLoading(true);
    try {
      const response = await api.user.updateAvatar(file);
      if (response.status === 200) {
        showToast.authSuccess('Cập nhật ảnh đại diện thành công!');
        const avatarData = response.data as { avatar_url?: string; avatar_id?: string } | undefined;
        if (avatarData && (avatarData.avatar_url || avatarData.avatar_id)) {
          setUser(prev => prev ? { ...prev, avatar_url: normalizeAvatarUrl(prev.id, avatarData.avatar_url || prev.avatar_url), avatar_id: avatarData.avatar_id || prev.avatar_id } : prev);
          setAvatarKey(k => k + 1); // bump version immediately
        }
        setTimeout(async () => { await loadUserProfile(); setAvatarKey(k => k + 1); }, 500);
      } else {
        const data = response.data as { message?: string } | undefined; let errorMsg = response.error || 'Tải ảnh lên thất bại'; if (data?.message) errorMsg = data.message; showToast.authError(errorMsg);
      }
    } catch { showToast.authError('Lỗi kết nối. Vui lòng thử lại.'); }
    finally { setUploading(false); setAvatarLoading(false); }
  };

  const updateRemindTime = async (time: string) => {
    if (!time) { showToast.authError('Vui lòng chọn giờ nhắc nhở'); return; }
    setRemindSaving(true);
    try {
      const response = await api.user.setNotifyTime({ remind_time: time });
      if (response.status === 200) {
        setRemindTime(time);
        setUser(prev => prev ? { ...prev, remind_time: time } : prev);
        showToast.authSuccess('Đã cập nhật thời gian nhắc nhở');
      } else {
        showToast.authError('Cập nhật thời gian nhắc nhở thất bại');
      }
    } catch {
      showToast.authError('Lỗi kết nối. Vui lòng thử lại.');
    } finally {
      setRemindSaving(false);
    }
  };

  return { loading, saving, user, editMode, setEditMode, uploading, avatarLoading, avatarKey, formData, setFormData, loadUserProfile, updateProfile, uploadAvatar, remindTime, setRemindTime, updateRemindTime, remindSaving };
}

function formatInitialBirthDate(user: UserProfile) {
  const dobValue = user.dob || user.birth_date || '';
  if (!dobValue) return '';
  try {
    let dateStr = dobValue;
    if (dateStr.includes('T') || dateStr.includes(' ')) dateStr = dateStr.split('T')[0].split(' ')[0];
    if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(dateStr)) return dateStr;
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
      const [year, month, day] = dateStr.split('-').map(Number);
      return `${String(day).padStart(2,'0')}/${String(month).padStart(2,'0')}/${year}`;
    }
    const date = new Date(dobValue);
    if (isNaN(date.getTime())) return '';
    const day = String(date.getUTCDate()).padStart(2,'0');
    const month = String(date.getUTCMonth()+1).padStart(2,'0');
    const year = date.getUTCFullYear();
    return `${day}/${month}/${year}`;
  } catch { return ''; }
}

function convertDateToISO(ddmmyyyy?: string) {
  if (!ddmmyyyy) return undefined;
  if (ddmmyyyy.includes('/')) {
    const [day, month, year] = ddmmyyyy.split('/').map(Number);
    if (day && month && year) return `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}T12:00:00.000Z`;
  }
  return undefined;
}

// Build payload to match new change-info API: always include keys, send null when empty
function buildProfilePayload(form: ProfileFormData) {
  return {
    family_name: form.family_name.trim() === '' ? null : form.family_name.trim(),
    given_name: form.given_name.trim() === '' ? null : form.given_name.trim(),
    dob: form.birth_date ? convertDateToISO(form.birth_date) || null : null,
    sex: form.sex.trim() === '' ? null : form.sex.trim(),
    bio: form.bio.trim() === '' ? null : form.bio.trim(),
  };
}
