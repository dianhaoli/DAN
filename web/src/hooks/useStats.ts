import { useEffect, useState } from 'react';
import { sessionsApi, usersApi } from '@/lib/api';

interface SessionStats {
  total_sessions: number;
  total_duration: number;
  total_hours: number;
  avg_focus_score: number;
  avg_productivity_score: number;
  period_days: number;
}

interface UserStats {
  total_sessions: number;
  total_hours: number;
  average_focus_score: number;
  average_productivity_score: number;
  topic_distribution: Record<string, number>;
  study_heatmap: Record<string, number>;
  weekly_trend: number[];
}

export function useSessionStats(days: number = 7) {
  const [stats, setStats] = useState<SessionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchStats() {
      try {
        setLoading(true);
        setError(null);
        const data = await sessionsApi.getStats(days);
        if (cancelled) return;
        setStats(data);
      } catch (err) {
        if (cancelled) return;
        console.error('Error fetching session stats:', err);
        setError(err as Error);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchStats();
    return () => {
      cancelled = true;
    };
  }, [days]);

  return { stats, loading, error };
}

export function useUserStats(userId: string | null) {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!userId) {
      setStats(null);
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function fetchStats() {
      try {
        setLoading(true);
        setError(null);
        const data = await usersApi.getStats(userId);
        if (cancelled) return;
        setStats(data);
      } catch (err) {
        if (cancelled) return;
        console.error('Error fetching user stats:', err);
        setError(err as Error);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchStats();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  return { stats, loading, error };
}
