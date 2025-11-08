'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import StatsOverview from '@/components/dashboard/StatsOverview';
import CurrentSession from '@/components/dashboard/CurrentSession';
import XPProgress from '@/components/dashboard/XPProgress';
import StreakTracker from '@/components/dashboard/StreakTracker';
import RecentSessions from '@/components/dashboard/RecentSessions';
import WeeklyChart from '@/components/dashboard/WeeklyChart';

export default function Dashboard() {
  const { user, loading } = useAuthContext();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user.displayName}!
          </h1>
          <p className="text-gray-600 mt-1">Track your progress and stay motivated.</p>
        </div>

        {/* Top Row: Current Session + Stats */}
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <CurrentSession />
          </div>
          <div className="space-y-6">
            <XPProgress user={user} />
            <StreakTracker user={user} />
          </div>
        </div>

        {/* Stats Overview */}
        <StatsOverview userId={user.id} />

        {/* Weekly Chart */}
        <WeeklyChart userId={user.id} />

        {/* Recent Sessions */}
        <RecentSessions userId={user.id} />
      </div>
    </DashboardLayout>
  );
}

