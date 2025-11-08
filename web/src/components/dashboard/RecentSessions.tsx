'use client';

import { useEffect, useState } from 'react';
import { formatDuration, getRelativeTime } from '@dan/shared';
import type { StudySession } from '@dan/shared';

interface RecentSessionsProps {
  userId: string;
}

export default function RecentSessions({ userId }: RecentSessionsProps) {
  const [sessions, setSessions] = useState<StudySession[]>([]);

  useEffect(() => {
    // Fetch recent sessions from Firestore
    // Placeholder for now
  }, [userId]);

  if (sessions.length === 0) {
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
        {sessions.map((session) => (
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

