import { Card, CardContent } from '@/components/ui/card';
import Avatar from '@/components/common/Avatar';
import { UserProfile } from './types';
import React from 'react';

export const ProfileCard: React.FC<{ user: UserProfile }> = ({ user }) => {
  return (
    <Card className="bg-[#111827] border-none text-white shadow-md md:col-span-1">
      <CardContent className="p-5 space-y-6">
        <div className="flex items-center gap-4">
          <Avatar user={user} size={64} displayName={user.name} showInitialsFallback className="ring-2 ring-violet-500/40" />
          <div className="min-w-0">
            <h2 className="text-base font-semibold leading-tight truncate">{user.name}</h2>
            <p className="text-[11px] text-gray-400 truncate">{user.email}</p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3 text-center text-[10px]">
          <div className="bg-white/5 rounded-md py-2">
            <div className="text-xs font-semibold text-emerald-400">{user.level}</div>
            <div className="text-[9px] text-gray-400 mt-0.5">Level</div>
          </div>
          <div className="bg-white/5 rounded-md py-2">
            <div className="text-xs font-semibold text-indigo-400">{user.completed_courses}/{user.total_courses}</div>
            <div className="text-[9px] text-gray-400 mt-0.5">Courses</div>
          </div>
          <div className="bg-white/5 rounded-md py-2">
            <div className="text-xs font-semibold text-amber-400">#{user.rank}</div>
            <div className="text-[9px] text-gray-400 mt-0.5">Rank</div>
          </div>
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-[10px] text-gray-400">
            <span>Tiến độ khóa học</span>
            <span className="font-medium text-gray-200">{user.total_courses ? Math.round((user.completed_courses!/user.total_courses!)*100) : 0}%</span>
          </div>
          <div className="h-2.5 bg-gray-700/70 rounded">
            <div className="h-2.5 rounded bg-gradient-to-r from-emerald-400 via-emerald-500 to-emerald-400" style={{ width: `${user.total_courses ? Math.round((user.completed_courses!/user.total_courses!)*100) : 0}%` }} />
          </div>
          <div className="flex justify-between text-[10px] text-gray-500">
            <span>{user.completed_courses} / {user.total_courses}</span>
            <span>{(user.current_exp||0).toLocaleString()} EXP</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
