"use client";
import { useEffect, useState } from 'react';
import { adminApi, AdminQuiz } from '@/lib/api/admin';
import { showToast } from '@/utils/toast';

export default function AdminQuizzesPage() {
  const [quizzes, setQuizzes] = useState<AdminQuiz[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const limit = 20;

  const loadQuizzes = async () => {
    setLoading(true);
    try {
      const resp = await adminApi.listAllQuizzes({ page, limit, search: search || undefined });
      if (resp?.data?.quizzes) {
        setQuizzes(resp.data.quizzes);
        setTotal(resp.data.total || 0);
      } else {
        showToast.error('Không thể tải danh sách quiz');
      }
    } catch (error) {
      showToast.error('Lỗi khi tải danh sách quiz');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuizzes();
  }, [page]);

  const handleSearch = () => {
    setPage(1);
    loadQuizzes();
  };

  const handleToggleVisibility = async (quizId: string, currentPublish: boolean) => {
    try {
      const resp = await adminApi.toggleQuizVisibility(quizId, !currentPublish);
      if (resp?.data?.status === 200) {
        showToast.success(`Đã ${!currentPublish ? 'công khai' : 'ẩn'} quiz`);
        loadQuizzes();
      } else {
        showToast.error('Cập nhật thất bại');
      }
    } catch (error) {
      showToast.error('Lỗi khi cập nhật');
    }
  };

  const handleDelete = async (quizId: string, title: string) => {
    if (!confirm(`Bạn có chắc muốn xóa quiz "${title}"?`)) return;

    try {
      const resp = await adminApi.deleteQuiz(quizId);
      if (resp?.data?.status === 200) {
        showToast.success('Đã xóa quiz thành công');
        loadQuizzes();
      } else {
        showToast.error('Xóa quiz thất bại');
      }
    } catch (error) {
      showToast.error('Lỗi khi xóa quiz');
    }
  };

  const totalPages = Math.ceil(total / limit);

  if (loading && quizzes.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Quiz Management</h2>
        <p className="text-sm text-gray-600">Total: {total} quizzes</p>
      </div>

      {/* Search */}
      <div className="mb-6 flex gap-3">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search by title..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSearch}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Search
        </button>
      </div>

      {/* Quizzes Table */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Owner</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Level</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Questions</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {quizzes.map((quiz) => (
              <tr key={quiz.quiz_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                  {quiz.title}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                  {quiz.user_id.substring(0, 8)}...
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      quiz.creation_type === 'manual'
                        ? 'bg-purple-100 text-purple-800'
                        : 'bg-cyan-100 text-cyan-800'
                    }`}
                  >
                    {quiz.creation_type === 'manual' ? 'Manual' : 'AI Generated'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 capitalize">
                  {quiz.level}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {quiz.num_questions}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <div className="flex gap-2">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        quiz.publish
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {quiz.publish ? 'Public' : 'Private'}
                    </span>
                    {quiz.finish && (
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Finished
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(quiz.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => handleToggleVisibility(quiz.quiz_id, quiz.publish)}
                    className="text-blue-600 hover:text-blue-900 mr-4"
                  >
                    {quiz.publish ? 'Hide' : 'Show'}
                  </button>
                  <button
                    onClick={() => handleDelete(quiz.quiz_id, quiz.title)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-gray-600">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
