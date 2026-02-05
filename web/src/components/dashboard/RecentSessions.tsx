'use client';

import { useSessions } from '@/hooks/useSessions';
import { formatDuration, getRelativeTime } from '@dan/shared';

interface RecentSessionsProps {
  userId: string;
}

export default function RecentSessions({ userId }: RecentSessionsProps) {
  const { sessions, loading, error } = useSessions({ limit: 5 });
  
  // Filter sessions to show only recent ones (last 7 days)
  const recentSessions = sessions.filter(s => {
    const daysAgo = (Date.now() - s.startTime.getTime()) / (1000 * 60 * 60 * 24);
    return daysAgo <= 7;
  });

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-md p-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Sessions</h3>
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading sessions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl shadow-md p-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Sessions</h3>
        <div className="text-center py-8">
          <p className="text-red-600">Error loading sessions: {error.message}</p>
        </div>
      </div>
    );
  }

  if (recentSessions.length === 0 && !loading) {
    return (
      <div className="bg-white rounded-2xl shadow-md p-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Sessions</h3>
        <div className="text-center py-8">
          <div className="text-4xl mb-4">📚</div>
          <p className="text-gray-600">No sessions yet. Start studying to see your history!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Recent Sessions</h3>
        <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
          View All
        </button>
      </div>

      <div className="space-y-4">
        {recentSessions.map((session) => (
          <div
            key={session.id}
            className="flex items-center justify-between p-4 border border-gray-200 rounded-xl hover:border-primary-300 transition-colors"
          >
            <div className="flex-1">
              <h4 className="font-medium text-gray-900 mb-1">{session.topic}</h4>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>{getRelativeTime(session.startTime)}</span>
                <span>•</span>
                <span>{formatDuration(session.duration / 60)}</span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  🎯 {Math.round(session.focusScore * 100)}%
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="px-3 py-1 bg-primary-50 text-primary-700 rounded-lg text-sm font-medium">
                +{session.xpEarned} XP
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

