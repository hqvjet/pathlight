'use client';

import { useEffect, useState } from 'react';
import { storage } from '@/utils/api';
import { showToast } from '@/utils/toast';

export const CookieWarning = () => {
  const [showWarning, setShowWarning] = useState(false);

  useEffect(() => {
    // Check if cookies are enabled
    if (typeof window !== 'undefined') {
      const cookiesEnabled = storage.isCookieEnabled?.();
      
      if (!cookiesEnabled) {
        setShowWarning(true);
        showToast.error(
          'Cookies bị vô hiệu hóa. Vui lòng bật cookies để sử dụng đầy đủ tính năng của ứng dụng.',
          {
            autoClose: false,
            closeOnClick: false,
          }
        );
      }
    }
  }, []);

  if (!showWarning) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-red-600 text-white p-4">
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center">
          <div className="mr-3">
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h3 className="font-semibold">Cookies bị vô hiệu hóa</h3>
            <p className="text-sm">
              Ứng dụng này cần cookies để hoạt động. Vui lòng bật cookies trong trình duyệt của bạn.
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowWarning(false)}
          className="ml-4 text-white hover:text-gray-200"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default CookieWarning;
