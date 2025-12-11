'use client';

import Image from 'next/image';
import { useState, useEffect, useRef } from 'react';
import { getAvatarSources, getUserInitials, type AvatarUser } from '@/utils/avatar';

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
  const [sourceIndex, setSourceIndex] = useState(0);
  const [hasError, setHasError] = useState(false);
  const loadedRef = useRef(false);
  const [timerId, setTimerId] = useState<number | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  const maxRetriesPerSource = 2;

  const rawSources = getAvatarSources(user);
  const applyCache = (url: string) => {
    if (!url) return url;
    if (/^data:/.test(url)) return url;
    const version = cacheKey !== undefined && cacheKey !== null ? cacheKey : '0';
    return `${url}${url.includes('?') ? '&' : '?'}v=${version}-${retryNonce}`;
  };
  const sources = rawSources.map(applyCache);
  const finalAlt = alt || `${displayName || user.id || 'User'} avatar`;

  useEffect(() => {
    setSourceIndex(0);
    setHasError(false);
    loadedRef.current = false;
    setRetryNonce(0);
    setRetryCount(0);
    if (timerId) window.clearTimeout(timerId);
  }, [user?.id, user?.avatar_url, user?.avatar_id, cacheKey, timerId]);

  useEffect(() => {
    if (!sources[sourceIndex] || hasError) return;
    const timeoutMs = 7000;
    const t = window.setTimeout(() => {
      if (!loadedRef.current) handleImageError();
    }, timeoutMs);
    setTimerId(t as unknown as number);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceIndex, sources.join('|'), hasError, retryNonce]);

  useEffect(() => {
    setRetryCount(0);
  }, [sourceIndex]);

  const handleImageError = () => {
    const currentSrc = sources[sourceIndex] || '';
    const isS3 = currentSrc.includes('/api/users/avatar');
    if (isS3 && retryCount < maxRetriesPerSource) {
      setRetryCount((r) => r + 1);
      setRetryNonce((n) => n + 1); // cache-bust and retry same source
      loadedRef.current = false;
      return;
    }
    const nextIndex = sourceIndex + 1;
    if (nextIndex < sources.length) {
      setSourceIndex(nextIndex);
      loadedRef.current = false;
    } else {
      setHasError(true);
    }
  };

  const handleLoad = () => {
    loadedRef.current = true;
    if (timerId) window.clearTimeout(timerId);
  };

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

  const currentSrc = sources[sourceIndex] || '/assets/images/default_avatar.png';

  return (
    <Image
      src={currentSrc}
      alt={finalAlt}
      width={size}
      height={size}
      className={`rounded-full object-cover ${className}`}
      onError={handleImageError}
      onLoad={handleLoad}
      priority={size > 64}
      unoptimized
      loading={size > 64 ? undefined : 'lazy'}
    />
  );
}
