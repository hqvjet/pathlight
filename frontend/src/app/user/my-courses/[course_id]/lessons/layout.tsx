import React from 'react';

// This layout bypasses the parent user layout to avoid double navbar
// Lesson pages have their own complete layout with sidebar
export default function LessonLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
