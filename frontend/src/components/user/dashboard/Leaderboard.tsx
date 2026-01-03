import React from 'react';
import { LeaderboardUser } from './types';
import Avatar from '@/components/common/Avatar';
import { Trophy, Medal } from 'lucide-react';

const pedestalGradients = ['from-sky-500 via-blue-500 to-indigo-600', 'from-indigo-500 via-violet-500 to-purple-600', 'from-emerald-500 via-teal-500 to-cyan-500'];

export const Leaderboard: React.FC<{ top: LeaderboardUser[] }> = ({ top }) => {
  if (!top || top.length === 0) {
    return (
      <div className="flex justify-center items-center py-12 text-gray-400">
        <p>Chưa có dữ liệu xếp hạng</p>
      </div>
    );
  }
  
  // Get top 3 users by rank, ensuring we have the actual top ranked users
  const topThree = [...top]
    .sort((a, b) => (a.rank || 999) - (b.rank || 999))
    .slice(0, 3);
  
  // Display order: 2nd place, 1st place (center/tallest), 3rd place
  const displayOrder = [1, 0, 2]; // indices in topThree array
  const sizes: Record<number,{pedestal:string; avatar:number;}> = { 
    0:{pedestal:'w-28 h-40 sm:w-36 md:w-44 sm:h-48 md:h-64', avatar:80}, // 1st place
    1:{pedestal:'w-24 h-36 sm:w-32 md:w-40 sm:h-44 md:h-56', avatar:68}, // 2nd place
    2:{pedestal:'w-20 h-28 sm:w-28 md:w-36 sm:h-36 md:h-48', avatar:60}  // 3rd place
  };

  const renderAvatar = (user: LeaderboardUser, size: number) => {
    return (
      <div className="rounded-full bg-white shadow-lg p-1">
        <Avatar
          user={{ ...user, avatar_url: user.id ? `/api/users/avatar?user-id=${encodeURIComponent(user.id)}` : '/assets/images/default_avatar.png' }}
          size={size}
          displayName={user.name}
          showInitialsFallback
          cacheKey={user.avatarKey ?? user.id}
          className="shadow-md"
        />
      </div>
    );
  };

  return (
    <div>
      {/* Top 3 Podium */}
      <div className="flex justify-center items-end gap-2 sm:gap-4 md:gap-6 lg:gap-10 pb-2 px-2 mb-6">
        {displayOrder.map((idx) => {
          const u = topThree[idx];
          if (!u) return null;
          const cfg = sizes[idx];
          const pedestalGradient = pedestalGradients[idx % pedestalGradients.length];
          return (
          <div key={u.rank} className="flex flex-col items-center flex-shrink-0">
            <div className="relative mb-4 sm:mb-6">
              {renderAvatar(u, cfg.avatar)}
              <div className="absolute -bottom-3 sm:-bottom-4 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[9px] sm:text-[11px] font-semibold px-2 sm:px-3 py-0.5 sm:py-1 rounded-full shadow whitespace-nowrap border border-white/10 max-w-[80px] sm:max-w-none truncate">{u.name}</div>
            </div>
            <div className={`relative ${cfg.pedestal} rounded-xl sm:rounded-2xl bg-gradient-to-b ${pedestalGradient} flex flex-col items-center justify-end pb-4 sm:pb-6 text-white shadow-xl overflow-hidden`}> 
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(255,255,255,0.2),rgba(255,255,255,0)_60%)]" />
              <div className="absolute top-1.5 sm:top-2 left-1.5 sm:left-2 text-[9px] sm:text-[11px] font-semibold bg-white/20 backdrop-blur px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-md border border-white/20 text-white/95">{u.rank===1 ? 'TOP 1' : `#${u.rank}`}</div>
              <div className="absolute top-6 sm:top-8 flex items-center justify-center">
                {u.rank===1 ? <Trophy className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 text-white" strokeWidth={1.4} /> : <Medal className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 text-white/95" strokeWidth={1.4} />}
              </div>
              <div className="mt-14 sm:mt-16 md:mt-20 text-3xl sm:text-4xl md:text-5xl font-black leading-none drop-shadow-sm">{u.level}</div>
              <div className="mt-2 sm:mt-3 text-[10px] sm:text-xs font-semibold bg-white/20 px-2 sm:px-4 py-0.5 sm:py-1 rounded-full backdrop-blur-sm border border-white/30">Level</div>
            </div>
          </div>
        );
      })}
    </div>
  </div>
  );
};

export const LeaderboardTable: React.FC<{ users: LeaderboardUser[] }> = ({ users }) => {
  // Only show users ranked 4 and below
  const tableUsers = users.filter(u => (u.rank || 0) > 3).sort((a, b) => (a.rank || 999) - (b.rank || 999));
  
  return (
  <div className="rounded-xl border bg-white -mx-1 sm:mx-0 overflow-hidden">
    <table className="w-full text-sm">
      <thead className="bg-gray-50 text-xs uppercase text-gray-600">
        <tr>
          <th className="py-2 sm:py-3 px-2 sm:px-3 text-left font-semibold w-16">Rank</th>
          <th className="py-2 sm:py-3 px-2 sm:px-3 text-left font-semibold w-16">Ảnh</th>
          <th className="py-2 sm:py-3 px-2 sm:px-3 text-left font-semibold">Người Dùng</th>
          <th className="py-2 sm:py-3 px-2 sm:px-3 text-left font-semibold w-20">Level</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {tableUsers.map(u => (
          <tr key={u.rank} className="hover:bg-gray-50 transition-colors">
            <td className="py-2 sm:py-3 px-2 sm:px-3 font-medium text-gray-700 w-16">#{u.rank}</td>
            <td className="py-2 sm:py-3 px-2 sm:px-3"><Avatar user={u} size={32} displayName={u.name} showInitialsFallback className="shadow-sm" cacheKey={u.avatarKey ?? u.id} /></td>
            <td className="py-2 sm:py-3 px-2 sm:px-3 font-medium text-gray-800 truncate max-w-[100px] sm:max-w-[140px]">{u.name}</td>
            <td className="py-2 sm:py-3 px-2 sm:px-3 font-semibold text-violet-600">{u.level}</td>
          </tr>
        ))}
        {tableUsers.length === 0 && (
          <tr><td colSpan={4} className="py-6 text-center text-gray-400 text-sm">Không có xếp hạng khác</td></tr>
        )}
      </tbody>
    </table>
  </div>
  );
};
