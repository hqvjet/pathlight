import { API_CONFIG } from '@/config';

export interface AvatarUser {
  id?: string;
  avatar_url?: string;
  avatar_id?: string;
}

export const getAvatarUrl = (user: AvatarUser): string => {
  // Google OAuth avatar (most reliable)
  if (user?.avatar_url && user.avatar_url.startsWith('http')) {
    const separator = user.avatar_url.includes('?') ? '&' : '?';
    const cacheParam = `_t=${Date.now()}&_r=${Math.random().toString(36).substr(2, 9)}`;
    return `${user.avatar_url}${separator}${cacheParam}`;
  }

  // Google OAuth avatar (legacy support)
  if (user?.avatar_id && user.avatar_id.startsWith('http')) {
    const separator = user.avatar_id.includes('?') ? '&' : '?';
    const cacheParam = `_t=${Date.now()}&_r=${Math.random().toString(36).substr(2, 9)}`;
    return `${user.avatar_id}${separator}${cacheParam}`;
  }

  // AWS S3 custom uploaded avatar
  if (user?.id) {
    const s3Url = `${API_CONFIG.USER_SERVICE_URL}/avatar/?user_id=${user.id}`;
    const cacheParam = `&_t=${Date.now()}&_r=${Math.random().toString(36).substr(2, 9)}`;
    return `${s3Url}${cacheParam}`;
  }
  
  // Default avatar
  return '/assets/images/default_avatar.png';
};

export const getUserInitials = (name: string): string => {
  if (!name) return '?';
  
  const words = name.trim().split(/\s+/);
  if (words.length === 1) {
    return words[0][0].toUpperCase();
  }
  
  return words.slice(0, 2).map(word => word[0].toUpperCase()).join('');
};
