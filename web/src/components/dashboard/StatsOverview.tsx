'use client';

import { useEffect, useState } from 'react';
import { formatDuration } from '@dan/shared';

interface StatsOverviewProps {
  userId: string;
}

interface Stats {
  totalHours: number;
  totalSessions: number;
  averageFocusScore: number;
  weeklyHours: number;
}

export default function StatsOverview({ userId }: StatsOverviewProps) {
  const [stats, setStats] = useState<Stats>({
    totalHours: 0,
    totalSessions: 0,
    averageFocusScore: 0,
    weeklyHours: 0,
  });

  useEffect(() => {
    // Fetch stats from Firestore
    // Placeholder for now
    setStats({
      totalHours: 42.5,
      totalSessions: 87,
      averageFocusScore: 0.85,
      weeklyHours: 8.3,
    });
  }, [userId]);

  const statCards = [
    {
      label: 'Total Study Time',
      value: `${stats.totalHours.toFixed(1)}h`,
      icon: '⏱️',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      label: 'Sessions Completed',
      value: stats.totalSessions,
      icon: '✅',
      color: 'from-green-500 to-emerald-500',
    },
    {
      label: 'Average Focus',
      value: `${Math.round(stats.averageFocusScore * 100)}%`,
      icon: '🎯',
      color: 'from-purple-500 to-pink-500',
    },
    {
      label: 'This Week',
      value: `${stats.weeklyHours.toFixed(1)}h`,
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

