export interface AvatarUser {
  id?: string;
  avatar_url?: string;
  avatar_id?: string;
}

export const getAvatarUrl = (user: AvatarUser): string => {
  if (!user) return '/assets/images/default_avatar.png';

  // 1. If explicit avatar_url provided, use it as-is (relative or absolute)
  if (user.avatar_url) {
    return user.avatar_url;
  }

  // 2. Fallback build canonical endpoint from id
  if (user.id) {
    return `/api/user/avatar?user-id=${user.id}`;
  }

  // 3. Default placeholder
  return '/assets/images/default_avatar.png';
};

export const getUserInitials = (name: string): string => {
  if (!name) return '?';
  const words = name.trim().split(/\s+/);
  if (words.length === 1) return words[0][0].toUpperCase();
  return words.slice(0, 2).map(w => w[0].toUpperCase()).join('');
};
