'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import { Navbar } from '@/components/navbar';
import { useState, useMemo } from 'react';
import { formatDuration, getRelativeTime, formatDate } from '@dan/shared';
import { useSessions } from '@/hooks/useSessions';

export default function SessionsPage() {
  const { user, loading: authLoading } = useAuthContext();
  const [filter, setFilter] = useState<'all' | 'week' | 'month'>('week');

  // Memoize date range to prevent unnecessary re-fetches
  // Only recalculate when filter changes, not on every render
  const dateRange = useMemo(() => {
    if (filter === 'all') {
      return undefined;
    }
    
    const now = Date.now();
    const days = filter === 'week' ? 7 : 30;
    
    return {
      startDate: new Date(now - days * 24 * 60 * 60 * 1000),
      endDate: new Date(now),
    };
  }, [filter]);
  const { sessions, loading, error } = useSessions({
    limit: 50,
    startDate: dateRange?.startDate,
    endDate: dateRange?.endDate,
  });

  // Wait for auth to finish loading before rendering
  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8 md:px-6 lg:px-8 max-w-7xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-foreground">Study Sessions</h1>
            <p className="text-muted-foreground mt-1">Review your study history and performance.</p>
          </div>

          {/* Filter */}
          <div className="flex gap-2">
            {(['all', 'week', 'month'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-xl font-medium transition-colors ${
                  filter === f
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-accent/50 text-foreground hover:bg-accent/60'
                }`}
              >
                {f === 'all' ? 'All Time' : f === 'week' ? 'This Week' : 'This Month'}
              </button>
            ))}
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid md:grid-cols-3 gap-6">
          <div className="rounded-2xl bg-card border border-border/40 p-6">
            <div className="text-sm text-muted-foreground mb-2">Total Study Time</div>
            <div className="text-3xl font-semibold text-foreground">
              {loading ? '...' : formatDuration(sessions.reduce((sum, s) => sum + s.duration / 60, 0))}
            </div>
          </div>
          <div className="rounded-2xl bg-card border border-border/40 p-6">
            <div className="text-sm text-muted-foreground mb-2">Average Focus</div>
            <div className="text-3xl font-semibold text-foreground">
              {loading ? '...' : sessions.length > 0 
                ? `${Math.round((sessions.reduce((sum, s) => sum + (s.focusScore || 0), 0) / sessions.length) * 100)}%`
                : '0%'}
            </div>
          </div>
          <div className="rounded-2xl bg-card border border-border/40 p-6">
            <div className="text-sm text-muted-foreground mb-2">Total XP Earned</div>
            <div className="text-3xl font-semibold text-foreground">
              {loading ? '...' : sessions.reduce((sum, s) => sum + (s.xpEarned || 0), 0)} XP
            </div>
          </div>
        </div>

        {/* Sessions List */}
        <div className="rounded-2xl bg-card border border-border/40">
          <div className="p-6 border-b border-border/40">
            <h3 className="text-lg font-semibold text-foreground">Session History</h3>
          </div>

          {loading && (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
              <p className="text-muted-foreground mt-4">Loading sessions...</p>
            </div>
          )}

          {error && (
            <div className="p-12 text-center">
              <p className="text-red-600">Error loading sessions: {error.message}</p>
            </div>
          )}

          {!loading && !error && sessions.length === 0 && (
            <div className="p-12 text-center">
              <div className="text-4xl mb-4">📚</div>
              <p className="text-muted-foreground">No sessions found for this period.</p>
            </div>
          )}

          {!loading && !error && sessions.length > 0 && (
            <div className="divide-y divide-border/40">
              {sessions.map((session) => (
              <div key={session.id} className="p-6 hover:bg-accent/30 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-foreground mb-1">{session.topic}</h4>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{formatDate(session.startTime)}</span>
                      <span>•</span>
                      <span>{getRelativeTime(session.startTime)}</span>
                    </div>
                  </div>
                  <div className="px-4 py-2 bg-primary/10 text-primary rounded-lg font-semibold">
                    +{session.xpEarned} XP
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Duration:</span>
                    <span className="font-medium text-foreground">{formatDuration(session.duration / 60)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Focus:</span>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden w-32">
                        <div
                          className="h-full bg-primary rounded-full"
                          style={{ width: `${session.focusScore * 100}%` }}
                        />
                      </div>
                      <span className="font-medium text-foreground">{Math.round(session.focusScore * 100)}%</span>
                    </div>
                  </div>
                </div>

                {session.aiSummary && (
                  <div className="bg-primary/5 border border-primary/10 rounded-lg p-3">
                    <div className="flex items-start gap-2">
                      <div className="flex-1">
                        <div className="text-xs font-medium text-primary mb-1">AI Summary</div>
                        <p className="text-sm text-foreground/80">{session.aiSummary}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

