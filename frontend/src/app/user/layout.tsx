'use client';

import React, { useMemo } from 'react';
import { usePathname } from 'next/navigation';
import Layout from '@/components/common/Layout';
import { useAuthContext } from '@/context/AuthContext';

// Root layout now injects a top NavBar; this layout focuses on sidebar + page framing.
// Simple title mapping based on current pathname. Extend if new pages are added.
const titleMap: Record<string, string> = {
  '/user/dashboard': 'Trang Chủ',
  '/user/my-courses': 'Khóa Học Của Tôi',
  '/user/my-quizzes': 'Quiz Của Tôi',
  '/user/profile': 'Hồ Sơ',
  '/user/create-course': 'Tạo Khóa Học',
  '/user/create-quiz': 'Tạo Quiz',
  '/user/study-time-setup': 'Thiết Lập Thời Gian Học',
};

interface UserSectionLayoutProps {
  children: React.ReactNode;
}

export default function UserSectionLayout({ children }: UserSectionLayoutProps) {
  const pathname = usePathname();

  // Lesson pages have their own complete layout (course outline sidebar)
  // so we bypass the user dashboard layout for them
  const isLessonPage = pathname.includes('/lessons/');
  
  if (isLessonPage) {
    return <>{children}</>;
  }

  // Derive the title from the current path (fallback generic)
  const title = titleMap[pathname] || 'PathLight';

  const { user: authUser } = useAuthContext();
  const user = useMemo(() => {
    if (!authUser) return undefined;
    return {
      name: authUser.name,
      email: authUser.email,
      avatar_url: authUser.avatar_url,
    };
  }, [authUser]);

  return <Layout title={title} user={user}>{children}</Layout>;
}
