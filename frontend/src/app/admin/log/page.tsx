"use client";
import { useCallback, useEffect, useMemo, useState } from 'react';
import { adminApi, LogItem, LogStream } from '@/lib/api/admin';
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
type SortOrder = 'desc' | 'asc';

export default function AdminLogsPage() {
  const [streams, setStreams] = useState<LogStream[]>([]);
  const [selectedStream, setSelectedStream] = useState<LogStream | null>(null);
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [loadingStreams, setLoadingStreams] = useState(true);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [filterKey, setFilterKey] = useState<FilterKeyOption>('daily');
  const [service, setService] = useState('all');
  const [serviceOptions, setServiceOptions] = useState<string[]>(baseServices);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const loadStreams = useCallback(async () => {
    setLoadingStreams(true);
    setSelectedStream(null);
    setLogs([]);
    try {
      const resp = await adminApi.getLogStreams(filterKey, service === 'all' ? undefined : service);
      const fetchedStreams = resp?.data?.streams ?? [];
      setStreams(fetchedStreams);

      const dynamicServices = Array.from(
        new Set(
          fetchedStreams
            .map((stream) => stream.log_group?.split('/').pop())
            .filter((g): g is string => Boolean(g))
        )
      );
      setServiceOptions(Array.from(new Set([...baseServices, ...dynamicServices])));
    } catch {
      showToast.error('Lỗi khi tải log stream');
    } finally {
      setLoadingStreams(false);
    }
  }, [filterKey, service]);

  useEffect(() => {
    loadStreams();
  }, [loadStreams]);

  const loadLogs = useCallback(
    async (targetStream: LogStream | null) => {
      if (!targetStream) return;
      setLoadingLogs(true);
      try {
        const resp = await adminApi.getLogs(filterKey, targetStream.log_group, targetStream.log_stream);
        const fetched = resp?.data?.logs ?? [];
        setLogs(fetched);
      } catch {
        showToast.error('Lỗi khi tải log');
      } finally {
        setLoadingLogs(false);
      }
    },
    [filterKey]
  );

  const normalizedLogs = useMemo(() => {
    const normalize = (ts: string) => new Date(ts.replace(' ', 'T')).getTime() || 0;
    const sorted = [...logs].sort((a, b) => (sortOrder === 'desc' ? normalize(b.timestamp) - normalize(a.timestamp) : normalize(a.timestamp) - normalize(b.timestamp)));
    if (!searchTerm.trim()) return sorted;
    const keyword = searchTerm.toLowerCase();
    return sorted.filter(
      (log) =>
        log.log.toLowerCase().includes(keyword) ||
        (log.type || '').toLowerCase().includes(keyword) ||
        (log.source || '').toLowerCase().includes(keyword)
    );
  }, [logs, sortOrder, searchTerm]);

  const typeCounts = useMemo(() => {
    return normalizedLogs.reduce(
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
  }, [normalizedLogs]);

  const serviceCounts = useMemo(() => {
    return normalizedLogs.reduce<Record<string, number>>((acc, log) => {
      const key = log.source || 'unknown';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
  }, [normalizedLogs]);

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

    return normalizedLogs.reduce<Record<string, number>>((acc, log) => {
      const key = toBucket(log.timestamp);
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
  }, [normalizedLogs, filterKey]);

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

  const totalLogs = normalizedLogs.length;

  if (loadingStreams && streams.length === 0) {
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
        <div className="flex gap-3">
          <button onClick={loadStreams} className="px-4 py-2 bg-slate-200 text-slate-800 rounded-md hover:bg-slate-300">
            Làm mới stream
          </button>
          <button
            onClick={() => loadLogs(selectedStream)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-60"
            disabled={!selectedStream}
          >
            Tải log của stream
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Tổng số log" value={totalLogs} tone="slate" />
        <StatCard label="Lỗi" value={typeCounts.error} tone="red" />
        <StatCard label="Cảnh báo" value={typeCounts.warn} tone="amber" />
        <StatCard label="Thông tin" value={typeCounts.info} tone="blue" />
      </div>

      <div className="bg-white shadow-md rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tìm kiếm log</label>
            <input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Tìm theo nội dung, loại hoặc nguồn"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sắp xếp theo thời gian</label>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as SortOrder)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="desc">Mới nhất trước</option>
              <option value="asc">Cũ nhất trước</option>
            </select>
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

        <ChartCard title="Theo stream">
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
            <LineChart data={Object.entries(timelineCounts).sort(([a], [b]) => (a > b ? 1 : -1)).map(([label, value]) => ({ label, value }))} />
          )}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-white shadow-md rounded-lg overflow-hidden lg:col-span-1">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-900">Log streams ({streams.length})</h3>
            {loadingStreams ? <span className="text-xs text-slate-500">Đang tải...</span> : null}
          </div>
          <div className="max-h-[600px] overflow-y-auto divide-y divide-gray-200">
            {streams.length === 0 ? (
              <div className="p-6 text-sm text-slate-500">Không có log stream cho bộ lọc này.</div>
            ) : (
              streams.map((stream) => {
                const isActive = selectedStream?.log_stream === stream.log_stream && selectedStream?.log_group === stream.log_group;
                return (
                  <button
                    key={`${stream.log_group}-${stream.log_stream}`}
                    className={`w-full text-left p-4 hover:bg-slate-50 ${isActive ? 'bg-blue-50 border-l-4 border-blue-500' : ''}`}
                    onClick={() => {
                      setSelectedStream(stream);
                      loadLogs(stream);
                    }}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold text-slate-900">{stream.log_stream}</p>
                        <p className="text-xs text-slate-600">{stream.log_group}</p>
                      </div>
                      <span className="text-[11px] text-slate-500">{stream.last_event_time || 'N/A'}</span>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs text-slate-600">
                      <span>Ingest: {stream.last_ingestion_time || 'N/A'}</span>
                      <span>Size: {stream.stored_bytes ? `${stream.stored_bytes}B` : 'N/A'}</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        <div className="bg-white shadow-md rounded-lg overflow-hidden lg:col-span-2">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-900">
              {selectedStream ? `Log của stream: ${selectedStream.log_stream}` : 'Chọn một log stream để xem log'} ({normalizedLogs.length})
            </h3>
            {loadingLogs ? <span className="text-xs text-slate-500">Đang tải...</span> : null}
          </div>

          <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
            {normalizedLogs.length > 0 ? (
              normalizedLogs.map((log, index) => (
                <div key={index} className={`p-4 hover:bg-gray-50 ${getLogTypeColor(log.type)}`}>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getLogTypeBadgeColor(log.type)} ${log.type ? '' : 'hidden'}`}>
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
                <p>{selectedStream ? 'Không có log nào cho stream này.' : 'Chọn một stream để xem log.'}</p>
                <p className="text-sm mt-2">Điều chỉnh bộ lọc hoặc chọn stream khác.</p>
              </div>
            )}
          </div>
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

type LineChartProps = {
  data: { label: string; value: number }[];
};

function LineChart({ data }: LineChartProps) {
  if (data.length === 0) return null;
  const max = Math.max(...data.map((d) => d.value), 1);
  const points = data.map((d, idx) => {
    const x = (idx / Math.max(data.length - 1, 1)) * 100;
    const y = 100 - (d.value / max) * 100;
    return `${x},${y}`;
  });

  return (
    <div className="h-48">
      <svg viewBox="0 0 100 100" className="w-full h-36 text-indigo-500">
        <polyline
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          points={points.join(' ')}
        />
        {data.map((d, idx) => {
          const x = (idx / Math.max(data.length - 1, 1)) * 100;
          const y = 100 - (d.value / max) * 100;
          return <circle key={d.label} cx={x} cy={y} r={1.5} fill="currentColor" />;
        })}
      </svg>
      <div className="flex flex-wrap gap-2 text-[10px] text-slate-600">
        {data.map((d) => (
          <span key={d.label} className="px-1.5 py-0.5 bg-slate-100 rounded">
            {d.label.slice(5)}: {d.value}
          </span>
        ))}
      </div>
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
