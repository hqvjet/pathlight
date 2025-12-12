export interface AvatarUser {
  id?: string;
  avatar_url?: string;
  avatar_id?: string;
  google_avatar_url?: string;
}

// Return ordered avatar sources: S3 proxy (by id), then explicit avatar_url, then default
export const getAvatarSources = (user: AvatarUser): string[] => {
  const sources: string[] = [];
  if (!user) return ['/assets/images/default_avatar.png'];

  if (user.avatar_url) {
    sources.push(user.avatar_url);
  }
  if (user.id) {
    sources.push(`/api/users/avatar?user-id=${encodeURIComponent(user.id)}`);
  }

  if (!sources.includes('/assets/images/default_avatar.png')) {
    sources.push('/assets/images/default_avatar.png');
  }
  return sources;
};

export const getAvatarUrl = (user: AvatarUser): string => {
  const sources = getAvatarSources(user);
  return sources[0];
};

export const getUserInitials = (name: string): string => {
  if (!name) return '?';
  const words = name.trim().split(/\s+/);
  if (words.length === 1) return words[0][0].toUpperCase();
  return words.slice(0, 2).map(w => w[0].toUpperCase()).join('');
};
