'use client';

import { useSessionStats } from '@/hooks/useStats';

interface StatsOverviewProps {
  userId: string;
}

export default function StatsOverview({ userId }: StatsOverviewProps) {
  const { stats, loading, error } = useSessionStats(7); // Last 7 days
  const weeklyStats = useSessionStats(7);
  
  // Calculate weekly hours from weekly stats
  const weeklyHours = weeklyStats.stats?.total_hours || 0;
  
  // Use stats from API or defaults
  const displayStats = {
    totalHours: stats?.total_hours || 0,
    totalSessions: stats?.total_sessions || 0,
    averageFocusScore: stats?.avg_focus_score || 0,
    weeklyHours: weeklyHours,
  };

  const statCards = [
    {
      label: 'Total Study Time',
      value: loading ? '...' : `${displayStats.totalHours.toFixed(1)}h`,
      icon: '⏱️',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      label: 'Sessions Completed',
      value: loading ? '...' : displayStats.totalSessions.toString(),
      icon: '✅',
      color: 'from-green-500 to-emerald-500',
    },
    {
      label: 'Average Focus',
      value: loading ? '...' : `${Math.round(displayStats.averageFocusScore * 100)}%`,
      icon: '🎯',
      color: 'from-purple-500 to-pink-500',
    },
    {
      label: 'This Week',
      value: loading ? '...' : `${displayStats.weeklyHours.toFixed(1)}h`,
      icon: '📅',
      color: 'from-amber-500 to-orange-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statCards.map((stat, index) => (
        <div
          key={index}
          className="bg-white rounded-2xl shadow-md p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-start justify-between mb-4">
            <div className={`w-12 h-12 bg-gradient-to-br ${stat.color} rounded-xl flex items-center justify-center text-2xl`}>
              {stat.icon}
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</div>
          <div className="text-sm text-gray-600">{stat.label}</div>
        </div>
      ))}
    </div>
  );
}

