"use client";
import { useEffect, useState } from 'react';
import { adminApi, AdminCourse } from '@/lib/api/admin';
import { showToast } from '@/utils/toast';
import Link from 'next/link';

export default function CoursesPageEnhanced() {
  const [courses, setCourses] = useState<AdminCourse[]>([]);
  const [filteredCourses, setFilteredCourses] = useState<AdminCourse[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterVisibility, setFilterVisibility] = useState<'all' | 'public' | 'private'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  const loadCourses = async () => {
    setLoading(true);
    try {
      const resp = await adminApi.listAllCourses({});
      if (resp?.data?.courses) {
        setCourses(resp.data.courses);
        setFilteredCourses(resp.data.courses);
      } else {
        showToast.error('Không thể tải danh sách khóa học');
      }
    } catch (error) {
      showToast.error('Lỗi khi tải danh sách khóa học');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCourses();
  }, []);

  useEffect(() => {
    let filtered = [...courses];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (c) =>
          c.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.overview?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Visibility filter
    if (filterVisibility !== 'all') {
      filtered = filtered.filter((c) => {
        if (filterVisibility === 'public') return c.publish === true;
        if (filterVisibility === 'private') return c.publish === false;
        return true;
      });
    }

    setFilteredCourses(filtered);
    setCurrentPage(1);
  }, [courses, searchTerm, filterVisibility]);

  const handleToggleVisibility = async (courseId: string, currentVisibility: boolean) => {
    try {
      const resp = await adminApi.toggleCourseVisibility(courseId, !currentVisibility);
      if (resp?.data?.status === 200) {
        showToast.success(`Đã ${currentVisibility ? 'ẩn' : 'công khai'} khóa học`);
        loadCourses();
      } else {
        showToast.error(resp?.data?.message || 'Thay đổi trạng thái thất bại');
      }
    } catch (error) {
      showToast.error('Lỗi khi thay đổi trạng thái khóa học');
    }
  };

  const handleDeleteCourse = async (courseId: string, name: string) => {
    if (!confirm(`Bạn có chắc muốn xóa khóa học "${name}"?`)) return;

    try {
      const resp = await adminApi.deleteCourse(courseId);
      if (resp?.data?.status === 200) {
        showToast.success('Đã xóa khóa học thành công');
        loadCourses();
      } else {
        showToast.error(resp?.data?.message || 'Xóa khóa học thất bại');
      }
    } catch (error) {
      showToast.error('Lỗi khi xóa khóa học');
    }
  };

  const stats = {
    total: courses.length,
    public: courses.filter((c) => c.publish === true).length,
    private: courses.filter((c) => c.publish === false).length,
    avgLessons:
      courses.length > 0
        ? courses.reduce((sum, c) => sum + (c.num_lessons || 0), 0) / courses.length
        : 0,
  };

  // Pagination
  const totalPages = Math.ceil(filteredCourses.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentCourses = filteredCourses.slice(startIndex, endIndex);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-4 text-white shadow-md">
          <p className="text-sm opacity-90">Total Courses</p>
          <p className="text-3xl font-bold">{stats.total}</p>
        </div>
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-4 text-white shadow-md">
          <p className="text-sm opacity-90">Public</p>
          <p className="text-3xl font-bold">{stats.public}</p>
        </div>
        <div className="bg-gradient-to-br from-gray-500 to-gray-600 rounded-lg p-4 text-white shadow-md">
          <p className="text-sm opacity-90">Private</p>
          <p className="text-3xl font-bold">{stats.private}</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-4 text-white shadow-md">
          <p className="text-sm opacity-90">Avg Lessons</p>
          <p className="text-3xl font-bold">{stats.avgLessons.toFixed(0)}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by title or overview..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Visibility</label>
            <select
              value={filterVisibility}
              onChange={(e) => setFilterVisibility(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              <option value="all">All</option>
              <option value="public">Public Only</option>
              <option value="private">Private Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results info */}
      <div className="flex justify-between items-center">
        <p className="text-sm text-gray-600">
          Showing <span className="font-semibold">{startIndex + 1}</span> to{' '}
          <span className="font-semibold">{Math.min(endIndex, filteredCourses.length)}</span> of{' '}
          <span className="font-semibold">{filteredCourses.length}</span> courses
        </p>
      </div>

      {/* Courses Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {currentCourses.map((course) => (
          <div
            key={course.course_id}
            className="bg-white rounded-lg shadow-md hover:shadow-xl transition-all border border-gray-200 overflow-hidden"
          >
            <div className="p-5">
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-bold text-gray-900 text-lg flex-1 line-clamp-2">{course.title}</h3>
                <span
                  className={`ml-2 px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap ${
                    course.publish ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {course.publish ? '🌐 Public' : '🔒 Private'}
                </span>
              </div>

              <p className="text-sm text-gray-600 mb-3 line-clamp-2 min-h-[40px]">
                {course.overview || 'No overview'}
              </p>

              <div className="flex items-center justify-between mb-4 text-sm text-gray-600">
                <span>📚 {course.num_lessons || 0} lessons</span>
                <span className="text-xs font-medium px-2 py-1 bg-blue-50 text-blue-700 rounded">
                  Level {course.level || 'N/A'}
                </span>
                <span className="text-xs font-mono truncate max-w-[120px]">
                  {course.course_id.substring(0, 8)}...
                </span>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleToggleVisibility(course.course_id, course.publish || false)}
                  className={`flex-1 px-3 py-2 text-sm rounded-md transition-colors ${
                    course.publish
                      ? 'bg-gray-600 text-white hover:bg-gray-700'
                      : 'bg-green-600 text-white hover:bg-green-700'
                  }`}
                >
                  {course.publish ? 'Hide' : 'Publish'}
                </button>
                <button
                  onClick={() => handleDeleteCourse(course.course_id, course.title)}
                  className="px-3 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredCourses.length === 0 && (
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <p className="text-gray-600">No courses found matching your filters.</p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          <div className="flex gap-1">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
              // Show first, last, current, and adjacent pages
              if (
                page === 1 ||
                page === totalPages ||
                (page >= currentPage - 1 && page <= currentPage + 1)
              ) {
                return (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`px-3 py-2 rounded-md ${
                      currentPage === page
                        ? 'bg-green-600 text-white'
                        : 'border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {page}
                  </button>
                );
              } else if (page === currentPage - 2 || page === currentPage + 2) {
                return <span key={page} className="px-2">...</span>;
              }
              return null;
            })}
          </div>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
