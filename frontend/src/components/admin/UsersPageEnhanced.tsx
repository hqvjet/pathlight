"use client";
import { useEffect, useState } from 'react';
import { adminApi, AdminUser } from '@/lib/api/admin';
import { showToast } from '@/utils/toast';

export default function AdminUsersPageEnhanced() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingUser, setEditingUser] = useState<{ userId: string; email: string } | null>(null);
  const [newEmail, setNewEmail] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSub, setFilterSub] = useState<'all' | 'free' | 'premium' | 'pro'>('all');
  const [sortBy, setSortBy] = useState<'level' | 'exp' | 'email'>('level');

  const loadUsers = async () => {
    setLoading(true);
    try {
      const resp = await adminApi.listUsers();
      if (resp?.data?.users) {
        setUsers(resp.data.users);
        setFilteredUsers(resp.data.users);
      } else {
        showToast.error('Không thể tải danh sách người dùng');
      }
    } catch {
      showToast.error('Lỗi khi tải danh sách người dùng');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  useEffect(() => {
    let filtered = [...users];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (u) =>
          u.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          u.given_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          u.family_name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Subscription filter
    if (filterSub !== 'all') {
      filtered = filtered.filter((u) => {
        if (filterSub === 'free') return !u.subscription || u.subscription === 0;
        if (filterSub === 'premium') return u.subscription === 1;
        if (filterSub === 'pro') return u.subscription === 2;
        return true;
      });
    }

    // Sort
    filtered.sort((a, b) => {
      if (sortBy === 'level') return (b.level || 0) - (a.level || 0);
      if (sortBy === 'exp') return (b.current_exp || 0) - (a.current_exp || 0);
      if (sortBy === 'email') return (a.email || '').localeCompare(b.email || '');
      return 0;
    });

    setFilteredUsers(filtered);
  }, [users, searchTerm, filterSub, sortBy]);

  const handleUpdateEmail = async () => {
    if (!editingUser || !newEmail.trim()) {
      showToast.error('Email không hợp lệ');
      return;
    }

    try {
      const resp = await adminApi.updateUserEmail(editingUser.userId, newEmail);
      if (resp?.data?.status === 200) {
        showToast.success('Đã cập nhật email thành công');
        setEditingUser(null);
        setNewEmail('');
        loadUsers();
      } else {
        showToast.error(resp?.data?.message || 'Cập nhật email thất bại');
      }
    } catch {
      showToast.error('Lỗi khi cập nhật email');
    }
  };

  const handleDeleteUser = async (userId: string, email: string) => {
    if (!confirm(`Bạn có chắc muốn xóa người dùng ${email}?`)) return;

    try {
      const resp = await adminApi.deleteUser(userId);
      if (resp?.data?.status === 200) {
        showToast.success('Đã xóa người dùng thành công');
        loadUsers();
      } else {
        showToast.error(resp?.data?.message || 'Xóa người dùng thất bại');
      }
    } catch {
      showToast.error('Lỗi khi xóa người dùng');
    }
  };

  const stats = {
    total: users.length,
    free: users.filter((u) => !u.subscription || u.subscription === 0).length,
    premium: users.filter((u) => u.subscription === 1).length,
    pro: users.filter((u) => u.subscription === 2).length,
    avgLevel: users.length > 0 ? users.reduce((sum, u) => sum + (u.level || 1), 0) / users.length : 0,
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-4 text-white shadow-md">
          <p className="text-sm opacity-90">Total Users</p>
          <p className="text-3xl font-bold">{stats.total}</p>
        </div>
        <div className="bg-gradient-to-br from-gray-500 to-gray-600 rounded-lg p-4 text-white shadow-md">
          <p className="text-sm opacity-90">Free</p>
          <p className="text-3xl font-bold">{stats.free}</p>
        </div>
        <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-lg p-4 text-white shadow-md">
          <p className="text-sm opacity-90">Premium</p>
          <p className="text-3xl font-bold">{stats.premium}</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-4 text-white shadow-md">
          <p className="text-sm opacity-90">Pro</p>
          <p className="text-3xl font-bold">{stats.pro}</p>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-4 text-white shadow-md">
          <p className="text-sm opacity-90">Avg Level</p>
          <p className="text-3xl font-bold">{stats.avgLevel.toFixed(1)}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name or email..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Subscription</label>
            <select
              value={filterSub}
              onChange={(e) => setFilterSub(e.target.value as 'all' | 'free' | 'premium' | 'pro')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All</option>
              <option value="free">Free</option>
              <option value="premium">Premium</option>
              <option value="pro">Pro</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'level' | 'exp' | 'email')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="level">Level (High to Low)</option>
              <option value="exp">Experience (High to Low)</option>
              <option value="email">Email (A-Z)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results count */}
      <div className="flex justify-between items-center">
        <p className="text-sm text-gray-600">
          Showing <span className="font-semibold">{filteredUsers.length}</span> of{' '}
          <span className="font-semibold">{users.length}</span> users
        </p>
      </div>

      {/* Users Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredUsers.map((user) => (
          <div
            key={user.user_id}
            className="bg-white rounded-lg shadow-md p-5 hover:shadow-lg transition-shadow border border-gray-200"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <h3 className="font-bold text-gray-900 text-lg">
                  {user.given_name || user.family_name
                    ? `${user.given_name || ''} ${user.family_name || ''}`.trim()
                    : 'Unknown User'}
                </h3>
                <p className="text-sm text-gray-600 truncate">{user.email || 'No email'}</p>
              </div>
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium ${
                  user.subscription === 1
                    ? 'bg-yellow-100 text-yellow-800'
                    : user.subscription === 2
                    ? 'bg-purple-100 text-purple-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {user.subscription === 1 ? 'Premium' : user.subscription === 2 ? 'Pro' : 'Free'}
              </span>
            </div>

            <div className="space-y-2 mb-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Level</span>
                <span className="font-semibold text-blue-600">{user.level || 1}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Experience</span>
                <span className="font-semibold text-green-600">{user.current_exp || 0} XP</span>
              </div>
              <div className="text-xs text-gray-500 font-mono">ID: {user.user_id.substring(0, 12)}...</div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => {
                  setEditingUser({ userId: user.user_id, email: user.email || '' });
                  setNewEmail(user.email || '');
                }}
                className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
              >
                Edit
              </button>
              <button
                onClick={() => handleDeleteUser(user.user_id, user.email || '')}
                className="flex-1 px-3 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredUsers.length === 0 && (
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <p className="text-gray-600">No users found matching your filters.</p>
        </div>
      )}

      {/* Edit Email Modal */}
      {editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">Edit User Email</h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Current Email</label>
              <p className="text-sm text-gray-600">{editingUser.email}</p>
            </div>
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">New Email</label>
              <input
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter new email"
              />
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setEditingUser(null);
                  setNewEmail('');
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateEmail}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Update
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
