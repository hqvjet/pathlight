"use client";
import { useEffect, useMemo, useState } from 'react';
import { adminApi, CostItem } from '@/lib/api/admin';
import { showToast } from '@/utils/toast';

const formatVnd = (amount: number) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(amount);

const parseCostDate = (value: string) => {
  // Support dd/mm/YYYY (backend) and ISO/US fallbacks
  const parts = value.split('/');
  if (parts.length === 3) {
    const [dd, mm, yyyy] = parts;
    const isoLike = `${yyyy}-${mm}-${dd}`;
    const d = new Date(isoLike);
    if (Number.isFinite(d.getTime())) return d;
  }
  const fallback = new Date(value);
  return fallback;
};

export default function AdminCostsPage() {
  const [costs, setCosts] = useState<CostItem[]>([]);
  const [totalCost, setTotalCost] = useState(0);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');

  const loadCosts = async () => {
    setLoading(true);
    try {
      const resp = await adminApi.getCosts();
      if (resp?.data) {
        setCosts(resp.data.costs || []);
        setTotalCost(resp.data.total_cost || 0);
      } else {
        showToast.error('Không thể tải dữ liệu chi phí');
      }
    } catch (error) {
      showToast.error('Lỗi khi tải dữ liệu chi phí');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCosts();
  }, []);

  const sortedCosts = useMemo(() => {
    return [...costs].sort((a, b) => parseCostDate(a.date).getTime() - parseCostDate(b.date).getTime());
  }, [costs]);

  const filteredCosts = useMemo(() => {
    if (range === 'all') return sortedCosts;
    const now = new Date();
    const daysMap: Record<'7d' | '30d' | '90d' | 'all', number> = { '7d': 7, '30d': 30, '90d': 90, all: 0 };
    const cutoff = new Date(now.getTime() - daysMap[range] * 24 * 60 * 60 * 1000);
    return sortedCosts.filter((item) => parseCostDate(item.date).getTime() >= cutoff.getTime());
  }, [sortedCosts, range]);

  const costStats = useMemo(() => {
    if (filteredCosts.length === 0) return { avg: 0, max: 0, min: 0, trend: 0, trendPct: 0 };
    const values = filteredCosts.map((c) => c.cost);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const avg = values.reduce((sum, c) => sum + c, 0) / filteredCosts.length;

    const latest = values[values.length - 1];
    const prev = values.length > 1 ? values[values.length - 2] : 0;
    const trend = prev ? latest - prev : 0;
    const trendPct = prev ? (trend / prev) * 100 : 0;

    return { avg, max, min, trend, trendPct };
  }, [filteredCosts]);

  const rangeLabel: Record<typeof range, string> = {
    '7d': '7 ngày gần nhất',
    '30d': '30 ngày gần nhất',
    '90d': '90 ngày gần nhất',
    all: 'Toàn bộ dữ liệu',
  };

  const miniSparkData = filteredCosts.slice(-10);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm text-slate-500">Quan sát chi tiêu</p>
          <h2 className="text-2xl font-bold text-gray-900">Theo dõi chi phí AWS</h2>
          <p className="text-sm text-slate-500">Tổng hợp chi phí và xu hướng theo dải thời gian đã chọn</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={range}
            onChange={(e) => setRange(e.target.value as typeof range)}
            className="px-3 py-2 border border-slate-200 rounded-md text-sm shadow-sm"
          >
            <option value="7d">7 ngày gần nhất</option>
            <option value="30d">30 ngày gần nhất</option>
            <option value="90d">90 ngày gần nhất</option>
            <option value="all">Toàn bộ dữ liệu</option>
          </select>
          <button
            onClick={loadCosts}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Làm mới
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white shadow-lg">
          <p className="text-sm text-white/90">Tổng chi phí AWS</p>
          <p className="text-4xl font-bold mt-1">{formatVnd(totalCost)}</p>
          <p className="text-xs mt-2 text-white/80">Tính trên dữ liệu đã tải</p>
          <p className="text-[11px] text-white/75 mt-1">Cửa sổ: {rangeLabel[range]}</p>
        </div>
        <StatCard title="Trung bình/ngày" value={formatVnd(costStats.avg)} subtitle="Theo cửa sổ chọn" tone="slate" sparkData={miniSparkData} />
        <StatCard title="Cao nhất/ngày" value={formatVnd(costStats.max)} subtitle="Đỉnh trong cửa sổ" tone="amber" sparkData={miniSparkData} />
        <StatCard
          title={costStats.trend >= 0 ? 'Tăng so với hôm trước' : 'Giảm so với hôm trước'}
          value={`${costStats.trend >= 0 ? '+' : ''}${formatVnd(Math.abs(costStats.trend))}`}
          subtitle={costStats.trendPct ? `${costStats.trendPct >= 0 ? '+' : ''}${costStats.trendPct.toFixed(1)}%` : 'Không có dữ liệu trước đó'}
          tone={costStats.trend >= 0 ? 'amber' : 'slate'}
          sparkData={miniSparkData}
        />
      </div>

      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-bold text-gray-900">Phân bổ chi phí theo ngày</h3>
            <p className="text-sm text-slate-500">Biểu đồ đường + thanh để nhìn nhanh biến động mỗi ngày</p>
          </div>
          <div className="text-right text-xs text-slate-500">
            <p>Cửa sổ: {rangeLabel[range]}</p>
            <p>Số ngày có dữ liệu: {filteredCosts.length}</p>
          </div>
        </div>
        {filteredCosts.length > 0 ? (
          <>
            <LineChart data={filteredCosts} />
            <div className="space-y-3 mt-4">
              {filteredCosts.map((item, index) => {
                const maxCost = Math.max(...filteredCosts.map((c) => c.cost));
                const barWidth = maxCost > 0 ? (item.cost / maxCost) * 100 : 0;
                const parsed = parseCostDate(item.date);
                const label = Number.isFinite(parsed.getTime())
                  ? parsed.toLocaleDateString('vi-VN', { month: 'short', day: 'numeric' })
                  : item.date;

                return (
                  <div key={index} className="flex items-center gap-4">
                    <div className="w-28 text-sm text-gray-600 flex-shrink-0">{label}</div>
                    <div className="flex-1 bg-gray-100 rounded-full h-8 relative overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-blue-400 to-blue-600 h-full rounded-full transition-all duration-300"
                        style={{ width: `${barWidth}%` }}
                      ></div>
                    </div>
                    <div className="w-28 text-right text-sm font-medium text-gray-900 flex-shrink-0">
                      {formatVnd(item.cost)}
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        ) : (
          <p className="text-gray-500 text-center py-8">Chưa có dữ liệu chi phí trong cửa sổ này</p>
        )}
      </div>

      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ngày
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Chi phí (VND)
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {costs.map((item, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {(() => {
                    const d = parseCostDate(item.date);
                    return Number.isFinite(d.getTime())
                      ? d.toLocaleDateString('vi-VN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
                      : item.date;
                  })()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-right">
                  <span className="text-slate-900">{formatVnd(item.cost)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {costs.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 text-sm">
            <strong>Lưu ý:</strong> Chưa có dữ liệu chi phí từ AWS Cost Explorer. Vui lòng kiểm tra cấu hình dịch vụ.
          </p>
        </div>
      )}
    </div>
  );
}

type StatCardProps = {
  title: string;
  value: string;
  subtitle?: string;
  tone: 'slate' | 'amber';
  sparkData?: CostItem[];
};

function StatCard({ title, value, subtitle, tone, sparkData = [] }: StatCardProps) {
  const toneMap: Record<StatCardProps['tone'], string> = {
    slate: 'bg-slate-50 text-slate-900 border-slate-200',
    amber: 'bg-amber-50 text-amber-800 border-amber-200',
  };

  const sparkPoints = sparkData.map((d) => d.cost);
  const sparkMax = Math.max(...sparkPoints, 1);
  const sparkMin = Math.min(...sparkPoints, 0);
  const sparkRange = Math.max(sparkMax - sparkMin, 1);

  return (
    <div className={`rounded-lg p-5 border ${toneMap[tone]} shadow-sm`}>
      <p className="text-sm font-medium">{title}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
      {subtitle && <p className="text-xs text-slate-600 mt-1">{subtitle}</p>}
      {sparkData.length > 1 && (
        <div className="mt-3">
          <MiniSparkline values={sparkPoints} rangeLabel="" />
        </div>
      )}
    </div>
  );
}

function LineChart({ data }: { data: CostItem[] }) {
  const width = 720;
  const height = 200;
  const pad = 30;
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
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-56">
        <defs>
          <linearGradient id="costGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </linearGradient>
        </defs>
        {points.length > 0 && (
          <>
            <polyline
              fill="url(#costGradient)"
              stroke="none"
              points={`${points.join(' ')} ${pad + (data.length - 1) * step},${height - pad} ${pad},${height - pad}`}
            />
            <polyline
              fill="none"
              stroke="#2563eb"
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
    </div>
  );
}

function MiniSparkline({ values, rangeLabel }: { values: number[]; rangeLabel?: string }) {
  if (values.length === 0) return null;
  const width = 120;
  const height = 36;
  const pad = 4;
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = Math.max(max - min, 1);
  const step = values.length > 1 ? (width - pad * 2) / (values.length - 1) : 0;
  const points = values.map((v, idx) => {
    const x = pad + idx * step;
    const y = height - pad - ((v - min) / range) * (height - pad * 2);
    return `${x},${y}`;
  });

  return (
    <div className="flex items-center justify-between gap-2">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-10">
        <polyline
          fill="none"
          stroke="#2563eb"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points.join(' ')}
        />
        {points.map((pt, idx) => {
          const [x, y] = pt.split(',').map(Number);
          return <circle key={idx} cx={x} cy={y} r={2.5} fill="#2563eb" />;
        })}
      </svg>
      {rangeLabel && <span className="text-[10px] text-slate-500">{rangeLabel}</span>}
    </div>
  );
}
