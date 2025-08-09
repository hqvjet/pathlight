import React, { useRef } from 'react';
import Avatar from '@/components/common/Avatar';
import { UserProfile } from './types';

interface Props {
  user: UserProfile;
  uploading: boolean;
  avatarLoading: boolean;
  avatarKey: number;
  onUpload: (file: File) => void;
}

export const ProfileAvatar: React.FC<Props> = ({ user, uploading, avatarLoading, avatarKey, onUpload }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  return (
    <div className="relative group w-full h-full select-none">
      <div className="relative w-full h-full flex items-center justify-center overflow-hidden bg-[#f3f3f3]">
        {avatarLoading && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center z-20">
            <div className="w-10 h-10 border-2 border-white border-t-transparent rounded-full animate-spin" />
          </div>
        )}
        <Avatar
          key={`profile-avatar-${avatarKey}-${user?.avatar_id || user?.avatar_url || 'default'}`}
          user={user}
          size={240}
          className="w-full h-full object-cover !rounded-none"
          displayName={user.family_name && user.given_name ? `${user.family_name} ${user.given_name}` : (user.name || user.email?.split('@')[0] || 'User')}
          showInitialsFallback
        />
        <button
          type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="absolute bottom-0 left-0 w-full h-10 flex items-center justify-center gap-2 text-sm font-medium text-white bg-black/55 backdrop-blur-[2px] hover:bg-black/70 transition-colors z-10 disabled:opacity-60"
        >
          {uploading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
              <span className="text-xs sm:text-sm">Tải Ảnh Lên</span>
            </>
          )}
        </button>
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={(e)=> { const f = e.target.files?.[0]; if (f) onUpload(f); e.target.value=''; }}
        className="hidden"
      />
    </div>
  );
};
