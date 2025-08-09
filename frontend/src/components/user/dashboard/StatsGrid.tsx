import React from 'react';
import { UserProfile } from './types';

interface StatDef { label: string; value: number | string; color: string; icon: React.ReactNode }
export const StatsGrid: React.FC<{ user: UserProfile }> = ({ user }) => {
  const stats: StatDef[] = [
    { label: 'Tổng Số Khóa Học', value: user.total_courses || 0, color: 'bg-orange-50 text-orange-600', icon: (<svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 19h16M4 5h16M5 12h14"/></svg>) },
    { label: 'Tổng Số Quiz', value: user.total_quizzes || 0, color: 'bg-indigo-50 text-indigo-600', icon: (<svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5h10M5 12h14M9 19h10"/></svg>) },
    { label: 'Tổng Số Bài Học', value: user.lesson_num || 0, color: 'bg-violet-50 text-violet-600', icon: (<svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 4h16v4H4zM4 12h16v8H4z"/></svg>) },
    { label: 'Số Khóa Học Hoàn Thành', value: user.completed_courses || 0, color: 'bg-green-50 text-green-600', icon: (<svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/></svg>) },
    { label: 'Kinh nghiệm', value: (user.current_exp || 0).toLocaleString(), color: 'bg-rose-50 text-rose-600', icon: (<svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>) },
    { label: 'Level', value: user.level || 0, color: 'bg-emerald-50 text-emerald-600', icon: (<svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path strokeLinecap="round" strokeLinejoin="round" d="M19.4 15A1.65 1.65 0 0121 16.65V21h-4.35A1.65 1.65 0 0115 19.35v-.7M4.6 9A1.65 1.65 0 013 7.35V3h4.35A1.65 1.65 0 019 4.65v.7"/></svg>) },
    { label: 'Bậc Xếp Hạng Của Bạn', value: user.rank || 0, color: 'bg-amber-50 text-amber-600', icon: (<svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M11.05 2.93a1 1 0 011.9 0l1.52 4.67a1 1 0 00.95.69h4.91a1 1 0 01.59 1.81l-3.98 2.89a1 1 0 00-.36 1.12l1.52 4.67a1 1 0 01-1.54 1.12l-3.98-2.89a1 1 0 00-1.18 0l-3.98 2.89a1 1 0 01-1.54-1.12l1.52-4.67a1 1 0 00-.36-1.12L2.5 10.1a1 1 0 01.59-1.81h4.91a1 1 0 00.95-.69l1.52-4.67z"/></svg>) },
    { label: 'Tổng Số Người Dùng', value: user.user_num || 0, color: 'bg-slate-100 text-slate-700', icon: (<svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 21v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2M13 7a4 4 0 11-8 0 4 4 0 018 0M21 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>) },
  ];
  return (
    <div className="grid gap-4 md:gap-5 grid-cols-2 sm:grid-cols-3 xl:grid-cols-4">
      {stats.map(stat => (
        <div key={stat.label} className="bg-white rounded-lg border flex items-center gap-4 p-4 shadow-sm hover:shadow transition">
          <div className={`w-12 h-12 rounded-md flex items-center justify-center ${stat.color}/10 ${stat.color.split(' ')[1]} font-medium`}>
            <span className={stat.color}>{stat.icon}</span>
          </div>
          <div className="min-w-0">
            <div className="text-xl font-semibold leading-none tracking-tight truncate">{stat.value}</div>
            <p className="mt-1 text-[11px] font-medium text-gray-500 uppercase tracking-wide">{stat.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
};
