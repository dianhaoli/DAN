'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { useState } from 'react';
import { formatDuration, getRelativeTime, formatDate } from '@dan/shared';

export default function SessionsPage() {
  const { user } = useAuthContext();
  const [filter, setFilter] = useState<'all' | 'week' | 'month'>('week');

  // Mock data - would fetch from Firestore
  const sessions = [
    {
      id: '1',
      topic: 'Machine Learning Algorithms',
      duration: 3600,
      focusScore: 0.89,
      xpEarned: 180,
      startTime: new Date(Date.now() - 86400000),
      aiSummary: 'Studied supervised learning algorithms including decision trees and random forests.',
    },
    {
      id: '2',
      topic: 'Linear Algebra',
      duration: 2700,
      focusScore: 0.92,
      xpEarned: 162,
      startTime: new Date(Date.now() - 172800000),
      aiSummary: 'Reviewed matrix operations and eigenvalues.',
    },
    {
      id: '3',
      topic: 'Web Development',
      duration: 5400,
      focusScore: 0.85,
      xpEarned: 270,
      startTime: new Date(Date.now() - 259200000),
      aiSummary: 'Built a responsive dashboard using React and TailwindCSS.',
    },
  ];

  if (!user) return null;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Study Sessions</h1>
            <p className="text-gray-600 mt-1">Review your study history and performance.</p>
          </div>

          {/* Filter */}
          <div className="flex gap-2">
            {(['all', 'week', 'month'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  filter === f
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {f === 'all' ? 'All Time' : f === 'week' ? 'This Week' : 'This Month'}
              </button>
            ))}
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl shadow-md p-6">
            <div className="text-sm text-gray-600 mb-2">Total Study Time</div>
            <div className="text-3xl font-bold text-gray-900">
              {formatDuration(sessions.reduce((sum, s) => sum + s.duration / 60, 0))}
            </div>
          </div>
          <div className="bg-white rounded-2xl shadow-md p-6">
            <div className="text-sm text-gray-600 mb-2">Average Focus</div>
            <div className="text-3xl font-bold text-gray-900">
              {Math.round((sessions.reduce((sum, s) => sum + s.focusScore, 0) / sessions.length) * 100)}%
            </div>
          </div>
          <div className="bg-white rounded-2xl shadow-md p-6">
            <div className="text-sm text-gray-600 mb-2">Total XP Earned</div>
            <div className="text-3xl font-bold text-gray-900">
              {sessions.reduce((sum, s) => sum + s.xpEarned, 0)} XP
            </div>
          </div>
        </div>

        {/* Sessions List */}
        <div className="bg-white rounded-2xl shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Session History</h3>
          </div>

          <div className="divide-y divide-gray-200">
            {sessions.map((session) => (
              <div key={session.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-gray-900 mb-1">{session.topic}</h4>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span>{formatDate(session.startTime)}</span>
                      <span>•</span>
                      <span>{getRelativeTime(session.startTime)}</span>
                    </div>
                  </div>
                  <div className="px-4 py-2 bg-primary-50 text-primary-700 rounded-lg font-semibold">
                    +{session.xpEarned} XP
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">Duration:</span>
                    <span className="font-medium">{formatDuration(session.duration / 60)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">Focus:</span>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden w-32">
                        <div
                          className="h-full bg-primary-600 rounded-full"
                          style={{ width: `${session.focusScore * 100}%` }}
                        />
                      </div>
                      <span className="font-medium">{Math.round(session.focusScore * 100)}%</span>
                    </div>
                  </div>
                </div>

                {session.aiSummary && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                    <div className="flex items-start gap-2">
                      <span className="text-lg">🧠</span>
                      <div className="flex-1">
                        <div className="text-xs font-medium text-purple-700 mb-1">AI Summary</div>
                        <p className="text-sm text-gray-700">{session.aiSummary}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

