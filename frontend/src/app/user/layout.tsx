'use client';

import React, { useMemo } from 'react';
import { usePathname } from 'next/navigation';
import Layout from '@/components/common/Layout';
import { useAuthContext } from '@/context/AuthContext';

interface UserSectionLayoutProps {
  children: React.ReactNode;
}

export default function UserSectionLayout({ children }: UserSectionLayoutProps) {
  const pathname = usePathname();

  // Derive the title from the current path (fallback generic)
  const title = useMemo(() => {
    if (!pathname) return 'PathLight';
    if (pathname.startsWith('/user/my-courses')) return 'Khóa Học';
    if (pathname.startsWith('/user/my-quizzes')) return 'Quiz';
    if (pathname.startsWith('/user/dashboard')) return 'Trang Chủ';
    if (pathname.startsWith('/user/profile')) return 'Hồ Sơ';
    if (pathname.startsWith('/user/create-course')) return 'Tạo Khóa Học';
    if (pathname.startsWith('/user/create-quiz')) return 'Tạo Quiz';
    if (pathname.startsWith('/user/study-time-setup')) return 'Thiết Lập Thời Gian Học';
    if (pathname.startsWith('/user/generation-tracking')) return 'Theo Dõi Tiến Trình';
    return 'PathLight';
  }, [pathname]);

  const { user: authUser } = useAuthContext();
  const user = useMemo(() => {
    if (!authUser) return undefined;
    return {
      id: authUser.id,
      name: authUser.name,
      email: authUser.email,
      avatar_url: authUser.avatar_url,
      google_avatar_url: authUser.google_avatar_url,
      level: authUser.level,
      current_exp: authUser.current_exp,
      require_exp: authUser.require_exp,
      remind_time: authUser.remind_time,
      rank: authUser.rank,
    };
  }, [authUser]);

  return <Layout title={title} user={user}>{children}</Layout>;
}
