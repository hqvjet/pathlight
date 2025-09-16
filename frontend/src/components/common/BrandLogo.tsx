"use client";

import Image from 'next/image';
import Link from 'next/link';
import { useState } from 'react';

interface BrandLogoProps {
  href?: string;
  size?: number; // base size (height/width)
  showText?: boolean;
  className?: string;
  priority?: boolean;
}

// Central brand logo with graceful fallback if image missing
export function BrandLogo({ href = '/', size = 40, showText = true, className = '', priority }: BrandLogoProps) {
  const [errored, setErrored] = useState(false);
  const content = (
    <div className={`flex items-center gap-2 group ${className}`}>
      {!errored ? (
        <Image
          src="/assets/icons/logo.png"
          alt="PathLight Logo"
          width={size}
          height={size}
          priority={priority}
          onError={() => setErrored(true)}
          className="object-contain w-9 h-9 sm:w-10 sm:h-10 transition-transform group-hover:scale-105"
        />
      ) : (
        <div className="w-9 h-9 sm:w-10 sm:h-10 flex items-center justify-center rounded bg-gradient-to-br from-orange-500 to-rose-500 text-white font-bold text-sm">PL</div>
      )}
      {showText && (
        <span className="text-lg sm:text-xl lg:text-2xl font-bold bg-gradient-to-r from-orange-600 to-rose-500 bg-clip-text text-transparent tracking-tight">
          PathLight
        </span>
      )}
    </div>
  );
  if (!href) return content;
  return (
    <Link href={href} className="focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500/60 rounded-sm">
      {content}
    </Link>
  );
}

export default BrandLogo;
