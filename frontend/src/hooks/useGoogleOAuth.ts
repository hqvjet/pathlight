'use client';

import { useEffect } from 'react';
import { AUTH_CONFIG, FEATURE_FLAGS } from '../config/env';

declare global {
  interface Window {
    google: any;
    googleSignInCallback: (response: any) => void;
  }
}

interface GoogleOAuthConfig {
  onSuccess: (credentialResponse: any) => void;
  onError?: () => void;
}

export const useGoogleOAuth = ({ onSuccess, onError }: GoogleOAuthConfig) => {
  useEffect(() => {
    // Check if Google Auth is enabled
    if (!FEATURE_FLAGS.ENABLE_GOOGLE_AUTH) {
      console.log('🔒 Google Auth is disabled via feature flag');
      return;
    }

    const handleCredentialResponse = (response: any) => {
      try {
        // Decode JWT token to get user info
        const base64Url = response.credential.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
          atob(base64)
            .split('')
            .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        );
        
        const userInfo = JSON.parse(jsonPayload);
        onSuccess({
          email: userInfo.email,
          google_id: userInfo.sub,
          given_name: userInfo.given_name,
          family_name: userInfo.family_name,
          avatar_id: userInfo.picture,
          credential: response.credential
        });
      } catch (error) {
        console.error('❌ Error parsing Google credential:', error);
        onError?.();
      }
    };

    const initializeGoogleSignIn = () => {
      const clientId = AUTH_CONFIG.GOOGLE_CLIENT_ID;
      
      console.log('🔧 Initializing Google Sign-In with Client ID:', clientId ? 'Set' : 'Not Set');
      
      if (!clientId) {
        console.warn('❌ Google Client ID not configured. Please set NEXT_PUBLIC_GOOGLE_CLIENT_ID in .env.local');
        return;
      }

      if (window.google) {
        console.log('✅ Google Sign-In API loaded successfully');
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true,
        });
        console.log('✅ Google Sign-In initialized');
      } else {
        console.error('❌ Google Sign-In API not loaded');
      }
    };

    // Load Google Sign-In script
    const loadGoogleScript = () => {
      if (document.getElementById('google-signin-script')) {
        console.log('🔄 Google script already exists, checking if loaded...');
        if (window.google) {
          initializeGoogleSignIn();
        }
        return;
      }

      console.log('📥 Loading Google Sign-In script...');
      const script = document.createElement('script');
      script.id = 'google-signin-script';
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        console.log('✅ Google script loaded successfully');
        initializeGoogleSignIn();
      };
      script.onerror = () => {
        console.error('❌ Failed to load Google Sign-In script');
      };
      document.head.appendChild(script);
    };

    loadGoogleScript();

    // Return cleanup function
    return () => {
      // Cleanup if needed
    };
  }, [onSuccess, onError]);

  const signIn = () => {
    if (!FEATURE_FLAGS.ENABLE_GOOGLE_AUTH) {
      console.log('� Google Auth is disabled');
      onError?.();
      return;
    }

    console.log('�🚀 Attempting Google Sign-In...');
    if (window.google) {
      console.log('✅ Google API available, showing prompt');
      window.google.accounts.id.prompt(); // Show One Tap dialog
    } else {
      console.error('❌ Google API not available');
      onError?.();
    }
  };

  const signInWithPopup = () => {
    if (!FEATURE_FLAGS.ENABLE_GOOGLE_AUTH) {
      console.log('� Google Auth is disabled');
      alert('Google OAuth hiện đang bị tắt. Vui lòng liên hệ quản trị viên.');
      return;
    }

    console.log('�🚀 Attempting Google Sign-In with popup...');
    
    const clientId = AUTH_CONFIG.GOOGLE_CLIENT_ID;
    if (!clientId) {
      console.error('❌ Google Client ID not configured');
      alert('Google OAuth chưa được cấu hình. Vui lòng thiết lập Client ID.');
      return;
    }

    if (!window.google) {
      console.error('❌ Google API not available');
      alert('Google Sign-In chưa sẵn sàng. Vui lòng đợi một chút và thử lại.');
      return;
    }

    console.log('✅ Google API available, showing prompt');
    window.google.accounts.id.prompt((notification: any) => {
      console.log('📋 Notification:', notification);
      if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
        console.log('ℹ️ One Tap not available');
        onError?.();
      }
    });
  };

  return { 
    signIn, 
    signInWithPopup,
    isEnabled: FEATURE_FLAGS.ENABLE_GOOGLE_AUTH,
    hasClientId: !!AUTH_CONFIG.GOOGLE_CLIENT_ID
  };
};
