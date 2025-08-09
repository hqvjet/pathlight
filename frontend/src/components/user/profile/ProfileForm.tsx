import React from 'react';
import { ProfileFormData } from './types';

interface Props {
  formData: ProfileFormData;
  setFormData: (v: ProfileFormData) => void;
  editMode: boolean;
  saving: boolean;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
}

export const ProfileForm: React.FC<Props> = ({ formData, setFormData, editMode, saving, onSubmit, onCancel }) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };
  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Họ</label>
          <input type="text" name="family_name" value={formData.family_name} onChange={handleChange} disabled={!editMode} placeholder="Nhập họ của bạn" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-600" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Tên</label>
          <input type="text" name="given_name" value={formData.given_name} onChange={handleChange} disabled={!editMode} placeholder="Nhập tên của bạn" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-600" />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Giới thiệu bản thân</label>
        <textarea name="bio" value={formData.bio} onChange={handleChange} disabled={!editMode} rows={4} placeholder="Viết vài dòng giới thiệu về bản thân..." className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none disabled:bg-gray-50 disabled:text-gray-600" />
      </div>
      {editMode && (
        <div className="flex gap-3 pt-4">
          <button type="submit" disabled={saving} className="flex-1 sm:flex-none bg-orange-500 hover:bg-orange-600 text-white font-medium py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed">{saving ? 'Đang lưu...' : 'Lưu thay đổi'}</button>
          <button type="button" onClick={onCancel} className="flex-1 sm:flex-none bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-3 px-6 rounded-lg transition-colors">Hủy</button>
        </div>
      )}
    </form>
  );
};
