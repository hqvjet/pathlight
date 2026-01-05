import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface ActivityHeatmapProps {
  selectedYear: number;
  setSelectedYear: (year: number) => void;
  generateYearActivityData: (year: number) => { date: Date; level: number; count: number; isCurrentYear: boolean; dateKey: string }[];
}

export const ActivityHeatmap: React.FC<ActivityHeatmapProps> = ({ selectedYear, setSelectedYear, generateYearActivityData }) => {
  return (
    <Card className="md:col-span-2 bg-cyan-50 border border-cyan-200 overflow-hidden">
      <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between">
        <CardTitle className="text-base text-gray-800">Hoạt động {selectedYear}</CardTitle>
        <select
          value={selectedYear}
          onChange={(e) => setSelectedYear(+e.target.value)}
          className="text-[11px] rounded-full border border-cyan-300 bg-white/80 text-gray-700 px-3 py-1 focus:outline-none focus:ring-2 focus:ring-cyan-400"
        >
          {[new Date().getFullYear(), new Date().getFullYear() - 1, new Date().getFullYear() - 2].map((y) => (
            <option key={y}>{y}</option>
          ))}
        </select>
      </CardHeader>
      <CardContent className="px-4 pt-0 pb-4">
        <div className="space-y-2">
          <div className="flex text-[10px] text-gray-600 mb-1 px-px select-none">
            {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].map(m => (
              <div key={m} className="flex-1 text-center font-medium tracking-wide">{m}</div>
            ))}
          </div>
          <div className="relative">
            <div className="grid gap-[3px]" style={{ gridTemplateRows: 'repeat(7, 1fr)', gridAutoFlow: 'column', gridAutoColumns: '1fr' }}>
              {(() => {
                const yearActivityData = generateYearActivityData(selectedYear);
                const colors = ['#e0f2fe','#7dd3fc','#38bdf8','#0284c7','#0369a1']; // cyan shades
                return yearActivityData.map((activity, i) => {
                  const isCurrentYear = activity.isCurrentYear;
                  const bg = isCurrentYear ? colors[activity.level] : 'transparent';
                  const border = isCurrentYear ? '#bae6fd' : 'transparent';
                  return (
                    <div
                      key={i}
                      className={`w-full aspect-square rounded-[2px] ${isCurrentYear ? 'cursor-default' : 'opacity-30'}`}
                      style={{ backgroundColor: bg, border: `1px solid ${border}` }}
                      title={isCurrentYear ? `${activity.date.toLocaleDateString('vi-VN')} · ${activity.count || 0} điểm` : activity.date.toLocaleDateString('vi-VN')}
                    />
                  );
                });
              })()}
            </div>
          </div>
          <div className="flex justify-start gap-6 text-[10px] text-gray-600 pl-1">
            {['Mon','Wed','Fri'].map(d => <span key={d}>{d}</span>)}
          </div>
        </div>
        <div className="flex items-center justify-end mt-3 gap-2 text-[10px] text-gray-600">
          <span>Less</span>
          {[0,1,2,3,4].map(l => {
            const legendColors = ['#e0f2fe','#7dd3fc','#38bdf8','#0284c7','#0369a1'];
            return <span key={l} className="w-3 h-3 rounded-[2px]" style={{ backgroundColor: legendColors[l], border: '1px solid #bae6fd' }} />
          })}
          <span>More</span>
        </div>
      </CardContent>
    </Card>
  );
};
