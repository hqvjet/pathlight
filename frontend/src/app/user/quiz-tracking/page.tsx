"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function QuizTrackingPage() {
  const router = useRouter();
  
  useEffect(() => {
    router.replace('/user/tracking?tab=quizzes');
  }, [router]);
  
  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-gray-600">Đang chuyển hướng...</p>
    </div>
  );
}
