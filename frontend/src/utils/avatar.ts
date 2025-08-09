export interface AvatarUser {
  id?: string;
  avatar_url?: string;
  avatar_id?: string;
}

export const getAvatarUrl = (user: AvatarUser): string => {
  // Google OAuth avatar absolute URL
  if (user?.avatar_url && user.avatar_url.startsWith('http')) {
    const separator = user.avatar_url.includes('?') ? '&' : '?';
    const cacheParam = `_t=${Date.now()}&_r=${Math.random().toString(36).substr(2, 9)}`;
    return `${user.avatar_url}${separator}${cacheParam}`;
  }

  // Prefer stored avatar id served by our proxy
  if (user?.avatar_id) {
    const url = `/api/users/avatar?avatar_id=${encodeURIComponent(user.avatar_id)}`;
    const cacheParam = `&_t=${Date.now()}&_r=${Math.random().toString(36).substr(2, 9)}`;
    return `${url}${cacheParam}`;
  }

  // Fallback to user id-based avatar fetch via proxy
  if (user?.id) {
    const url = `/api/users/avatar?user_id=${encodeURIComponent(user.id)}`;
    const cacheParam = `&_t=${Date.now()}&_r=${Math.random().toString(36).substr(2, 9)}`;
    return `${url}${cacheParam}`;
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
