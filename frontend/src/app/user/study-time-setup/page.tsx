'use client';

import { useRouter } from 'next/navigation';
import StudyTimeSetup from '@/components/user/StudyTimeSetup';
import { storage } from '@/utils/api';

export default function StudyTimeSetupPage() {
  const router = useRouter();

  const handleComplete = () => {
    // Mark setup as completed and redirect to dashboard
    storage.set('study_time_setup_completed', 'true');
    router.push('/user/dashboard');
  };

  const handleSkip = () => {
    // Mark setup as completed (skipped) and go to dashboard
    storage.set('study_time_setup_completed', 'true');
    router.push('/user/dashboard');
  };

  return (
    <StudyTimeSetup 
      onComplete={handleComplete}
      onSkip={handleSkip}
    />
  );
}
