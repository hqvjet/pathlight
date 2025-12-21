"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { RefreshCw, TrendingUp } from "lucide-react";
import { showToast } from "@/utils/toast";
import { quizApi } from "@/lib/api/quiz";
import QuizGenerationList from "@/components/user/quiz-generation/QuizGenerationList";

export interface QuizGenerationItem {
  quiz_id: string;
  user_id?: string;
  progress?: string;
  title_ready?: boolean;
  cards_ready?: boolean;
  final_ready?: boolean;
  updated_at?: string;
}

export default function QuizTrackingPage() {
  const [items, setItems] = useState<QuizGenerationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(6);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await quizApi.listMyGenerations();
      if (resp.status === 200 && Array.isArray(resp.data?.items)) {
        const mapped = (resp.data.items as unknown as Array<Record<string, unknown>>).map((r) => ({
          quiz_id: String(r.quiz_id ?? ""),
          user_id: r.user_id ? String(r.user_id) : undefined,
          progress: r.progress ? String(r.progress) : undefined,
          title_ready: Boolean(r.title_ready),
          cards_ready: Boolean(r.cards_ready),
          final_ready: Boolean(r.final_ready),
          vectorized: Boolean(r.vectorized),
          updated_at: r.updated_at ? String(r.updated_at) : undefined,
        })) as QuizGenerationItem[];
        
        // Sort by updated_at descending (newest first)
        mapped.sort((a, b) => {
          if (!a.updated_at) return 1;
          if (!b.updated_at) return -1;
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        });
        
        setItems(mapped);
      } else if (resp.status === 401) {
        showToast.error("Bạn cần đăng nhập để xem tiến trình.");
      } else {
        showToast.error("Không thể tải dữ liệu tiến trình.");
      }
    } catch {
      showToast.error("Có lỗi xảy ra khi tải dữ liệu.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-green-500" />
            <span className="text-sm font-medium text-green-600 uppercase tracking-wide">
              Quiz Generation
            </span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Theo dõi tiến trình tạo Quiz</h1>
          <p className="text-gray-600 max-w-2xl">
            Theo dõi chi tiết quá trình AI tạo quiz tự động của bạn. 
            Nhấp vào từng quiz để xem thông tin chi tiết.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Button 
            variant="outline" 
            onClick={loadData} 
            disabled={loading}
            className="border-gray-200"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Làm mới
          </Button>
          <Link href="/user/my-quizzes">
            <Button variant="outline" className="border-gray-200">
              Quiz của tôi
            </Button>
          </Link>
          <Link href="/user/create-quiz">
            <Button className="bg-green-500 hover:bg-green-600">
              Tạo Quiz mới
            </Button>
          </Link>
        </div>
      </div>

      {/* Generation List */}
      <QuizGenerationList
        items={items}
        loading={loading}
        currentPage={currentPage}
        itemsPerPage={itemsPerPage}
        onPageChange={handlePageChange}
        onItemsPerPageChange={handleItemsPerPageChange}
      />
    </div>
  );
}
