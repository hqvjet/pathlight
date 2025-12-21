"use client";
import { usePathname } from 'next/navigation';
import { AuthProvider } from '@/context/AuthContext';

export function ConditionalAuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  
  // Don't use AuthProvider for admin routes
  if (pathname?.startsWith('/admin')) {
    return <>{children}</>;
  }
  
  // Use AuthProvider for all other routes
  return <AuthProvider>{children}</AuthProvider>;
}
