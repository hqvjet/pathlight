'use client';

import { useParams, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Trophy, ArrowLeft } from 'lucide-react';

export default function FinalTestPage() {
  const params = useParams();
  const router = useRouter();
  const courseId = params.course_id as string;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-10 py-8 space-y-6">
        <Button
          variant="outline"
          onClick={() => router.push(`/user/my-courses/${courseId}`)}
          className="hover:bg-white"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Quay lại khóa học
        </Button>

        <Card className="p-12 text-center bg-white shadow-lg border-0">
          <div className="w-20 h-20 bg-gradient-to-br from-purple-400 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-6">
            <Trophy className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Bài Kiểm Tra Cuối Khóa
          </h1>
          <p className="text-gray-600 mb-8 max-w-md mx-auto">
            Trang bài test cuối khóa đang được phát triển. Hoàn thành để nhận chứng chỉ.
          </p>
          <Button 
            onClick={() => router.push(`/user/my-courses/${courseId}`)}
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
          >
            Quay lại khóa học
          </Button>
        </Card>
      </div>
    </div>
  );
}
