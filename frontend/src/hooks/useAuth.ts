// Deprecated legacy hook kept for backward compatibility.
// New code should import state from '@/context/AuthContext' via useAuthContext().
// This shim maps to the new context so existing imports don't immediately break.
'use client';
import { useAuthContext } from '@/context/AuthContext';

export const useAuth = () => {
  const { isAuthenticated, isRemembered, loading, logout } = useAuthContext();
  return { isAuthenticated, isRemembered, loading, logout };
};
