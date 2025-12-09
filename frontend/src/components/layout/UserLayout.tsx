'use client';

import { ReactNode } from 'react';
import NavBarAuth from './NavBarAuth';

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
      <NavBarAuth
        user={user}
        onLogout={onLogout}
        showLogoutButton={showNavLogout}
      />
      <main className="pt-32 py-8">
        {children}
      </main>
    </div>
  );
}
