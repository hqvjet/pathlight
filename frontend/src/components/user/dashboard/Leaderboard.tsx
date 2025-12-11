import React from 'react';
import { LeaderboardUser } from './types';
import Avatar from '@/components/common/Avatar';
import { Trophy, Medal } from 'lucide-react';

const pedestalGradients = ['from-sky-500 via-blue-500 to-indigo-600', 'from-indigo-500 via-violet-500 to-purple-600', 'from-emerald-500 via-teal-500 to-cyan-500'];

export const Leaderboard: React.FC<{ top: LeaderboardUser[] }> = ({ top }) => {
  const top3 = [...top].slice(0,3);
  while (top3.length < 3) top3.push({ rank: top3.length+1, name: 'Đang cập nhật', level:0, experience:0, initials:'?', avatar_url:'', id: undefined });
  const order = [2,1,3];
  const sizes: Record<number,{pedestal:string; avatar:number;}> = { 1:{pedestal:'w-44 h-64', avatar:120}, 2:{pedestal:'w-40 h-58', avatar:104}, 3:{pedestal:'w-36 h-52', avatar:92} };

  const renderAvatarRing = (user: LeaderboardUser, size: number) => {
    const ringSize = size + 14;
    const strokeWidthOuter = 6;
    const radiusOuter = (ringSize - strokeWidthOuter) / 2;
    const circumferenceOuter = 2 * Math.PI * radiusOuter;
    // Use level for simple progress accent (clamped)
    const pct = Math.min(1, Math.max(0, (user.level || 1) / 10));
    const dashOuter = circumferenceOuter * pct;
    const offsetOuter = circumferenceOuter - dashOuter;
    return (
      <div className="relative" style={{ width: ringSize, height: ringSize }}>
        <svg className="absolute inset-0" width={ringSize} height={ringSize}>
          <defs>
            <linearGradient id="lbOuter" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="50%" stopColor="#6366f1" />
              <stop offset="100%" stopColor="#0ea5e9" />
            </linearGradient>
          </defs>
          <circle cx={ringSize/2} cy={ringSize/2} r={radiusOuter} stroke="rgba(255,255,255,0.35)" strokeWidth={strokeWidthOuter} fill="none" />
          <circle
            cx={ringSize/2}
            cy={ringSize/2}
            r={radiusOuter}
            stroke="url(#lbOuter)"
            strokeWidth={strokeWidthOuter}
            strokeLinecap="round"
            strokeDasharray={`${dashOuter} ${circumferenceOuter}`}
            strokeDashoffset={offsetOuter}
            fill="none"
          />
        </svg>
        <div className="absolute inset-[7px] rounded-full bg-white shadow-lg flex items-center justify-center">
          <Avatar user={{ ...user, avatar_url: user.id ? `/api/users/avatar?user-id=${encodeURIComponent(user.id)}` : '/assets/images/default_avatar.png' }} size={size} displayName={user.name} showInitialsFallback cacheKey={user.id} className="shadow-md" />
        </div>
      </div>
    );
  };

  return (
    <div className="flex justify-center items-end gap-6 md:gap-10">
      {order.map(r => {
        const u = top3.find(x=>x.rank===r) || top3[r-1];
        const cfg = sizes[u.rank];
        const pedestalGradient = pedestalGradients[(u.rank-1) % pedestalGradients.length];
        return (
          <div key={u.rank} className="flex flex-col items-center">
            <div className="relative mb-6">
              {renderAvatarRing(u, cfg.avatar)}
              {u.rank === 1 && (
                <span className="absolute -top-5 left-1/2 -translate-x-1/2 text-2xl drop-shadow" aria-label="Top 1">👑</span>
              )}
              <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[11px] font-semibold px-3 py-1 rounded-full shadow whitespace-nowrap border border-white/10">{u.name}</div>
            </div>
            <div className={`relative ${cfg.pedestal} rounded-2xl bg-gradient-to-b ${pedestalGradient} flex flex-col items-center justify-end pb-6 text-white shadow-xl overflow-hidden`}> 
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(255,255,255,0.2),rgba(255,255,255,0)_60%)]" />
              <div className="absolute top-2 left-2 text-[11px] font-semibold bg-white/20 backdrop-blur px-2 py-1 rounded-md border border-white/20 text-white/95">{u.rank===1 ? 'TOP 1' : `#${u.rank}`}</div>
              <div className="absolute top-8 flex items-center justify-center">
                {u.rank===1 ? <Trophy className="w-12 h-12 text-white" strokeWidth={1.4} /> : <Medal className="w-12 h-12 text-white/95" strokeWidth={1.4} />}
              </div>
              <div className="mt-20 text-5xl font-black leading-none drop-shadow-sm">{u.level}</div>
              <div className="mt-3 text-xs font-semibold bg-white/20 px-4 py-1 rounded-full backdrop-blur-sm border border-white/30">Level</div>
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
            <td className="py-3 px-4"><Avatar user={u} size={36} displayName={u.name} showInitialsFallback className="shadow-sm" cacheKey={u.id} /></td>
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
