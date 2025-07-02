'use client';

import { ReactNode } from 'react';
import NavBar from './NavBar';

interface UserLayoutProps {
  children: ReactNode;
  user: {
    name: string;
    avatar_url?: string;
  };
  onLogout: () => void;
  showNavLogout?: boolean;
}

export default function UserLayout({ 
  children, 
  user, 
  onLogout, 
  showNavLogout = true 
}: UserLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar 
        user={user} 
        onLogout={onLogout} 
        showLogoutButton={showNavLogout}
      />
      <main className="py-8">
        {children}
      </main>
    </div>
  );
}
