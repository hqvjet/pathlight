"use client";
import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { adminApi, AdminUser } from '@/lib/api/admin';
import { showToast } from '@/utils/toast';

type DashboardStats = {
  totalUsers: number;
  totalCourses: number;
  totalQuizzes: number;
  activeTodayUsers: number;
  newUsersThisWeek: number;
  totalCost: number;
  avgUserLevel: number;
  premiumUsers: number;
  publicContent: number;
  recentErrors: number;
};

type ChartData = {
  date: string;
  users: number;
  courses: number;
  quizzes: number;
};

type CostData = {
  date: string;
  cost: number;
};

type AdminAccount = {
  id: string;
  username: string;
  created_at?: string;
};

const parseCostDate = (value: string) => {
  const parts = value.split('/');
  if (parts.length === 3) {
    const [dd, mm, yyyy] = parts;
    const isoLike = `${yyyy}-${mm}-${dd}`;
    const d = new Date(isoLike);
    if (Number.isFinite(d.getTime())) return d;
  }
  return new Date(value);
};

const formatVnd = (amount: number) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(amount);

export default function AdminDashboard() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [admins, setAdmins] = useState<AdminAccount[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalUsers: 0,
    totalCourses: 0,
    totalQuizzes: 0,
    activeTodayUsers: 0,
    newUsersThisWeek: 0,
    totalCost: 0,
    avgUserLevel: 0,
    premiumUsers: 0,
    publicContent: 0,
    recentErrors: 0,
  });
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [costSeries, setCostSeries] = useState<CostData[]>([]);
  const [loading, setLoading] = useState(true);
  const [adminForm, setAdminForm] = useState({ username: '', password: '', submitting: false });

  const activityCostSeries = (() => {
    const len = Math.min(chartData.length, costSeries.length);
    if (len === 0) return [] as { label: string; activity: number; cost: number }[];
    return Array.from({ length: len }).map((_, idx) => {
      const activity = chartData[idx]?.users ?? 0;
      const cost = costSeries[idx]?.cost ?? 0;
      const label = chartData[idx]?.date ?? costSeries[idx]?.date ?? `${idx + 1}`;
      return { label, activity, cost };
    });
  })();

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const [usersRes, coursesRes, quizzesRes, costsRes, logsRes, adminsRes] = await Promise.allSettled([
        adminApi.listUsers(),
        adminApi.listAllCourses({ page: 1, limit: 1000 }),
        adminApi.listAllQuizzes({ page: 1, limit: 1000 }),
        adminApi.getCosts(),
        adminApi.getLogs('weekly'),
        adminApi.listAdmins(),
      ]);

      const safe = function <T>(res: PromiseSettledResult<T>, fallback: T): T {
        return res.status === 'fulfilled' ? res.value : fallback;
      };

      const usersResp = safe(usersRes, { data: { status: 200, users: [] } } as Awaited<ReturnType<typeof adminApi.listUsers>>);
      const coursesResp = safe(coursesRes, { data: { status: 200, courses: [] } } as Awaited<ReturnType<typeof adminApi.listAllCourses>>);
      const quizzesResp = safe(quizzesRes, { data: { status: 200, quizzes: [] } } as Awaited<ReturnType<typeof adminApi.listAllQuizzes>>);
      const costsResp = safe(costsRes, { data: { status: 200, total_cost: 0, costs: [] } } as Awaited<ReturnType<typeof adminApi.getCosts>>);
      const logsResp = safe(logsRes, { data: { status: 200, logs: [] } } as Awaited<ReturnType<typeof adminApi.getLogs>>);
      const adminsResp = safe(adminsRes, { data: { status: 200, admins: [] } } as Awaited<ReturnType<typeof adminApi.listAdmins>>);

      const users = usersResp.data?.users ?? [];
      const courses = coursesResp.data?.courses ?? [];
      const quizzes = quizzesResp.data?.quizzes ?? [];
      const logs = logsResp.data?.logs ?? [];
      const totalCost = costsResp.data?.total_cost ?? 0;
      const costs = costsResp.data?.costs ?? [];
      const adminList = adminsResp.data?.admins ?? [];

      const avgLevel = users.length
        ? users.reduce((sum, user) => sum + (user.level ?? 0), 0) / users.length
        : 0;
      const premiumCount = users.filter((u) => (u.subscription ?? 0) > 0).length;
      const publicCourses = courses.filter((c) => c.publish).length;
      const publicQuizzes = quizzes.filter((q) => q.publish).length;
      const errorLogs = logs.filter((l) => l.type?.toLowerCase().includes('error')).length;

      setUsers(users);
      setAdmins(adminList);

      setStats({
        totalUsers: users.length,
        totalCourses: courses.length,
        totalQuizzes: quizzes.length,
        activeTodayUsers: Math.floor(users.length * 0.3),
        newUsersThisWeek: Math.floor(users.length * 0.1),
        totalCost,
        avgUserLevel: avgLevel,
        premiumUsers: premiumCount,
        publicContent: publicCourses + publicQuizzes,
        recentErrors: errorLogs,
      });

      const orderedCosts = costs
        .map((c) => ({ ...c, date: c.date }))
        .sort((a, b) => parseCostDate(a.date).getTime() - parseCostDate(b.date).getTime());
      setCostSeries(orderedCosts.slice(-10));

      const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
      const maxUsersLen = Math.max(users.length, 1);
      const mockData = days.map((day, idx) => ({
        date: day,
        users: 50 + idx * 7 + (maxUsersLen % 10),
        courses: 15 + idx * 3 + (courses.length % 8),
        quizzes: 20 + idx * 4 + (quizzes.length % 6),
      }));
      setChartData(mockData);

      const anyRejected = [usersRes, coursesRes, quizzesRes, costsRes, logsRes, adminsRes].some((r) => r.status === 'rejected');
      if (anyRejected) {
        // showToast.error('Một số dữ liệu không tải được, vui lòng kiểm tra lại API');
      }
    } catch (error) {
      console.error('Failed to load dashboard', error);
      showToast.error('Không thể tải dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleCreateAdmin = async () => {
    const { username, password } = adminForm;
    if (!username.trim() || !password.trim()) {
      showToast.error('Vui lòng nhập đủ username/password');
      return;
    }
    try {
      setAdminForm((prev) => ({ ...prev, submitting: true }));
      const resp = await adminApi.createAdmin(username.trim(), password.trim());
      if (resp?.data?.status === 200) {
        showToast.success(resp.data.message || 'Đã tạo admin mới');
        setAdminForm({ username: '', password: '', submitting: false });
      } else {
        showToast.error(resp?.data?.message || 'Tạo admin thất bại');
        setAdminForm((prev) => ({ ...prev, submitting: false }));
      }
    } catch (error) {
      console.error('Create admin failed', error);
      showToast.error('Không thể tạo admin');
      setAdminForm((prev) => ({ ...prev, submitting: false }));
    }
  };

  const handleDeleteUser = async (userId: string) => {
    try {
      const confirmed = typeof window === 'undefined' ? true : confirm('Xoá người dùng này?');
      if (!confirmed) return;
      const resp = await adminApi.deleteUser(userId);
      if (resp?.data?.status === 200) {
        showToast.success('Đã xoá user');
        loadDashboard();
      } else {
        showToast.error(resp?.data?.message || 'Xoá user thất bại');
      }
    } catch (error) {
      console.error('Delete user failed', error);
      showToast.error('Không thể xoá user');
    }
  };

  const handlePromotePremium = (userId: string) => {
    const input = typeof window === 'undefined' ? '1' : prompt('Nhập gói (0=Free,1=Premium,2=Pro)', '1');
    if (input === null) return;
    const subscription = Number.parseInt(input, 10);
    if (![0, 1, 2].includes(subscription)) {
      showToast.error('Giá trị gói không hợp lệ');
      return;
    }
    adminApi
      .updateUserSubscription(userId, subscription)
      .then((resp) => {
        if (resp?.data?.status === 200) {
          showToast.success('Đã cập nhật gói người dùng');
          loadDashboard();
        } else {
          showToast.error(resp?.data?.message || 'Không thể cập nhật gói');
        }
      })
      .catch((error) => {
        console.error('Update subscription failed', error);
        showToast.error('Lỗi khi cập nhật gói');
      });
  };

  const handleAddExperience = (userId: string) => {
    const input = typeof window === 'undefined' ? '100' : prompt('Thêm bao nhiêu exp?', '100');
    if (input === null) return;
    const exp = Number.parseInt(input, 10);
    if (!Number.isFinite(exp) || exp <= 0) {
      showToast.error('Exp phải > 0');
      return;
    }
    adminApi
      .addUserExperience(userId, exp)
      .then((resp) => {
        if (resp?.data?.status === 200) {
          showToast.success(resp.data.message || 'Đã thêm exp');
          loadDashboard();
        } else {
          showToast.error(resp?.data?.message || 'Không thể thêm exp');
        }
      })
      .catch((error) => {
        console.error('Add exp failed', error);
        showToast.error('Lỗi khi thêm exp');
      });
  };

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const percent = (value: number, total: number) => {
    if (total <= 0) return 0;
    return Math.round((value / total) * 100);
  };

  const totalContent = stats.totalCourses + stats.totalQuizzes;

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500">Tổng quan hệ thống</p>
          <h1 className="text-3xl font-bold text-slate-900">Bảng điều hành</h1>
        </div>
        <button
          onClick={loadDashboard}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 shadow-sm"
        >
          <span>🔄</span>
          <span>Làm mới</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard title="Người dùng" value={stats.totalUsers.toLocaleString()} subtitle="Đang quản lý" color="text-blue-500" />
            <StatCard title="Khoá học" value={stats.totalCourses.toLocaleString()} subtitle="Trong hệ thống" color="text-emerald-500" />
            <StatCard title="Bài kiểm tra" value={stats.totalQuizzes.toLocaleString()} subtitle="Đang xuất bản" color="text-purple-500" />
            <StatCard title="Chi phí Cloud" value={formatVnd(stats.totalCost)} subtitle="Ước tính AWS" color="text-amber-500" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <GaugeCard label="Hoạt động hôm nay" value={stats.activeTodayUsers} max={Math.max(stats.totalUsers, 1)} color="blue" />
        <GaugeCard label="Người mới trong tuần" value={stats.newUsersThisWeek} max={Math.max(stats.totalUsers, 1)} color="amber" />
        <GaugeCard label="Người dùng premium" value={stats.premiumUsers} max={Math.max(stats.totalUsers, 1)} color="purple" />
        <GaugeCard label="Lỗi gần đây" value={stats.recentErrors} max={20} color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-3">Tạo admin mới</h3>
          <div className="space-y-3">
            <div>
              <label className="text-sm text-slate-600">Username</label>
              <input
                className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                value={adminForm.username}
                onChange={(e) => setAdminForm((prev) => ({ ...prev, username: e.target.value }))}
                placeholder="admin_name"
              />
            </div>
            <div>
              <label className="text-sm text-slate-600">Password</label>
              <input
                type="password"
                className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                value={adminForm.password}
                onChange={(e) => setAdminForm((prev) => ({ ...prev, password: e.target.value }))}
                placeholder="••••••••"
              />
            </div>
            <button
              onClick={handleCreateAdmin}
              disabled={adminForm.submitting}
              className="w-full px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 disabled:opacity-60"
            >
              {adminForm.submitting ? 'Đang tạo...' : 'Tạo admin'}
            </button>
            <p className="text-xs text-slate-500">Yêu cầu token admin hiện tại để gọi API.</p>
          </div>

          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold text-slate-800">Admins hiện có</h4>
              <span className="text-xs text-slate-500">{admins.length}</span>
            </div>
            {admins.length ? (
              <div className="divide-y divide-slate-200 max-h-64 overflow-y-auto">
                {admins.slice(0, 8).map((a) => (
                  <div key={a.id} className="py-2 flex items-center justify-between">
                    <div className="text-sm text-slate-800 truncate">{a.username}</div>
                    <div className="text-[11px] text-slate-500">{a.created_at ? new Date(a.created_at).toLocaleDateString() : ''}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">Chưa có dữ liệu admin.</p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-slate-900">Người dùng (top 5)</h3>
            <span className="text-xs text-slate-500">Tổng: {users.length}</span>
          </div>
          {users.length ? (
            <div className="divide-y divide-slate-200">
              {users
                .slice()
                .sort((a, b) => (b.level || 0) - (a.level || 0))
                .slice(0, 5)
                .map((u) => (
                  <div key={u.user_id} className="py-3 flex items-center justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-slate-900 truncate">{u.email || 'Không email'}</p>
                      <p className="text-xs text-slate-500">Level {u.level ?? '-'} · ID {u.user_id.slice(0, 8)}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button onClick={() => handlePromotePremium(u.user_id)} className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs hover:bg-slate-50">
                        Premium
                      </button>
                      <button onClick={() => handleAddExperience(u.user_id)} className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs hover:bg-slate-50">
                        +Exp
                      </button>
                      <button onClick={() => handleDeleteUser(u.user_id)} className="px-3 py-1.5 rounded-lg border border-rose-200 text-xs text-rose-600 hover:bg-rose-50">
                        Xoá
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">Chưa tải được danh sách người dùng.</p>
          )}
          <p className="text-[11px] text-slate-500 mt-2">Nâng cấp premium / thêm exp cần API backend mới.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Hoạt động theo tuần</h3>
              <p className="text-sm text-slate-500">Người dùng / Khoá học / Bài kiểm tra</p>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-500">
              <LegendDot color="bg-blue-500" label="Người dùng" />
              <LegendDot color="bg-emerald-500" label="Khoá học" />
              <LegendDot color="bg-purple-500" label="Bài kiểm tra" />
            </div>
          </div>
          <div className="grid grid-cols-7 gap-3 items-end h-64">
            {chartData.map((item) => {
              const max = Math.max(...chartData.map((d) => Math.max(d.users, d.courses, d.quizzes)), 1);
              return (
                <div key={item.date} className="flex flex-col items-center gap-2">
                  <div className="w-full rounded-lg bg-slate-100 p-2 flex flex-col justify-end gap-1 h-48">
                    <div
                      className="w-full rounded-md bg-blue-500"
                      style={{ height: `${(item.users / max) * 100}%` }}
                      title={`Users ${item.users}`}
                    />
                    <div
                      className="w-full rounded-md bg-emerald-500"
                      style={{ height: `${(item.courses / max) * 100}%` }}
                      title={`Courses ${item.courses}`}
                    />
                    <div
                      className="w-full rounded-md bg-purple-500"
                      style={{ height: `${(item.quizzes / max) * 100}%` }}
                      title={`Quizzes ${item.quizzes}`}
                    />
                  </div>
                  <span className="text-xs font-medium text-slate-600">{item.date}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Cơ cấu nội dung</h3>
              <p className="text-sm text-slate-500">Công khai / Premium / Đang hoạt động</p>
            </div>
            <span className="text-2xl">📊</span>
          </div>
          <StackedBar label="Nội dung công khai" primary={stats.publicContent} secondary={Math.max(totalContent - stats.publicContent, 0)} color="blue" />
          <StackedBar label="Người dùng premium" primary={stats.premiumUsers} secondary={Math.max(stats.totalUsers - stats.premiumUsers, 0)} color="purple" />
          <StackedBar label="Đang hoạt động" primary={stats.activeTodayUsers} secondary={Math.max(stats.totalUsers - stats.activeTodayUsers, 0)} color="emerald" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Xu hướng chi phí</h3>
              <p className="text-sm text-slate-500">Chi phí AWS gần đây so với mức hoạt động</p>
            </div>
            <div className="text-right text-sm text-slate-600">
              <p>Chi phí / người dùng hoạt động</p>
              <p className="text-xl font-bold text-slate-900">{formatVnd(stats.totalCost / Math.max(stats.activeTodayUsers || 1, 1))}</p>
            </div>
          </div>
          <CostMiniChart data={costSeries} />
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Tổng quan vận hành</h3>
              <p className="text-sm text-slate-500">Ghép chi phí với hoạt động người dùng</p>
            </div>
            <span className="text-2xl">📈</span>
          </div>
            <div className="grid grid-cols-2 gap-4">
              <MiniStat
                label="Avg cost (recent)"
                value={formatVnd(costSeries.reduce((s, c) => s + c.cost, 0) / Math.max(costSeries.length, 1))}
              />
              <MiniStat label="Max cost (recent)" value={formatVnd(Math.max(...costSeries.map((c) => c.cost), 0))} />
              <MiniStat label="Active today" value={stats.activeTodayUsers.toLocaleString()} />
              <MiniStat label="Premium users" value={stats.premiumUsers.toLocaleString()} />
            </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Hoạt động vs Chi phí</h3>
              <p className="text-sm text-slate-500">So sánh hình dạng giữa người dùng hoạt động và chi phí</p>
            </div>
            <span className="text-2xl">📊</span>
          </div>
          <ActivityCostChart data={activityCostSeries} />
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Dải lỗi gần đây</h3>
              <p className="text-sm text-slate-500">Đếm lỗi trong cửa sổ log vừa tải</p>
            </div>
            <span className="text-2xl">🚦</span>
          </div>
          <ErrorMiniChart count={stats.recentErrors} />
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-md border border-gray-200">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Lối tắt quản trị</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <Link href="/admin/users" className="flex flex-col items-center gap-2 p-4 rounded-lg border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-all group">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
              👥
            </div>
            <span className="text-sm font-medium text-gray-700 group-hover:text-blue-600">Quản lý người dùng</span>
          </Link>

          <Link href="/admin/courses" className="flex flex-col items-center gap-2 p-4 rounded-lg border-2 border-gray-200 hover:border-green-500 hover:bg-green-50 transition-all group">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
              📚
            </div>
            <span className="text-sm font-medium text-gray-700 group-hover:text-green-600">Quản lý khoá học</span>
          </Link>

          <Link href="/admin/quizzes" className="flex flex-col items-center gap-2 p-4 rounded-lg border-2 border-gray-200 hover:border-purple-500 hover:bg-purple-50 transition-all group">
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
              📝
            </div>
            <span className="text-sm font-medium text-gray-700 group-hover:text-purple-600">Quản lý bài kiểm tra</span>
          </Link>

          <Link href="/admin/costs" className="flex flex-col items-center gap-2 p-4 rounded-lg border-2 border-gray-200 hover:border-orange-500 hover:bg-orange-50 transition-all group">
            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
              💰
            </div>
            <span className="text-sm font-medium text-gray-700 group-hover:text-orange-600">Xem chi phí</span>
          </Link>

          <Link href="/admin/log" className="flex flex-col items-center gap-2 p-4 rounded-lg border-2 border-gray-200 hover:border-red-500 hover:bg-red-50 transition-all group">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
              📋
            </div>
            <span className="text-sm font-medium text-gray-700 group-hover:text-red-600">Xem log</span>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-md border border-gray-200">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Sức khỏe hệ thống</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">API</span>
              <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">✓ Hoạt động</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Cơ sở dữ liệu</span>
              <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">✓ Ổn định</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Lưu trữ</span>
              <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">✓ Sẵn sàng</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Tỉ lệ lỗi</span>
              <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
                {stats.recentErrors > 5 ? '⚠ Cần theo dõi' : '✓ Thấp'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-md border border-gray-200">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Phân bổ nội dung</h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Nội dung công khai</span>
                <span className="font-medium">{percent(stats.publicContent, totalContent)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${percent(stats.publicContent, totalContent)}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Người dùng premium</span>
                <span className="font-medium">{percent(stats.premiumUsers, stats.totalUsers)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-yellow-500 h-2 rounded-full" style={{ width: `${percent(stats.premiumUsers, stats.totalUsers)}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Người dùng hoạt động hôm nay</span>
                <span className="font-medium">{percent(stats.activeTodayUsers, stats.totalUsers)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: `${percent(stats.activeTodayUsers, stats.totalUsers)}%` }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

type StatCardProps = {
  title: string;
  value: string;
  subtitle?: string;
  color: string;
};

function StatCard({ title, value, subtitle, color }: StatCardProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-600">{title}</p>
          <p className="text-3xl font-bold mt-1 text-slate-900">{value}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        <span className={`text-xl ${color}`}>●</span>
      </div>
    </div>
  );
}

type GaugeCardProps = {
  label: string;
  value: number;
  max: number;
  color: 'blue' | 'amber' | 'purple' | 'red';
};

function GaugeCard({ label, value, max, color }: GaugeCardProps) {
  const ratio = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  const colorMap: Record<GaugeCardProps['color'], string> = {
    blue: 'from-blue-500 to-blue-600',
    amber: 'from-amber-500 to-amber-600',
    purple: 'from-purple-500 to-purple-600',
    red: 'from-rose-500 to-rose-600',
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-sm text-slate-600">{label}</p>
          <p className="text-2xl font-bold text-slate-900">{value.toLocaleString()}</p>
        </div>
        <span className="text-lg">🎯</span>
      </div>
      <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full bg-gradient-to-r ${colorMap[color]}`} style={{ width: `${ratio}%` }}></div>
      </div>
      <p className="text-xs text-slate-500 mt-2">{ratio.toFixed(0)}% mục tiêu</p>
    </div>
  );
}

type LegendDotProps = {
  color: string;
  label: string;
};

function LegendDot({ color, label }: LegendDotProps) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className={`w-3 h-3 rounded-full ${color}`}></span>
      <span>{label}</span>
    </span>
  );
}

type StackedBarProps = {
  label: string;
  primary: number;
  secondary: number;
  color: 'blue' | 'purple' | 'emerald';
};

function StackedBar({ label, primary, secondary, color }: StackedBarProps) {
  const total = Math.max(primary + secondary, 1);
  const primaryPercent = (primary / total) * 100;
  const secondaryPercent = (secondary / total) * 100;
  const colorMap: Record<StackedBarProps['color'], string> = {
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    emerald: 'bg-emerald-500',
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-600">{label}</span>
        <span className="text-slate-900 font-medium">{primary.toLocaleString()}</span>
      </div>
      <div className="w-full h-3 rounded-full bg-slate-100 overflow-hidden flex">
        <div className={`${colorMap[color]} h-full`} style={{ width: `${primaryPercent}%` }}></div>
        <div className="bg-slate-300 h-full" style={{ width: `${secondaryPercent}%` }}></div>
      </div>
      <div className="flex justify-between text-xs text-slate-500">
        <span>Chính</span>
        <span>Phụ</span>
      </div>
    </div>
  );
}

function CostMiniChart({ data }: { data: CostData[] }) {
  if (!data.length) {
    return <p className="text-sm text-slate-500">No cost data</p>;
  }

  const width = 520;
  const height = 180;
  const pad = 24;
  const maxCost = Math.max(...data.map((d) => d.cost), 1);
  const minCost = Math.min(...data.map((d) => d.cost), 0);
  const range = Math.max(maxCost - minCost, 1);
  const step = data.length > 1 ? (width - pad * 2) / (data.length - 1) : 0;
  const points = data.map((d, idx) => {
    const x = pad + idx * step;
    const y = height - pad - ((d.cost - minCost) / range) * (height - pad * 2);
    return `${x},${y}`;
  });

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-44">
        {points.length > 0 && (
          <>
            <polyline
              fill="none"
              stroke="#3b82f6"
              strokeWidth={3}
              strokeLinejoin="round"
              strokeLinecap="round"
              points={points.join(' ')}
            />
            {points.map((pt, idx) => {
              const [x, y] = pt.split(',').map(Number);
              return <circle key={idx} cx={x} cy={y} r={4} fill="#2563eb" />;
            })}
          </>
        )}
        <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="#e2e8f0" />
      </svg>
      <div className="flex justify-between text-[11px] text-slate-500 mt-1">
        {data.map((d, idx) => {
          const parsed = parseCostDate(d.date);
          const label = Number.isFinite(parsed.getTime()) ? parsed.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : d.date;
          return <span key={idx}>{label}</span>;
        })}
      </div>
    </div>
  );
}

function ActivityCostChart({ data }: { data: { label: string; activity: number; cost: number }[] }) {
  if (!data.length) return <p className="text-sm text-slate-500">Chưa có dữ liệu so sánh</p>;

  const width = 520;
  const height = 200;
  const pad = 28;
  const maxActivity = Math.max(...data.map((d) => d.activity), 1);
  const maxCost = Math.max(...data.map((d) => d.cost), 1);
  const step = data.length > 1 ? (width - pad * 2) / (data.length - 1) : 0;

  const buildPoints = (values: number[], maxVal: number) =>
    values.map((v, idx) => {
      const x = pad + idx * step;
      const y = height - pad - (v / maxVal) * (height - pad * 2);
      return `${x},${y}`;
    });

  const activityPoints = buildPoints(data.map((d) => d.activity), maxActivity);
  const costPoints = buildPoints(data.map((d) => d.cost), maxCost);

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-52">
        <polyline
          fill="none"
          stroke="#2563eb"
          strokeWidth={3}
          strokeLinecap="round"
          strokeLinejoin="round"
          points={activityPoints.join(' ')}
        />
        <polyline
          fill="none"
          stroke="#f97316"
          strokeWidth={3}
          strokeLinecap="round"
          strokeLinejoin="round"
          points={costPoints.join(' ')}
        />
        {activityPoints.map((pt, idx) => {
          const [x, y] = pt.split(',').map(Number);
          return <circle key={`a-${idx}`} cx={x} cy={y} r={4} fill="#2563eb" />;
        })}
        {costPoints.map((pt, idx) => {
          const [x, y] = pt.split(',').map(Number);
          return <circle key={`c-${idx}`} cx={x} cy={y} r={4} fill="#f97316" />;
        })}
        <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="#e2e8f0" />
      </svg>
      <div className="flex justify-between text-[11px] text-slate-500 mt-1">
        {data.map((d, idx) => (
          <span key={idx}>{d.label}</span>
        ))}
      </div>
      <div className="flex items-center gap-4 text-xs text-slate-600 mt-2">
        <LegendDot color="bg-blue-500" label="Hoạt động" />
        <LegendDot color="bg-orange-500" label="Chi phí" />
      </div>
    </div>
  );
}

function ErrorMiniChart({ count }: { count: number }) {
  const capped = Math.min(count, 20);
  const ratio = Math.min((capped / 20) * 100, 100);
  const tone = ratio > 60 ? 'bg-red-500' : ratio > 30 ? 'bg-amber-500' : 'bg-emerald-500';

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm text-slate-700">
        <span>Lỗi phát hiện</span>
        <span className="font-semibold">{count}</span>
      </div>
      <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full ${tone}`} style={{ width: `${ratio}%` }}></div>
      </div>
      <p className="text-xs text-slate-500">Giới hạn hiển thị: 20 log lỗi gần đây</p>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 p-3 bg-slate-50">
      <p className="text-xs text-slate-600">{label}</p>
      <p className="text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}
