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

type RangeKey = '7d' | '30d' | '90d' | 'all';
type ViewKey = 'daily' | 'weekly' | 'monthly';

export default function AdminCostsPage() {
  const [costs, setCosts] = useState<CostItem[]>([]);
  const [totalCost, setTotalCost] = useState(0);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState<RangeKey>('30d');
  const [view, setView] = useState<ViewKey>('daily');
  const [tableYear, setTableYear] = useState<string>('all');
  const [tableMonth, setTableMonth] = useState<string>('all');

  const ranges: { key: RangeKey; label: string }[] = [
    { key: '7d', label: '7 ngày' },
    { key: '30d', label: '30 ngày' },
    { key: '90d', label: '90 ngày' },
    { key: 'all', label: 'Tất cả' },
  ];

  const viewTabs: { key: ViewKey; label: string }[] = [
    { key: 'daily', label: 'Ngày' },
    { key: 'weekly', label: 'Tuần' },
    { key: 'monthly', label: 'Tháng' },
  ];

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
    } catch {
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
    const daysMap: Record<RangeKey, number> = { '7d': 7, '30d': 30, '90d': 90, all: 0 };
    const cutoff = new Date(now.getTime() - daysMap[range] * 24 * 60 * 60 * 1000);
    return sortedCosts.filter((item) => parseCostDate(item.date).getTime() >= cutoff.getTime());
  }, [sortedCosts, range]);

  const costStats = useMemo(() => {
    if (filteredCosts.length === 0) {
      return { avg: 0, max: 0, min: 0, median: 0, stddev: 0, trend: 0, trendPct: 0 };
    }
    const values = filteredCosts.map((c) => c.cost);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const avg = values.reduce((sum, c) => sum + c, 0) / filteredCosts.length;

    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    const median = sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;

    const variance = values.reduce((sum, v) => sum + Math.pow(v - avg, 2), 0) / values.length;
    const stddev = Math.sqrt(variance);

    const latest = values[values.length - 1];
    const prev = values.length > 1 ? values[values.length - 2] : 0;
    const trend = prev ? latest - prev : 0;
    const trendPct = prev ? (trend / prev) * 100 : 0;

    return { avg, max, min, median, stddev, trend, trendPct };
  }, [filteredCosts]);

  const viewAggregated = useMemo(() => {
    const bucketMap: Record<ViewKey, (d: Date) => string> = {
      daily: (d) => d.toLocaleDateString('vi-VN', { month: 'short', day: 'numeric' }),
      weekly: (d) => {
        const onejan = new Date(d.getFullYear(), 0, 1);
        const week = Math.ceil(((d.getTime() - onejan.getTime()) / 86400000 + onejan.getDay() + 1) / 7);
        return `Tuần ${week} ${d.getFullYear()}`;
      },
      monthly: (d) => d.toLocaleDateString('vi-VN', { month: 'short', year: 'numeric' }),
    };

    const grouped: Record<string, { total: number; count: number }> = {};
    filteredCosts.forEach((item) => {
      const dateObj = parseCostDate(item.date);
      const key = bucketMap[view](dateObj);
      grouped[key] = grouped[key] || { total: 0, count: 0 };
      grouped[key].total += item.cost;
      grouped[key].count += 1;
    });

    return Object.entries(grouped)
      .map(([label, stats]) => ({ label, total: stats.total, avg: stats.total / stats.count }))
      .sort((a, b) => b.total - a.total || a.label.localeCompare(b.label));
  }, [filteredCosts, view]);

  const rangeLabel: Record<RangeKey, string> = {
    '7d': '7 ngày gần nhất',
    '30d': '30 ngày gần nhất',
    '90d': '90 ngày gần nhất',
    all: 'Toàn bộ dữ liệu',
  };

  const tableFilteredCosts = useMemo(() => {
    return costs.filter((item) => {
      const d = parseCostDate(item.date);
      const yearOk = tableYear === 'all' || d.getFullYear().toString() === tableYear;
      const monthOk = tableMonth === 'all' || (d.getMonth() + 1).toString() === tableMonth;
      return yearOk && monthOk;
    });
  }, [costs, tableMonth, tableYear]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 bg-white">
      <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm text-slate-600">Quan sát chi tiêu</p>
            <h2 className="text-3xl font-bold text-slate-900">AWS Cost Pulse</h2>
            <p className="text-sm text-slate-600">Theo dõi chi phí, biến động và phân bổ theo thời gian</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-100 rounded-full px-2 py-1">
              {ranges.map((r) => (
                <button
                  key={r.key}
                  onClick={() => setRange(r.key)}
                  className={`px-3 py-1 text-sm rounded-full transition border ${
                    range === r.key ? 'bg-slate-900 text-white border-slate-900' : 'text-slate-800 border-slate-200 hover:border-slate-400'
                  }`}
                >
                  {r.label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 bg-slate-100 rounded-full px-2 py-1">
              {viewTabs.map((v) => (
                <button
                  key={v.key}
                  onClick={() => setView(v.key)}
                  className={`px-3 py-1 text-sm rounded-full transition border ${
                    view === v.key ? 'bg-slate-900 text-white border-slate-900' : 'text-slate-800 border-slate-200 hover:border-slate-400'
                  }`}
                >
                  {v.label}
                </button>
              ))}
            </div>
            <button
              onClick={loadCosts}
              className="px-4 py-2 bg-slate-900 text-white rounded-full text-sm font-semibold shadow hover:bg-slate-800"
            >
              Làm mới
            </button>
          </div>
        </div>
        <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <HeroStat label="Tổng chi phí" value={formatVnd(totalCost)} hint={`Cửa sổ: ${rangeLabel[range]}`} />
          <HeroStat label="Trung bình" value={formatVnd(costStats.avg)} hint="Trung bình cửa sổ" />
          <HeroStat label="Median" value={formatVnd(costStats.median)} hint="Trung vị cửa sổ" />
          <HeroStat
            label={costStats.trend >= 0 ? 'Tăng so với kỳ trước' : 'Giảm so với kỳ trước'}
            value={`${costStats.trend >= 0 ? '+' : ''}${formatVnd(Math.abs(costStats.trend))}`}
            hint={costStats.trendPct ? `${costStats.trendPct >= 0 ? '+' : ''}${costStats.trendPct.toFixed(1)}%` : 'Không có dữ liệu trước đó'}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="bg-white shadow-md rounded-xl p-6 xl:col-span-2 border border-slate-100">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-bold text-gray-900">Chi phí theo thời gian</h3>
              <p className="text-sm text-slate-500">Đường xu hướng + diện tích cho cửa sổ đã chọn</p>
            </div>
            <div className="text-right text-xs text-slate-500">
              <p>Cửa sổ: {rangeLabel[range]}</p>
              <p>{filteredCosts.length} điểm dữ liệu</p>
            </div>
          </div>
          {filteredCosts.length > 0 ? <LineChart data={filteredCosts} /> : <p className="text-gray-500 text-center py-8">Chưa có dữ liệu</p>}
        </div>

        <div className="bg-white shadow-md rounded-xl p-6 border border-slate-100">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-bold text-gray-900">Phân bổ theo {view === 'daily' ? 'ngày' : view === 'weekly' ? 'tuần' : 'tháng'}</h3>
            <span className="text-xs text-slate-500">{viewAggregated.length} nhóm</span>
          </div>
          {viewAggregated.length > 0 ? (
            <div className="divide-y divide-slate-200 max-h-80 overflow-y-auto">
              {viewAggregated.map((item, idx) => (
                <div key={item.label} className="py-3 flex items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-800 truncate">{idx + 1}. {item.label}</p>
                    <p className="text-xs text-slate-500">Trung bình: {formatVnd(item.avg ?? 0)}</p>
                  </div>
                  <div className="text-right flex flex-col items-end">
                    <span className="text-sm font-bold text-slate-900">{formatVnd(item.total)}</span>
                    <span className="text-[11px] text-slate-500">Tổng</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-6">Không có dữ liệu</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="bg-white shadow-md rounded-xl p-6 border border-slate-100 xl:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Top ngày tiêu tốn</h3>
              <p className="text-sm text-slate-600">Xếp hạng chi phí cao nhất trong cửa sổ</p>
            </div>
            <span className="text-xs text-slate-500">Top 10</span>
          </div>
          {filteredCosts.length > 0 ? (
            <TopList costs={filteredCosts.slice().sort((a, b) => b.cost - a.cost).slice(0, 10)} />
          ) : (
            <p className="text-slate-600 text-center py-6">Chưa có dữ liệu</p>
          )}
        </div>

        <div className="bg-white shadow-md rounded-xl p-6 border border-slate-100">
          <h3 className="text-lg font-bold text-slate-900 mb-3">Biến động & phân phối</h3>
          <div className="space-y-3">
            <DistributionRow label="Độ lệch chuẩn" value={formatVnd(costStats.stddev)} note="Độ dao động quanh trung bình" color="from-indigo-500 to-indigo-700" />
            <DistributionRow label="Min" value={formatVnd(costStats.min)} note="Thấp nhất trong cửa sổ" color="from-emerald-500 to-emerald-700" />
            <DistributionRow label="Max" value={formatVnd(costStats.max)} note="Cao nhất trong cửa sổ" color="from-amber-500 to-orange-600" />
          </div>
        </div>
      </div>

      <div className="bg-white shadow-md rounded-xl overflow-hidden border border-slate-100">
        <div className="flex flex-wrap items-center gap-3 px-6 py-4 bg-slate-50 border-b border-slate-200">
          <div>
            <label className="block text-xs text-slate-600">Năm</label>
            <select
              value={tableYear}
              onChange={(e) => setTableYear(e.target.value)}
              className="px-3 py-2 border border-slate-200 rounded-md text-sm shadow-sm text-slate-800"
            >
              <option value="all">Tất cả</option>
              {Array.from(new Set(costs.map((c) => parseCostDate(c.date).getFullYear().toString()))).map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-600">Tháng</label>
            <select
              value={tableMonth}
              onChange={(e) => setTableMonth(e.target.value)}
              className="px-3 py-2 border border-slate-200 rounded-md text-sm shadow-sm text-slate-800"
            >
              <option value="all">Tất cả</option>
              {[...Array(12)].map((_, idx) => (
                <option key={idx + 1} value={idx + 1}>{idx + 1}</option>
              ))}
            </select>
          </div>
        </div>
        {tableFilteredCosts.length > 0 ? (
          <div className="divide-y divide-slate-200 max-h-[520px] overflow-y-auto">
            {tableFilteredCosts.map((item, index) => (
              <div key={index} className="px-6 py-4 flex items-start justify-between gap-4 hover:bg-slate-50">
                <div className="flex-1 min-w-0 text-sm text-slate-900">
                  {(() => {
                    const d = parseCostDate(item.date);
                    return Number.isFinite(d.getTime())
                      ? d.toLocaleDateString('vi-VN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
                      : item.date;
                  })()}
                </div>
                <div className="text-sm font-semibold text-slate-900 whitespace-nowrap">{formatVnd(item.cost)}</div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-600 text-center py-6">Không có dữ liệu</p>
        )}
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

type HeroStatProps = {
  label: string;
  value: string;
  hint?: string;
};

function HeroStat({ label, value, hint }: HeroStatProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-800">{label}</p>
      <p className="text-2xl font-bold text-slate-900">{value}</p>
      {hint && <p className="text-[11px] text-slate-600 mt-1">{hint}</p>}
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

function TopList({ costs }: { costs: CostItem[] }) {
  const max = Math.max(...costs.map((c) => c.cost), 1);
  return (
    <div className="space-y-3">
      {costs.map((item, idx) => {
        const parsed = parseCostDate(item.date);
        const label = Number.isFinite(parsed.getTime())
          ? parsed.toLocaleDateString('vi-VN', { weekday: 'short', month: 'short', day: 'numeric' })
          : item.date;
        const pct = (item.cost / max) * 100;
        return (
          <div key={idx} className="flex items-center gap-3">
            <span className="w-6 text-sm font-semibold text-slate-700">{idx + 1}</span>
            <div className="flex-1">
              <div className="flex justify-between text-sm text-slate-700">
                <span>{label}</span>
                <span className="font-semibold">{formatVnd(item.cost)}</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden mt-1">
                <div className="h-full bg-gradient-to-r from-amber-400 to-amber-600" style={{ width: `${pct}%` }}></div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

type DistributionRowProps = {
  label: string;
  value: string;
  note?: string;
  color: string;
};

function DistributionRow({ label, value, note, color }: DistributionRowProps) {
  return (
    <div className="p-3 rounded-lg border border-slate-100 bg-slate-50">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-800">{label}</p>
          {note && <p className="text-xs text-slate-500">{note}</p>}
        </div>
        <span className={`text-sm font-bold bg-clip-text text-transparent bg-gradient-to-r ${color}`}>{value}</span>
      </div>
    </div>
  );
}
