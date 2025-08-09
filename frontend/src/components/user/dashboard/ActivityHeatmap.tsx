import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface ActivityHeatmapProps {
  selectedYear: number;
  setSelectedYear: (year: number) => void;
  generateYearActivityData: (year: number) => { date: Date; level: number; count: number; isCurrentYear: boolean; dateKey: string }[];
  handleActivityClick: (dateKey: string, level: number) => void;
}

export const ActivityHeatmap: React.FC<ActivityHeatmapProps> = ({ selectedYear, setSelectedYear, generateYearActivityData, handleActivityClick }) => {
  return (
    <Card className="md:col-span-2 bg-[#0d1117] text-gray-200 border border-gray-700/60 overflow-hidden">
      <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between">
        <CardTitle className="text-base text-gray-100">Hoạt động {selectedYear}</CardTitle>
        <select
          value={selectedYear}
          onChange={(e) => setSelectedYear(+e.target.value)}
          className="text-[11px] rounded-full border border-gray-600 bg-[#161b22] text-gray-300 px-3 py-1 focus:outline-none focus:ring-2 focus:ring-emerald-500"
        >
          {[new Date().getFullYear(), new Date().getFullYear() - 1, new Date().getFullYear() - 2].map((y) => (
            <option key={y}>{y}</option>
          ))}
        </select>
      </CardHeader>
      <CardContent className="px-4 pt-0 pb-4">
        <div className="space-y-2">
          <div className="flex text-[10px] text-gray-500 mb-1 px-px select-none">
            {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].map(m => (
              <div key={m} className="flex-1 text-center font-medium tracking-wide">{m}</div>
            ))}
          </div>
          <div className="relative">
            <div className="grid grid-rows-7 gap-[3px]" style={{ gridTemplateColumns: 'repeat(53, 1fr)' }}>
              {(() => {
                const yearActivityData = generateYearActivityData(selectedYear);
                const colors = ['#161b22','#003820','#005c31','#238b45','#2ea043'];
                return yearActivityData.map((activity, i) => {
                  const isCurrentYear = activity.isCurrentYear;
                  const bg = isCurrentYear ? colors[activity.level] : 'transparent';
                  const border = isCurrentYear ? '#30363d' : 'transparent';
                  return (
                    <div
                      key={i}
                      className={`w-full aspect-square rounded-[2px] transition-transform ${isCurrentYear ? 'cursor-pointer hover:scale-110' : 'opacity-30'}`}
                      style={{ backgroundColor: bg, border: `1px solid ${border}` }}
                      onClick={() => isCurrentYear && handleActivityClick(activity.dateKey, activity.level)}
                      title={isCurrentYear ? `${activity.date.toLocaleDateString('vi-VN')} - Level ${activity.level}` : activity.date.toLocaleDateString('vi-VN')}
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
        <div className="flex items-center justify-end mt-3 gap-2 text-[10px] text-gray-500">
          <span>Less</span>
          {[0,1,2,3,4].map(l => {
            const legendColors = ['#161b22','#003820','#005c31','#238b45','#2ea043'];
            return <span key={l} className="w-3 h-3 rounded-[2px]" style={{ backgroundColor: legendColors[l], border: '1px solid #30363d' }} />
          })}
          <span>More</span>
        </div>
      </CardContent>
    </Card>
  );
};
