"use client";
import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, LayoutGrid, List } from "lucide-react";
import QuizGenerationCard from "./QuizGenerationCard";
import QuizGenerationDetailModal from "./QuizGenerationDetailModal";
import { userApi } from "@/lib/api/user";

export interface QuizGenerationItem {
  quiz_id: string;
  user_id?: string;
  status?: string;
  progress_percentage?: number;
  current_step?: string;
  current_step_detail?: string;
  plan_ready?: boolean;
  questions_ready?: boolean;
  title?: string;
  overview?: string;
  ideas_count?: number;
  questions_count?: number;
  start_timestamp?: string;
  end_timestamp?: string;
  updated_at?: string;
  // Legacy field names for backward compatibility
  title_ready?: boolean;
  cards_ready?: boolean;
  final_ready?: boolean;
}

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  itemsPerPage: number;
  onItemsPerPageChange: (items: number) => void;
  totalItems: number;
}

function Pagination({ 
  currentPage, 
  totalPages, 
  onPageChange, 
  itemsPerPage, 
  onItemsPerPageChange,
  totalItems 
}: PaginationProps) {
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-gray-100">
      <div className="flex items-center gap-4 text-sm text-gray-600">
        <span>Hiển thị {startItem}-{endItem} của {totalItems} mục</span>
        <div className="flex items-center gap-2">
          <span>Số mục/trang:</span>
          <select
            value={itemsPerPage}
            onChange={(e) => onItemsPerPageChange(Number(e.target.value))}
            className="border border-gray-200 rounded px-2 py-1 text-sm"
          >
            <option value={6}>6</option>
            <option value={12}>12</option>
            <option value={24}>24</option>
          </select>
        </div>
      </div>
      
      {totalPages > 1 && (
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            let pageNum;
            if (totalPages <= 5) {
              pageNum = i + 1;
            } else if (currentPage <= 3) {
              pageNum = i + 1;
            } else if (currentPage >= totalPages - 2) {
              pageNum = totalPages - 4 + i;
            } else {
              pageNum = currentPage - 2 + i;
            }
            
            return (
              <Button
                key={pageNum}
                variant={currentPage === pageNum ? "default" : "outline"}
                size="sm"
                onClick={() => onPageChange(pageNum)}
                className={currentPage === pageNum ? "bg-green-500 hover:bg-green-600" : ""}
              >
                {pageNum}
              </Button>
            );
          })}
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

export default function QuizGenerationList({ 
  items, 
  loading,
  currentPage = 1,
  itemsPerPage = 6,
  onPageChange,
  onItemsPerPageChange,
}: { 
  items: QuizGenerationItem[]; 
  loading?: boolean;
  currentPage?: number;
  itemsPerPage?: number;
  onPageChange?: (page: number) => void;
  onItemsPerPageChange?: (items: number) => void;
}) {
  const [selectedItem, setSelectedItem] = useState<QuizGenerationItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [userNames, setUserNames] = useState<Record<string, string>>({});

  // Fetch user names when items change
  useEffect(() => {
    const fetchUserNames = async () => {
      const userIds = [...new Set(items.map(item => item.user_id).filter(Boolean))] as string[];
      if (userIds.length === 0) return;
      
      try {
        const response = await userApi.batchUsers(userIds);
        if (response.status === 200 && response.data) {
          const names: Record<string, string> = {};
          // Response.data is an object, not an array
          Object.values(response.data).forEach((user: unknown) => {
            const userRecord = user as Record<string, unknown>;
            if (userRecord.id) {
              names[userRecord.id as string] = (userRecord.name || userRecord.email || userRecord.id) as string;
            }
          });
          setUserNames(names);
        }
      } catch (error) {
        console.error('Failed to fetch user names:', error);
      }
    };

    fetchUserNames();
  }, [items]);

  const handleItemClick = (item: QuizGenerationItem) => {
    setSelectedItem(item);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedItem(null);
  };

  if (loading) {
    return (
      <Card className="p-12 text-center border-gray-100">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto"></div>
        <p className="mt-4 text-gray-600 font-medium">Đang tải tiến trình tạo quiz...</p>
        <p className="text-sm text-gray-500 mt-1">Vui lòng chờ trong giây lát</p>
      </Card>
    );
  }

  if (!items || items.length === 0) {
    return (
      <Card className="p-12 text-center border-dashed border-gray-300">
        <LayoutGrid className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-600 mb-2">Chưa có dữ liệu tiến trình</h3>
        <p className="text-gray-500 mb-4">Bạn chưa tạo quiz bằng AI hoặc chưa có dữ liệu theo dõi.</p>
        <Button variant="outline" className="border-green-200 text-green-600 hover:bg-green-50">
          Tạo quiz đầu tiên
        </Button>
      </Card>
    );
  }

  const totalPages = Math.ceil(items.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = items.slice(startIndex, endIndex);

  return (
    <div className="space-y-6">
      {/* View Mode Toggle */}
      <div className="flex items-center justify-end gap-2 px-6">
        <span className="text-sm text-gray-600 font-medium">Hiển thị:</span>
        <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'list'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
            title="Danh sách"
          >
            <List className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'grid'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
            title="Lưới"
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* List or Grid */}
      <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 p-6' : 'space-y-4 p-6'}>
        {currentItems.map((item) => (
          <QuizGenerationCard
            key={item.quiz_id}
            item={item}
            onClick={() => handleItemClick(item)}
            userNames={userNames}
          />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && onPageChange && onItemsPerPageChange && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={onPageChange}
          itemsPerPage={itemsPerPage}
          onItemsPerPageChange={onItemsPerPageChange}
          totalItems={items.length}
        />
      )}

      {/* Detail Modal */}
      {selectedItem && (
        <QuizGenerationDetailModal
          item={selectedItem}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
}
