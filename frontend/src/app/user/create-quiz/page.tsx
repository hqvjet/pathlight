'use client';

import { CreateQuizWizard } from '@/components/user/create-quiz/CreateQuizWizard';

export default function CreateQuizPage() {
  // TODO: Get user subscription tier from auth context
  // For now, defaulting to 'free'
  return <CreateQuizWizard userTier="free" />;
}
