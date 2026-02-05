'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Navbar } from "@/components/navbar"
import { StatsCards } from "@/components/stats-cards"
import { RecentSessions } from "@/components/recent-sessions"
import { GrowthChart } from "@/components/growth-chart"
import { FocusTimer } from "@/components/focus-timer"
import { MotivationalQuote } from "@/components/motivational-quote"

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
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="container mx-auto px-4 py-8 md:px-6 lg:px-8 max-w-7xl">
        {/* Header Section */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-semibold text-foreground mb-2 text-balance">
            Welcome back, {user.displayName || 'Learner'}
          </h1>
          <p className="text-muted-foreground text-lg">Your growth continues today</p>
        </div>

        {/* Motivational Quote */}
        <MotivationalQuote />

        {/* Stats Cards */}
        <StatsCards />

        {/* Two Column Layout */}
        <div className="grid gap-6 lg:grid-cols-3 mt-6">
          {/* Main Content - 2 columns */}
          <div className="lg:col-span-2 space-y-6">
            <GrowthChart />
            <RecentSessions userId={user.id} />
          </div>

          {/* Sidebar - 1 column */}
          <div className="space-y-6">
            <FocusTimer />
          </div>
        </div>
      </main>
    </div>
  );
}

