'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { showToast } from '@/utils/toast';
import { api, storage } from '@/utils/api';
import Avatar from '@/components/common/Avatar';
import Layout from '@/components/common/Layout';

interface UserProfile {
  id: string;
  email: string;
  given_name?: string;
  family_name?: string;
  name?: string;
  birth_date?: string;
  dob?: string;
  sex?: string;
  bio?: string;
  avatar_id?: string;
  avatar_url?: string;
  level?: number;
  current_exp?: number;
  require_exp?: number;
  course_num?: number;
  total_courses?: number;
  completed_courses?: number;
  quiz_num?: number;
  total_quizzes?: number;
  lesson_num?: number;
  created_at?: string;
}

export default function ProfilePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [avatarLoading, setAvatarLoading] = useState(false);
  const [avatarKey, setAvatarKey] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [formData, setFormData] = useState({
    given_name: '',
    family_name: '',
    birth_date: '',
    sex: '',
    bio: '',
  });

  const loadUserProfile = useCallback(async () => {
    try {
      let response = await api.user.getInfo();
      if (response.status === 401) {
        storage.removeToken();
        router.push('/auth/signin');
        return;
      }
      if (response.status !== 200) {
        response = await api.user.getDashboard();
        if (response.status === 401) {
          storage.removeToken();
          router.push('/auth/signin');
          return;
        }
      }
      if (response.status === 200) {
        const responseData: unknown = response.data;
        let userData: unknown;
        if (responseData && typeof responseData === 'object') {
          if ('info' in responseData) {
            userData = (responseData as { info: unknown }).info;
          } else if ('Info' in responseData) {
            userData = (responseData as { Info: unknown }).Info;
          } else {
            userData = responseData;
          }
        } else {
          userData = responseData;
        }
        const userObj = userData as UserProfile;
        if (!userObj || (!userObj.email && !userObj.id)) {
          showToast.authError('Dữ liệu người dùng không hợp lệ');
          return;
        }
        setUser(userObj);
        setFormData({
          given_name: userObj.given_name || '',
          family_name: userObj.family_name || '',
          birth_date: (() => {
            const dobValue = userObj.dob || userObj.birth_date || '';
            if (!dobValue) return '';
            try {
              let dateStr = dobValue;
              if (dateStr.includes('T') || dateStr.includes(' ')) {
                dateStr = dateStr.split('T')[0].split(' ')[0];
              }
              if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(dateStr)) {
                return dateStr;
              }
              if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
                const [year, month, day] = dateStr.split('-').map(Number);
                return `${String(day).padStart(2, '0')}/${String(month).padStart(2, '0')}/${year}`;
              }
              const date = new Date(dobValue);
              if (isNaN(date.getTime())) return '';
              const day = String(date.getUTCDate()).padStart(2, '0');
              const month = String(date.getUTCMonth() + 1).padStart(2, '0');
              const year = date.getUTCFullYear();
              return `${day}/${month}/${year}`;
            } catch {
              return '';
            }
          })(),
          sex: userObj.sex || '',
          bio: userObj.bio || '',
        });
      } else {
        showToast.authError('Không thể tải thông tin hồ sơ');
      }
    } catch {
      showToast.authError('Không thể tải thông tin hồ sơ');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadUserProfile();
  }, [loadUserProfile]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      const updateData: Record<string, unknown> = {
        family_name: formData.family_name || undefined,
        given_name: formData.given_name || undefined,
        dob: formData.birth_date ? (() => {
          if (formData.birth_date.includes('/')) {
            const [day, month, year] = formData.birth_date.split('/').map(Number);
            if (day && month && year) {
              const paddedMonth = String(month).padStart(2, '0');
              const paddedDay = String(day).padStart(2, '0');
              return `${year}-${paddedMonth}-${paddedDay}T12:00:00.000Z`;
            }
          }
          return undefined;
        })() : undefined,
        sex: formData.sex || undefined,
        bio: formData.bio || undefined,
      };
      Object.keys(updateData).forEach(key => {
        if (updateData[key] === undefined) {
          delete updateData[key];
        }
      });
      const response = await api.user.updateProfile(updateData);
      if (response.status === 200) {
        showToast.authSuccess('Cập nhật hồ sơ thành công!');
        setEditMode(false);
        await loadUserProfile();
      } else {
        const data: unknown = response.data;
        let errorMsg = response.error || 'Cập nhật hồ sơ thất bại';
        if (typeof data === 'object' && data !== null && 'message' in data) {
          errorMsg = (data as { message?: string }).message || errorMsg;
        }
        showToast.authError(errorMsg);
      }
    } catch {
      showToast.authError('Lỗi kết nối. Vui lòng thử lại.');
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 3 * 1024 * 1024) {
      showToast.authError('Ảnh không được vượt quá 3MB');
      return;
    }
    if (!file.type.startsWith('image/')) {
      showToast.authError('Vui lòng chọn file ảnh');
      return;
    }
    setUploading(true);
    setAvatarLoading(true);
    try {
      const response = await api.user.updateAvatar(file);
      if (response.status === 200) {
        showToast.authSuccess('Cập nhật ảnh đại diện thành công!');
        const responseData: unknown = response.data;
        const avatarData = responseData as { avatar_url?: string; avatar_id?: string };
        if (avatarData?.avatar_url || avatarData?.avatar_id) {
          setUser(prevUser => {
            if (!prevUser) return prevUser;
            return {
              ...prevUser,
              avatar_url: avatarData.avatar_url || prevUser.avatar_url,
              avatar_id: avatarData.avatar_id || prevUser.avatar_id
            };
          });
          setAvatarKey(prev => prev + 1);
        }
        setTimeout(async () => {
          await loadUserProfile();
          setAvatarKey(prev => prev + 1);
        }, 500);
      } else {
        const data: unknown = response.data;
        let errorMsg = response.error || 'Tải ảnh lên thất bại';
        if (typeof data === 'object' && data !== null && 'message' in data) {
          errorMsg = (data as { message?: string }).message || errorMsg;
        }
        showToast.authError(errorMsg);
      }
    } catch {
      showToast.authError('Lỗi kết nối. Vui lòng thử lại.');
    } finally {
      setUploading(false);
      setAvatarLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const getProgressPercentage = () => {
    if (!user?.current_exp || !user?.require_exp) return 0;
    return Math.min(100, (user.current_exp / user.require_exp) * 100);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-lg text-gray-300 animate-pulse">Đang tải thông tin...</div>
      </div>
    );
  }

  return (
    <Layout 
      title="Hồ Sơ Của Tôi" 
      user={{
        avatar_url: user?.avatar_url || '',
        name: (() => {
          if (user?.family_name && user?.given_name) {
            return `${user.family_name} ${user.given_name}`;
          } else if (user?.family_name) {
            return user.family_name;
          } else if (user?.given_name) {
            return user.given_name;
          } else if (user?.name) {
            return user.name;
          } else if (user?.email) {
            return user.email.split('@')[0];
          } else {
            return 'User';
          }
        })(),
        email: user?.email
      }}
    >
      {/* Profile Content */}
      <div className="p-4 sm:p-6 lg:p-8 min-h-screen">
        <div className="max-w-7xl mx-auto">
          {/* Hero Section */}
          <div className="bg-gradient-to-r from-gray-500 to-red-500 rounded-2xl p-6 sm:p-8 mb-8 text-white">
            <div className="flex flex-col lg:flex-row items-center lg:items-start gap-6">
                {/* Avatar Section */}
                <div className="relative group">
                  <div className="w-24 h-24 sm:w-32 sm:h-32 lg:w-40 lg:h-40 rounded-full overflow-hidden bg-white/20 flex items-center justify-center relative">
                    {avatarLoading && (
                      <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-10">
                        <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      </div>
                    )}
                    <Avatar 
                      key={`profile-avatar-${avatarKey}-${user?.avatar_id || user?.avatar_url || 'default'}`}
                      user={user} 
                      size={160} 
                      className="w-full h-full"
                      displayName={(() => {
                        // Hiển thị tên thật, nếu không có thì dùng phần trước @ của email
                        if (user?.family_name && user?.given_name) {
                          return `${user.family_name} ${user.given_name}`;
                        } else if (user?.family_name) {
                          return user.family_name;
                        } else if (user?.given_name) {
                          return user.given_name;
                        } else if (user?.name) {
                          return user.name;
                        } else if (user?.email) {
                          return user.email.split('@')[0];
                        } else {
                          return 'User';
                        }
                      })()}
                      showInitialsFallback={true}
                    />
                  </div>
                  
                  {/* Upload Button */}
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    className="absolute bottom-0 right-0 w-8 h-8 sm:w-10 sm:h-10 bg-white text-orange-500 rounded-full flex items-center justify-center shadow-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
                  >
                    {uploading ? (
                      <div className="w-4 h-4 border-2 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                      <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    )}
                  </button>
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarUpload}
                    className="hidden"
                  />
                </div>

                {/* User Info */}
                <div className="flex-1 text-center lg:text-left">
                  <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-2">
                    {(() => {
                      // Combine name with more flexible logic
                      if (user?.family_name && user?.given_name) {
                        return `${user.family_name} ${user.given_name}`;
                      } else if (user?.family_name) {
                        return user.family_name;
                      } else if (user?.given_name) {
                        return user.given_name;
                      } else if (user?.name) {
                        return user.name;
                      } else {
                        return user?.email || 'Người dùng';
                      }
                    })()}
                  </h1>
                  <p className="text-white/80 mb-4 text-sm sm:text-base">{user?.email}</p>
                  
                  {/* Stats Row */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                    <div className="text-center">
                      <div className="text-xl sm:text-2xl font-bold">{user?.level || 1}</div>
                      <div className="text-xs sm:text-sm text-white/80">Level</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl sm:text-2xl font-bold">{user?.total_courses || user?.course_num || 0}</div>
                      <div className="text-xs sm:text-sm text-white/80">Khóa học</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl sm:text-2xl font-bold">{user?.total_quizzes || user?.quiz_num || 0}</div>
                      <div className="text-xs sm:text-sm text-white/80">Quiz</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl sm:text-2xl font-bold">{user?.lesson_num || 0}</div>
                      <div className="text-xs sm:text-sm text-white/80">Bài học</div>
                    </div>
                  </div>

                  {/* Experience Progress */}
                  {user?.require_exp && (
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Kinh nghiệm</span>
                        <span>{user.current_exp?.toLocaleString() || 0} / {user.require_exp.toLocaleString()}</span>
                      </div>
                      <div className="w-full bg-white/20 rounded-full h-3">
                        <div 
                          className="bg-white h-3 rounded-full transition-all duration-500"
                          style={{ width: `${getProgressPercentage()}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Edit Toggle */}
                <div className="lg:self-start">
                  <button
                    onClick={() => setEditMode(!editMode)}
                    className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors text-white font-medium"
                  >
                    {editMode ? 'Hủy Bỏ' : 'Chỉnh sửa'}
                  </button>
                </div>
              </div>
            </div>

            {/* Profile Form */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Main Form */}
              <div className="lg:col-span-2">
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-6">Thông tin cá nhân</h2>
                  
                  <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Name Fields */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Họ
                        </label>
                        <input
                          type="text"
                          name="family_name"
                          value={formData.family_name}
                          onChange={handleInputChange}
                          disabled={!editMode}
                          placeholder="Nhập họ của bạn"
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-600"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Tên
                        </label>
                        <input
                          type="text"
                          name="given_name"
                          value={formData.given_name}
                          onChange={handleInputChange}
                          disabled={!editMode}
                          placeholder="Nhập tên của bạn"
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-600"
                        />
                      </div>
                    </div>

                    {/* Email Field (Read-only) */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email
                      </label>
                      <input
                        type="email"
                        value={user?.email || ''}
                        readOnly
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-600 cursor-not-allowed"
                      />
                    </div>

                    {/* Birth Date */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Ngày sinh
                      </label>
                      <input
                        type="date"
                        name="birth_date"
                        value={(() => {
                          // Convert dd/mm/yyyy to yyyy-mm-dd for date input
                          if (!formData.birth_date) return '';
                          if (formData.birth_date.includes('/')) {
                            const [day, month, year] = formData.birth_date.split('/');
                            if (day && month && year && year.length === 4) {
                              return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
                            }
                            return '';
                          }
                          // Already in yyyy-mm-dd format
                          return formData.birth_date;
                        })()}
                        onChange={(e) => {
                          const value = e.target.value; // This will be in yyyy-mm-dd format
                          if (value) {
                            // Chuyển đổi yyyy-mm-dd thành dd/mm/yyyy không qua Date object để tránh lỗi timezone
                            const [year, month, day] = value.split('-');
                            if (year && month && day) {
                              const ddmmyyyy = `${day}/${month}/${year}`;
                              setFormData(prev => ({ ...prev, birth_date: ddmmyyyy }));
                            }
                          } else {
                            setFormData(prev => ({ ...prev, birth_date: '' }));
                          }
                        }}
                        disabled={!editMode}
                        max={new Date().toISOString().split('T')[0]} // Không cho chọn ngày tương lai
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-600"
                      />
                      {formData.birth_date && (
                        <p className="mt-1 text-sm text-gray-500">
                          Ngày sinh: {formData.birth_date}
                        </p>
                      )}
                    </div>

                    {/* Bio */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Giới thiệu bản thân
                      </label>
                      <textarea
                        name="bio"
                        value={formData.bio}
                        onChange={handleInputChange}
                        disabled={!editMode}
                        rows={4}
                        placeholder="Viết vài dòng giới thiệu về bản thân..."
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none disabled:bg-gray-50 disabled:text-gray-600"
                      />
                    </div>

                    {/* Submit Button */}
                    {editMode && (
                      <div className="flex gap-3 pt-4">
                        <button
                          type="submit"
                          disabled={saving}
                          className="flex-1 sm:flex-none bg-orange-500 hover:bg-orange-600 text-white font-medium py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditMode(false)}
                          className="flex-1 sm:flex-none bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-3 px-6 rounded-lg transition-colors"
                        >
                          Hủy
                        </button>
                      </div>
                    )}
                  </form>
                </div>
              </div>

              {/* Side Panel */}
              <div className="space-y-6">
                {/* Account Info */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Thông tin tài khoản</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Trạng thái</span>
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">
                        Hoạt động
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Ngày tham gia</span>
                      <span className="text-sm font-medium">
                        {user?.created_at ? (() => {
                          try {
                            const date = new Date(user.created_at);
                            if (isNaN(date.getTime())) return 'N/A';
                            const day = String(date.getUTCDate()).padStart(2, '0');
                            const month = String(date.getUTCMonth() + 1).padStart(2, '0');
                            const year = date.getUTCFullYear();
                            return `${day}/${month}/${year}`;
                          } catch {
                            return 'N/A';
                          }
                        })() : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">ID người dùng</span>
                      <span className="text-sm font-mono text-gray-500">
                        {user?.id?.slice(-8) || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
    </Layout>
  );
}
