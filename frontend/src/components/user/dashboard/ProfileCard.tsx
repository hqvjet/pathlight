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
  
  return (
    <Card className="bg-white border border-gray-200 shadow-lg">
      <CardContent className="p-4 sm:p-6">
        <div className="flex flex-col items-center text-center">
          <Avatar 
            user={user} 
            size={80} 
            displayName={user.name} 
            showInitialsFallback 
            className="ring-4 ring-blue-400/30 mb-3 sm:mb-4" 
            cacheKey={user.avatarKey} 
            priority 
          />
          <h2 className="text-lg sm:text-xl font-bold text-gray-900 mb-1">{user.name}</h2>
          <p className="text-xs sm:text-sm text-gray-600 mb-3 sm:mb-4 truncate max-w-full">{user.email}</p>
          
          {/* Level Badge */}
          <div className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-full px-4 py-2 mb-4 shadow-md">
            <div className="flex items-center gap-2">
              <span className="text-xl">⭐</span>
              <span className="font-bold">Level {user.level || 1}</span>
            </div>
          </div>

          {/* EXP Progress */}
          <div className="w-full">
            <div className="flex justify-between text-xs text-gray-600 mb-2">
              <span>Kinh nghiệm</span>
              <span className="font-semibold">{expPercent}%</span>
            </div>
            <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-500 transition-all duration-500" 
                style={{ width: `${expPercent}%` }} 
              />
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>{currentExp} EXP</span>
              <span>{requireExp} EXP</span>
            </div>
            <p className="text-xs text-gray-600 mt-2">
              Còn {requireExp - currentExp} EXP để lên Lv {user.level + 1}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
