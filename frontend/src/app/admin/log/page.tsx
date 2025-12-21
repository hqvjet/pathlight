"use client";
import { useEffect, useMemo, useState } from 'react';
import { adminApi, LogItem } from '@/lib/api/admin';
import { showToast } from '@/utils/toast';

const baseServices = [
  'all',
  'pathlight-agentic-service',
  'pathlight-authentication-service',
  'pathlight-course-service',
  'pathlight-user-service',
  'pathlight-quiz-service',
];

type FilterKeyOption = 'daily' | 'weekly' | 'monthly' | 'hourly' | '30m' | '1m';

export default function AdminLogsPage() {
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterKey, setFilterKey] = useState<FilterKeyOption>('daily');
  const [service, setService] = useState('all');
  const [serviceOptions, setServiceOptions] = useState<string[]>(baseServices);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const resp = await adminApi.getLogs(filterKey, service === 'all' ? undefined : service);
      const fetchedLogs = resp?.data?.logs ?? [];
      setLogs(fetchedLogs);

      const dynamicServices = Array.from(new Set(fetchedLogs.map((log) => log.source).filter(Boolean)));
      setServiceOptions(Array.from(new Set([...baseServices, ...dynamicServices])));
    } catch (error) {
      showToast.error('Lỗi khi tải logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey, service]);

  const typeCounts = useMemo(() => {
    return logs.reduce(
      (acc, log) => {
        const lower = (log.type || '').toLowerCase();
        if (lower.includes('error')) acc.error += 1;
        else if (lower.includes('warn')) acc.warn += 1;
        else if (lower.includes('info')) acc.info += 1;
        else acc.other += 1;
        return acc;
      },
      { error: 0, warn: 0, info: 0, other: 0 }
    );
  }, [logs]);

  const serviceCounts = useMemo(() => {
    return logs.reduce<Record<string, number>>((acc, log) => {
      const key = log.source || 'unknown';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
  }, [logs]);

  const timelineCounts = useMemo(() => {
    const toBucket = (ts: string) => {
      const safe = ts.replace(' ', 'T');
      const date = new Date(safe);
      if (!Number.isFinite(date.getTime())) return ts;
      const yyyy = date.getFullYear();
      const mm = String(date.getMonth() + 1).padStart(2, '0');
      const dd = String(date.getDate()).padStart(2, '0');
      const hh = String(date.getHours()).padStart(2, '0');
      const mi = String(date.getMinutes()).padStart(2, '0');

      if (filterKey === 'hourly') return `${yyyy}-${mm}-${dd} ${hh}:00`;
      if (filterKey === '30m') return `${yyyy}-${mm}-${dd} ${hh}:${Number(mi) < 30 ? '00' : '30'}`;
      if (filterKey === '1m') return `${yyyy}-${mm}-${dd} ${hh}:${mi}`;
      return `${yyyy}-${mm}-${dd}`;
    };

    return logs.reduce<Record<string, number>>((acc, log) => {
      const key = toBucket(log.timestamp);
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
  }, [logs, filterKey]);

  const getLogTypeColor = (type: string) => {
    const lowerType = type.toLowerCase();
    if (lowerType.includes('error')) return 'text-red-600 bg-red-50';
    if (lowerType.includes('warn')) return 'text-yellow-600 bg-yellow-50';
    if (lowerType.includes('info')) return 'text-blue-600 bg-blue-50';
    return 'text-gray-600 bg-gray-50';
  };

  const getLogTypeBadgeColor = (type: string) => {
    const lowerType = type.toLowerCase();
    if (lowerType.includes('error')) return 'bg-red-100 text-red-800';
    if (lowerType.includes('warn')) return 'bg-yellow-100 text-yellow-800';
    if (lowerType.includes('info')) return 'bg-blue-100 text-blue-800';
    return 'bg-gray-100 text-gray-800';
  };

  const totalLogs = logs.length;
  const chartMax = Math.max(...Object.values(timelineCounts), 1);

  if (loading && logs.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <p className="text-sm text-slate-500">Quan sát hệ thống</p>
          <h2 className="text-2xl font-bold text-gray-900">Nhật ký CloudWatch</h2>
          <p className="text-sm text-slate-500">Xem nhanh lỗi, cảnh báo và thông tin theo dịch vụ</p>
        </div>
        <button onClick={loadLogs} className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
          Làm mới
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Tổng số log" value={totalLogs} tone="slate" />
        <StatCard label="Lỗi" value={typeCounts.error} tone="red" />
        <StatCard label="Cảnh báo" value={typeCounts.warn} tone="amber" />
        <StatCard label="Thông tin" value={typeCounts.info} tone="blue" />
      </div>

      <div className="bg-white shadow-md rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Khoảng thời gian</label>
            <select
              value={filterKey}
              onChange={(e) => setFilterKey(e.target.value as FilterKeyOption)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="1m">1 phút gần nhất</option>
              <option value="30m">30 phút gần nhất</option>
              <option value="hourly">1 giờ gần nhất</option>
              <option value="daily">24 giờ gần nhất</option>
              <option value="weekly">7 ngày gần nhất</option>
              <option value="monthly">30 ngày gần nhất</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Lọc theo dịch vụ</label>
            <select
              value={service}
              onChange={(e) => setService(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {serviceOptions.map((svc) => (
                <option key={svc} value={svc}>
                  {svc === 'all' ? 'Tất cả dịch vụ' : svc}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={loadLogs}
              className="w-full px-4 py-2 bg-slate-800 text-white rounded-md hover:bg-slate-900"
            >
              Áp dụng bộ lọc
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <ChartCard title="Theo mức độ">
          {[
            { label: 'Lỗi', value: typeCounts.error, color: 'bg-red-500' },
            { label: 'Cảnh báo', value: typeCounts.warn, color: 'bg-amber-500' },
            { label: 'Thông tin', value: typeCounts.info, color: 'bg-blue-500' },
            { label: 'Khác', value: typeCounts.other, color: 'bg-slate-400' },
          ].map((item) => (
            <BarRow key={item.label} label={item.label} value={item.value} total={totalLogs} color={item.color} />
          ))}
        </ChartCard>

        <ChartCard title="Theo dịch vụ">
          {Object.entries(serviceCounts).length === 0 ? (
            <p className="text-sm text-slate-500">Không có dữ liệu</p>
          ) : (
            Object.entries(serviceCounts)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 6)
              .map(([svc, count]) => (
                <BarRow key={svc} label={svc} value={count} total={totalLogs} color="bg-emerald-500" />
              ))
          )}
        </ChartCard>

        <ChartCard title="Dòng thời gian">
          {Object.keys(timelineCounts).length === 0 ? (
            <p className="text-sm text-slate-500">Không có dữ liệu</p>
          ) : (
            <div className="flex items-end gap-2 h-40">
              {Object.entries(timelineCounts)
                .sort(([a], [b]) => (a > b ? 1 : -1))
                .map(([date, count]) => (
                  <div key={date} className="flex flex-col items-center gap-1">
                    <div className="w-10 bg-indigo-500 rounded-md" style={{ height: `${(count / chartMax) * 100}%` }} title={`${date}: ${count}`} />
                    <span className="text-[10px] text-slate-600">{date.slice(5)}</span>
                  </div>
                ))}
            </div>
          )}
        </ChartCard>
      </div>

      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h3 className="text-sm font-medium text-gray-900">Danh sách log ({logs.length})</h3>
        </div>

        <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
          {logs.length > 0 ? (
            logs.map((log, index) => (
              <div key={index} className={`p-4 hover:bg-gray-50 ${getLogTypeColor(log.type)}`}>
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getLogTypeBadgeColor(log.type)}`}>
                      {log.type}
                    </span>
                    <span className="text-xs text-gray-500">{new Date(log.timestamp).toLocaleString('vi-VN')}</span>
                  </div>
                  <span className="text-xs text-gray-500 font-mono">{log.source}</span>
                </div>
                <div className="text-sm text-gray-900 font-mono bg-gray-50 p-3 rounded border border-gray-200 overflow-x-auto">
                  <pre className="whitespace-pre-wrap break-words">{log.log}</pre>
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-gray-500">
              <p>No logs found for the selected filters.</p>
              <p className="text-sm mt-2">Try adjusting the time period or service filter.</p>
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-blue-800 text-sm">
          <strong>Note:</strong> Logs are fetched from AWS CloudWatch. The data shown depends on your CloudWatch configuration and retention policies.
        </p>
      </div>
    </div>
  );
}

type StatCardProps = {
  label: string;
  value: number;
  tone: 'slate' | 'red' | 'amber' | 'blue';
};

function StatCard({ label, value, tone }: StatCardProps) {
  const toneMap: Record<StatCardProps['tone'], string> = {
    slate: 'bg-slate-100 text-slate-900',
    red: 'bg-red-50 text-red-700',
    amber: 'bg-amber-50 text-amber-700',
    blue: 'bg-blue-50 text-blue-700',
  };
  return (
    <div className={`rounded-lg p-4 border border-slate-200 ${toneMap[tone]}`}>
      <p className="text-sm font-medium">{label}</p>
      <p className="text-2xl font-bold">{value.toLocaleString()}</p>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm space-y-3">
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      {children}
    </div>
  );
}

type BarRowProps = {
  label: string;
  value: number;
  total: number;
  color: string;
};

function BarRow({ label, value, total, color }: BarRowProps) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm text-slate-700">
        <span>{label}</span>
        <span className="font-medium">{value.toLocaleString()}</span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div className={`${color} h-full`} style={{ width: `${pct}%` }}></div>
      </div>
      <p className="text-xs text-slate-500">{pct}% of total</p>
    </div>
  );
}
