"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import GenerationList, { GenerationItem } from "@/components/user/generation/GenerationList";
import { courseApi } from "@/lib/api/course";
import { showToast } from "@/utils/toast";
import { RefreshCw, TrendingUp } from "lucide-react";

export default function GenerationTrackingPage() {
  const [items, setItems] = useState<GenerationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(6);

  const loadData = async () => {
    setLoading(true);
    try {
      const resp = await courseApi.listMyGenerations();
      if (resp.status === 200 && Array.isArray(resp.data?.items)) {
        const mapped = (resp.data.items as unknown as Array<Record<string, unknown>>).map((r) => ({
          course_id: String(r.course_id ?? ""),
          user_id: r.user_id ? String(r.user_id) : undefined,
          progress: r.progress ? String(r.progress) : undefined,
          title_ready: Boolean(r.title_ready),
          lessons_ready: Boolean(r.lessons_ready),
          final_ready: Boolean(r.final_ready),
          vectorized: Boolean(r.vectorized),
          updated_at: r.updated_at ? String(r.updated_at) : undefined,
        })) as GenerationItem[];
        
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
  };

  useEffect(() => {
    loadData();
  }, []);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    // Scroll to top when page changes
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1); // Reset to first page when changing items per page
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-orange-500" />
            <span className="text-sm font-medium text-orange-600 uppercase tracking-wide">
              Course Generation
            </span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Theo dõi tiến trình</h1>
          <p className="text-gray-600 max-w-2xl">
            Theo dõi chi tiết quá trình tạo khóa học tự động của bạn. 
            Nhấp vào từng khóa học để xem thông tin chi tiết.
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
          <Link href="/user/my-courses">
            <Button variant="outline" className="border-gray-200">
              Khóa học của tôi
            </Button>
          </Link>
          <Link href="/user/create-course">
            <Button className="bg-orange-500 hover:bg-orange-600">
              Tạo khóa học mới
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <Card className="border-gray-100 overflow-hidden">
        <GenerationList
          items={items}
          loading={loading}
          currentPage={currentPage}
          itemsPerPage={itemsPerPage}
          onPageChange={handlePageChange}
          onItemsPerPageChange={handleItemsPerPageChange}
        />
      </Card>
    </div>
  );
}
