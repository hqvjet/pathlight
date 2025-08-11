export interface AvatarUser {
  id?: string;
  avatar_url?: string;
  avatar_id?: string;
}

export const getAvatarUrl = (user: AvatarUser): string => {
  if (!user) return '/assets/images/default_avatar.png';
  const id = user.id;

  // If we have a user id, always build canonical endpoint with user-id (public avatar endpoint handles fallback & defaults)
  if (id) {
    return `/api/user/avatar?user-id=${id}`;
  }

  // Legacy: external absolute URL (keep origin/path)
  if (user?.avatar_url && user.avatar_url.startsWith('http')) {
    try {
      const urlObj = new URL(user.avatar_url);
      if (/\/avatar\/?/.test(urlObj.pathname)) {
        // Try to extract user-id from query if present
        const qId = urlObj.searchParams.get('user-id');
        if (qId) return `/api/user/avatar?user-id=${qId}`;
        return '/api/user/avatar';
      }
      return urlObj.origin + urlObj.pathname;
    } catch {
      return '/api/user/avatar';
    }
  }

  // Fallback
  return '/assets/images/default_avatar.png';
};

export const getUserInitials = (name: string): string => {
  if (!name) return '?';
  const words = name.trim().split(/\s+/);
  if (words.length === 1) return words[0][0].toUpperCase();
  return words.slice(0, 2).map(w => w[0].toUpperCase()).join('');
};
