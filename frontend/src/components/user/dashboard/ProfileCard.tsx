import { Card, CardContent } from '@/components/ui/card';
import Avatar from '@/components/common/Avatar';
import { UserProfile } from './types';
import React from 'react';

export const ProfileCard: React.FC<{ user: UserProfile }> = ({ user }) => {
  const currentExp = user.current_exp ?? (user as { experience?: number })?.experience ?? 0;
  const requireExp = user.require_exp ?? (user as { exp_needed_for_next?: number; required_exp?: number })?.exp_needed_for_next ?? (user as { required_exp?: number })?.required_exp ?? 0;
  const expPercent = (() => {
    if (!requireExp || requireExp <= 0) return 0;
    return Math.min(100, Math.round((currentExp / requireExp) * 100));
  })();
  const expLabel = `${currentExp} / ${requireExp || 0} EXP`;
  return (
    <Card className="bg-cyan-50 border border-cyan-200 shadow-md md:col-span-1">
      <CardContent className="p-5 space-y-6">
        <div className="flex items-center gap-4">
          <Avatar user={user} size={64} displayName={user.name} showInitialsFallback className="ring-2 ring-cyan-400/60" cacheKey={user.avatarKey} />
          <div className="min-w-0">
            <h2 className="text-base font-semibold leading-tight truncate text-gray-800">{user.name}</h2>
            <p className="text-[11px] text-gray-600 truncate">{user.email}</p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3 text-center text-[10px]">
          <div className="bg-white/80 border border-emerald-200/50 rounded-md py-2 shadow-sm">
            <div className="text-xs font-semibold text-emerald-600">{user.level}</div>
            <div className="text-[9px] text-gray-600 mt-0.5">Level</div>
          </div>
          <div className="bg-white/80 border border-indigo-200/50 rounded-md py-2 shadow-sm">
            <div className="text-xs font-semibold text-indigo-600">{user.completed_courses}/{user.total_courses}</div>
            <div className="text-[9px] text-gray-600 mt-0.5">Courses</div>
          </div>
          <div className="bg-white/80 border border-amber-200/50 rounded-md py-2 shadow-sm">
            <div className="text-xs font-semibold text-amber-600">#{user.rank}</div>
            <div className="text-[9px] text-gray-600 mt-0.5">Rank</div>
          </div>
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-[10px] text-gray-600">
            <span>Kinh nghiệm</span>
            <span className="font-medium text-gray-800">{expPercent}%</span>
          </div>
          <div className="h-2.5 bg-cyan-100/80 rounded overflow-hidden border border-cyan-200/30">
            <div className="h-full bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-500" style={{ width: `${expPercent}%` }} />
          </div>
          <div className="flex justify-between text-[10px] text-gray-500">
            <span>{expLabel}</span>
            <span>Lv {user.level || 1}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
