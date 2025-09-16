'use client';

import React, { useMemo } from 'react';
import { usePathname } from 'next/navigation';
import Layout from '@/components/common/Layout';

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

  // Derive the title from the current path (fallback generic)
  const title = titleMap[pathname] || 'PathLight';

  // TODO: Replace with real user fetching logic (hook or context) once available.
  const user = useMemo(
    () => ({
      name: 'Nguyễn Văn A',
      email: 'user@example.com',
      avatar_url: '',
    }),
    []
  );

  return <Layout title={title} user={user}>{children}</Layout>;
}
