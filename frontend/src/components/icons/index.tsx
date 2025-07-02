import React from 'react';

interface IconProps {
  className?: string;
  size?: number;
}

export const HomeIcon = ({ className = '', size = 20 }: IconProps) => (
  <svg width={size} height={size} className={className} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    <polyline strokeLinecap="round" strokeLinejoin="round" points="9,22 9,12 15,12 15,22" />
  </svg>
);

export const BookOpenIcon = ({ className = '', size = 20 }: IconProps) => (
  <svg width={size} height={size} className={className} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="m22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
  </svg>
);

export const ClipboardListIcon = ({ className = '', size = 20 }: IconProps) => (
  <svg width={size} height={size} className={className} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <rect strokeLinecap="round" strokeLinejoin="round" x="8" y="2" width="8" height="4" rx="1" ry="1" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
    <path strokeLinecap="round" strokeLinejoin="round" d="m9 14 2 2 4-4" />
  </svg>
);

export const UserCircleIcon = ({ className = '', size = 20 }: IconProps) => (
  <svg width={size} height={size} className={className} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle strokeLinecap="round" strokeLinejoin="round" cx="12" cy="7" r="4" />
  </svg>
);

export const LogoutIcon = ({ className = '', size = 20 }: IconProps) => (
  <svg width={size} height={size} className={className} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline strokeLinecap="round" strokeLinejoin="round" points="16,17 21,12 16,7" />
    <line strokeLinecap="round" strokeLinejoin="round" x1="21" y1="12" x2="9" y2="12" />
  </svg>
);

export const PlusCircleIcon = ({ className = '', size = 20 }: IconProps) => (
  <svg width={size} height={size} className={className} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <circle strokeLinecap="round" strokeLinejoin="round" cx="12" cy="12" r="10" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v8" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h8" />
  </svg>
);

export const DocumentTextIcon = ({ className = '', size = 20 }: IconProps) => (
  <svg width={size} height={size} className={className} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline strokeLinecap="round" strokeLinejoin="round" points="14,2 14,8 20,8" />
    <line strokeLinecap="round" strokeLinejoin="round" x1="16" y1="13" x2="8" y2="13" />
    <line strokeLinecap="round" strokeLinejoin="round" x1="16" y1="17" x2="8" y2="17" />
    <polyline strokeLinecap="round" strokeLinejoin="round" points="10,9 9,9 8,9" />
  </svg>
);

export const MenuIcon = ({ className = '', size = 20 }: IconProps) => (
  <svg width={size} height={size} className={className} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <line strokeLinecap="round" strokeLinejoin="round" x1="4" y1="6" x2="20" y2="6" />
    <line strokeLinecap="round" strokeLinejoin="round" x1="4" y1="12" x2="20" y2="12" />
    <line strokeLinecap="round" strokeLinejoin="round" x1="4" y1="18" x2="20" y2="18" />
  </svg>
);

export const ChevronLeftIcon = ({ className = '', size = 20 }: IconProps) => (
  <svg width={size} height={size} className={className} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <polyline strokeLinecap="round" strokeLinejoin="round" points="15,18 9,12 15,6" />
  </svg>
);
