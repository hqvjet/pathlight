'use client';

import Image from 'next/image';
import { useState, useEffect, useRef } from 'react';
import { getAvatarUrl, getUserInitials, type AvatarUser } from '@/utils/avatar';

interface AvatarProps {
  user: AvatarUser;
  size?: number;
  className?: string;
  alt?: string;
  showInitialsFallback?: boolean;
  displayName?: string;
  // Optional cache busting key (method 2)
  cacheKey?: number | string;
}

export default function Avatar({ 
  user, 
  size = 32, 
  className = '', 
  alt,
  showInitialsFallback = false,
  displayName,
  cacheKey
}: AvatarProps) {
  const [hasError, setHasError] = useState(false);
  const loadedRef = useRef(false);
  
  const avatarUrl = getAvatarUrl(user);
  // Append version param if cacheKey provided (stable between renders until changed)
  const versionedAvatarUrl = cacheKey !== undefined && cacheKey !== null
    ? `${avatarUrl}${avatarUrl.includes('?') ? '&' : '?'}v=${cacheKey}`
    : avatarUrl;
  const defaultAvatarUrl = '/assets/images/default_avatar.png';
  const finalAlt = alt || `${displayName || user.id || 'User'} avatar`;
  
  useEffect(() => {
    setHasError(false);
    loadedRef.current = false;
  }, [user?.id, user?.avatar_url, user?.avatar_id]);

  // Client-side timeout safety: if avatar takes too long, fallback gracefully
  useEffect(() => {
    if (!versionedAvatarUrl || hasError) return;
    const timeoutMs = 5000; // 5s timeout for avatars
    const timer = window.setTimeout(() => {
      if (!loadedRef.current) {
        setHasError(true);
      }
    }, timeoutMs);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [versionedAvatarUrl]);
  
  const handleImageError = () => {
    setHasError(true);
  };

  // Initials fallback if enabled and image failed
  if (showInitialsFallback && hasError) {
    const initials = getUserInitials(displayName || user.id || '?');
    return (
      <div 
        className={`
          inline-flex items-center justify-center 
          bg-gradient-to-br from-blue-500 to-purple-600 
          text-white font-semibold rounded-full
          ${className}
        `}
        style={{ width: size, height: size, fontSize: size * 0.4 }}
        title={finalAlt}
      >
        {initials}
      </div>
    );
  }

  // Image avatar with fallback to default
  const srcToUse = hasError ? defaultAvatarUrl : versionedAvatarUrl;

  return (
    <Image
      src={srcToUse}
      alt={finalAlt}
      width={size}
      height={size}
      className={`rounded-full object-cover ${className}`}
      onError={handleImageError}
  onLoadingComplete={() => { loadedRef.current = true; }}
  priority={size > 64}
  // Avoid Next.js image optimization proxy to prevent upstream timeouts (504)
  // when the avatar endpoint is slow. Let the browser fetch directly and
  // fall back via onError to a local placeholder.
  unoptimized
  loading={size > 64 ? undefined : 'lazy'}
    />
  );
}
