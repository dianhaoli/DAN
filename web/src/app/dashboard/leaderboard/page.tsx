'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import Leaderboard from '@/components/social/Leaderboard';
import { useState } from 'react';

export default function LeaderboardPage() {
  const { user } = useAuthContext();
  const [selectedType, setSelectedType] = useState<'hours' | 'xp' | 'streak'>('hours');
  const [selectedPeriod, setSelectedPeriod] = useState<'weekly' | 'monthly' | 'all-time'>('weekly');
  const [scope, setScope] = useState<'global' | 'friends'>('global');

  if (!user) return null;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Leaderboard</h1>
          <p className="text-gray-600 mt-1">Compete with friends and the global community.</p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Metric</label>
              <div className="flex gap-2">
                {(['hours', 'xp', 'streak'] as const).map((type) => (
                  <button
                    key={type}
                    onClick={() => setSelectedType(type)}
                    className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                      selectedType === type
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Period</label>
              <div className="flex gap-2">
                {(['weekly', 'monthly', 'all-time'] as const).map((period) => (
                  <button
                    key={period}
                    onClick={() => setSelectedPeriod(period)}
                    className={`flex-1 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                      selectedPeriod === period
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {period === 'all-time' ? 'All Time' : period.charAt(0).toUpperCase() + period.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Scope</label>
              <div className="flex gap-2">
                {(['global', 'friends'] as const).map((s) => (
                  <button
                    key={s}
                    onClick={() => setScope(s)}
                    className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                      scope === s
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Leaderboard */}
        <Leaderboard type={selectedType} period={selectedPeriod} scope={scope} userId={user.id} />
      </div>
    </DashboardLayout>
  );
}

