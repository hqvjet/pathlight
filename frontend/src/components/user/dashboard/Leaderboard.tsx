import React from 'react';
import { LeaderboardUser } from './types';
import Avatar from '@/components/common/Avatar';
import { Trophy, Medal } from 'lucide-react';

export const Leaderboard: React.FC<{ top: LeaderboardUser[] }> = ({ top }) => {
  const top3 = [...top].slice(0,3);
  while (top3.length < 3) top3.push({ rank: top3.length+1, name: 'Đang cập nhật', level:0, experience:0, initials:'?', avatar_url:'' });
  const order = [2,1,3];
  const sizes: Record<number,{pedestal:string; avatar:number;}> = { 1:{pedestal:'w-44 h-60', avatar:110}, 2:{pedestal:'w-40 h-52', avatar:96}, 3:{pedestal:'w-40 h-52', avatar:96} };
  return (
    <div className="flex justify-center items-end gap-8">
      {order.map(r => {
        const u = top3.find(x=>x.rank===r) || top3[r-1];
        const cfg = sizes[u.rank];
        return (
          <div key={u.rank} className="flex flex-col items-center">
            <div className="relative mb-5">
              <Avatar user={u} size={cfg.avatar} displayName={u.name} showInitialsFallback className="ring-3 ring-violet-200/60 shadow-md bg-gradient-to-br from-indigo-400 via-blue-500 to-violet-500" />
              {u.rank === 1 && <span className="absolute -top-4 right-2 text-xl" aria-label="Top 1">👑</span>}
              <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[11px] font-medium px-3 py-1 rounded-md shadow whitespace-nowrap">{u.name}</div>
            </div>
            <div className={`relative ${cfg.pedestal} rounded-xl bg-gradient-to-b from-[#5a17ff] via-[#651eff] to-[#7d28ff] flex flex-col items-center justify-end pb-6 text-white shadow-lg overflow-hidden`}>
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(255,255,255,0.18),rgba(255,255,255,0)_60%)]" />
              <div className="absolute top-2 left-2 text-[11px] font-semibold bg-white/15 backdrop-blur px-2 py-1 rounded-md border border-white/10 text-white/90">{u.rank===1 ? 'TOP 1' : `#${u.rank}`}</div>
              <div className="absolute top-8 flex items-center justify-center">
                {u.rank===1 ? <Trophy className="w-12 h-12 text-white" strokeWidth={1.4} /> : <Medal className="w-12 h-12 text-white/95" strokeWidth={1.4} />}
              </div>
              <div className="mt-20 text-5xl font-bold leading-none drop-shadow-sm">{u.level}</div>
              <div className="mt-3 text-xs font-medium bg-white/15 px-4 py-1 rounded-full backdrop-blur-sm border border-white/10">Level</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export const LeaderboardTable: React.FC<{ users: LeaderboardUser[] }> = ({ users }) => (
  <div className="overflow-hidden rounded-xl border bg-white">
    <table className="w-full text-sm">
      <thead className="bg-gray-50 text-xs uppercase text-gray-600">
        <tr>
          <th className="py-3 px-4 text-left font-semibold">Xếp Hạng</th>
          <th className="py-3 px-4 text-left font-semibold">Ảnh</th>
          <th className="py-3 px-4 text-left font-semibold">Người Dùng</th>
          <th className="py-3 px-4 text-left font-semibold">Level</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {users.slice(3,10).map(u => (
          <tr key={u.rank} className="hover:bg-gray-50 transition-colors">
            <td className="py-3 px-4 font-medium text-gray-700">{u.rank}</td>
            <td className="py-3 px-4"><Avatar user={u} size={36} displayName={u.name} showInitialsFallback className="shadow-sm" /></td>
            <td className="py-3 px-4 font-medium text-gray-800 truncate max-w-[140px]">{u.name}</td>
            <td className="py-3 px-4 font-semibold text-violet-600">{u.level}</td>
          </tr>
        ))}
        {(!users || users.length < 4) && (
          <tr><td colSpan={4} className="py-6 text-center text-gray-400 text-sm">Không đủ dữ liệu</td></tr>
        )}
      </tbody>
    </table>
  </div>
);
