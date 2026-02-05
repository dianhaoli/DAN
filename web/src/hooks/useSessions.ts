import { useEffect, useState, useMemo, useCallback } from 'react';
import { sessionsApi } from '@/lib/api';
import type { StudySession } from '@dan/shared';
import { auth } from '@/lib/firebase';
import { onAuthStateChanged } from 'firebase/auth';

interface UseSessionsOptions {
  limit?: number;
  skip?: number;
  startDate?: Date;
  endDate?: Date;
  topic?: string;
}

export function useSessions(options: UseSessionsOptions = {}) {
  const [sessions, setSessions] = useState<StudySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [total, setTotal] = useState(0);
  const [authReady, setAuthReady] = useState(false);

  // Memoize date strings to prevent unnecessary re-fetches
  // Round to nearest minute to prevent constant re-fetches when endDate is "now"
  const startDateStr = useMemo(() => {
    if (!options.startDate) return undefined;
    const date = new Date(options.startDate);
    date.setSeconds(0, 0);
    return date.toISOString();
  }, [options.startDate?.getTime()]);
  
  const endDateStr = useMemo(() => {
    if (!options.endDate) return undefined;
    // Round to nearest minute to prevent constant re-fetches
    const date = new Date(options.endDate);
    date.setSeconds(0, 0);
    return date.toISOString();
  }, [Math.floor((options.endDate?.getTime() || 0) / 60000)]); // Round to minutes

  // Wait for auth to be ready before fetching sessions
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      // Auth state has been determined
      setAuthReady(true);
    });

    return () => unsubscribe();
  }, []);

  // Memoize fetch function to prevent unnecessary re-creations
  const fetchSessions = useCallback(async (isInitialLoad: boolean = false) => {
    try {
      // Only set loading to true on initial load to prevent UI flicker during polling
      if (isInitialLoad) {
        setLoading(true);
      }
      setError(null);

      // Check if user is authenticated before making API call
      const user = auth.currentUser;
      if (!user) {
        // User is not authenticated - this is expected if they're not logged in
        setSessions([]);
        setTotal(0);
        setLoading(false);
        return;
      }

      // Ensure we have a valid token (getIdToken automatically refreshes expired tokens)
      try {
        await user.getIdToken(); // This automatically refreshes if expired
      } catch (tokenError) {
        console.error('Error getting auth token:', tokenError);
        throw new Error('Authentication failed. Please log in again.');
      }

      const params: any = {
        limit: options.limit || 20,
        skip: options.skip || 0,
      };

      if (startDateStr) {
        params.start_date = startDateStr;
      }
      if (endDateStr) {
        params.end_date = endDateStr;
      }
      if (options.topic) {
        params.topic = options.topic;
      }

      const response = await sessionsApi.list(params);

      // Transform FastAPI response to StudySession format
      const transformedSessions: StudySession[] = response.sessions.map((s: any) => ({
        id: s.id,
        userId: s.user_id,
        startTime: new Date(s.start_time),
        endTime: s.end_time ? new Date(s.end_time) : undefined,
        duration: s.duration,
        topic: s.topic,
        domains: s.domains || [],
        focusScore: s.focus_score || 0,
        productivityScore: s.productivity_score || 0,
        tabSwitches: s.tab_switches || 0,
        activeTime: s.active_time || 0,
        idleTime: s.idle_time || 0,
        xpEarned: s.xp_earned || 0,
        aiSummary: s.ai_summary,
        source: s.source as 'extension' | 'manual',
        platform: s.platform,
        createdAt: new Date(s.created_at),
        updatedAt: new Date(s.updated_at),
      }));

      setSessions(transformedSessions);
      setTotal(response.total);
    } catch (err) {
      console.error('Error fetching sessions:', err);
      setError(err as Error);
      setSessions([]);
    } finally {
      if (isInitialLoad) {
        setLoading(false);
      }
    }
  }, [options.limit, options.skip, startDateStr, endDateStr, options.topic]);

  useEffect(() => {
    // Don't fetch until auth is ready
    if (!authReady) {
      return;
    }

    // Initial fetch
    fetchSessions(true);

    // Poll for updates every 5 seconds (similar to useTodos)
    // This ensures new sessions from the extension appear automatically
    const interval = setInterval(() => {
      fetchSessions(false);
    }, 5000);

    return () => {
      clearInterval(interval);
    };
  }, [authReady, fetchSessions]);

  return { sessions, loading, error, total };
}
