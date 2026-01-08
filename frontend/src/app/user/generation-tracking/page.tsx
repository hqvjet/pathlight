"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function GenerationTrackingPage() {
  const router = useRouter();
  
  useEffect(() => {
    router.replace('/user/tracking?tab=courses');
  }, [router]);
  
  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-gray-600">Đang chuyển hướng...</p>
    </div>
  );
}

