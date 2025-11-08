'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { useEffect, useState } from 'react';
import type { AIInsight, WeeklySummary } from '@dan/shared';

export default function InsightsPage() {
  const { user } = useAuthContext();
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [weeklySummary, setWeeklySummary] = useState<WeeklySummary | null>(null);

  useEffect(() => {
    // Fetch AI insights and weekly summary
    // Placeholder for now
    setInsights([
      {
        id: '1',
        userId: user?.id || '',
        type: 'pattern',
        title: '🌅 Morning Productivity Peak',
        message: 'Your focus scores are highest between 8-10 AM. Consider scheduling important topics during this time.',
        isRead: false,
        isDismissed: false,
        createdAt: new Date(),
      },
      {
        id: '2',
        userId: user?.id || '',
        type: 'suggestion',
        title: '📚 Consistent Progress',
        message: 'You\'ve studied 5 days this week! Keep it up to maintain your streak.',
        isRead: false,
        isDismissed: false,
        createdAt: new Date(),
      },
      {
        id: '3',
        userId: user?.id || '',
        type: 'achievement',
        title: '🎯 Focus Champion',
        message: 'Your average focus score this week is 87% - 12% higher than last week!',
        isRead: false,
        isDismissed: false,
        createdAt: new Date(),
      },
    ]);
  }, [user]);

  if (!user) return null;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Insights</h1>
          <p className="text-gray-600 mt-1">Personalized feedback powered by AI to optimize your study habits.</p>
        </div>

        {/* Weekly Summary */}
        <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl shadow-lg p-8 text-white">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-4xl">📊</span>
            <div>
              <h2 className="text-2xl font-bold">This Week's Summary</h2>
              <p className="text-sm opacity-90">Nov 1 - Nov 8, 2025</p>
            </div>
          </div>

          <div className="grid md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4">
              <div className="text-xs opacity-75 mb-1">Total Hours</div>
              <div className="text-3xl font-bold">12.5h</div>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4">
              <div className="text-xs opacity-75 mb-1">Sessions</div>
              <div className="text-3xl font-bold">18</div>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4">
              <div className="text-xs opacity-75 mb-1">Avg Focus</div>
              <div className="text-3xl font-bold">87%</div>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4">
              <div className="text-xs opacity-75 mb-1">XP Gained</div>
              <div className="text-3xl font-bold">1,250</div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-sm leading-relaxed">
              Excellent work this week! You've maintained consistent study habits and your focus has improved significantly.
              Your productivity peaks in the morning hours - consider tackling challenging topics during this time.
              Keep up the momentum to reach your weekly goal!
            </p>
          </div>
        </div>

        {/* AI Insights */}
        <div className="space-y-4">
          {insights.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))}
        </div>

        {/* Productivity Tips */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Productivity Tips</h3>
          <div className="space-y-3">
            {[
              { icon: '🎯', title: 'Set Clear Goals', description: 'Define specific topics before each session' },
              { icon: '⏰', title: 'Use Time Blocks', description: 'Study in 25-50 minute focused intervals' },
              { icon: '🔕', title: 'Minimize Distractions', description: 'Close unnecessary tabs and notifications' },
              { icon: '☕', title: 'Take Breaks', description: 'Short breaks improve focus and retention' },
            ].map((tip, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl">{tip.icon}</div>
                <div>
                  <div className="font-medium text-gray-900">{tip.title}</div>
                  <div className="text-sm text-gray-600">{tip.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

function InsightCard({ insight }: { insight: AIInsight }) {
  const getBackgroundColor = () => {
    switch (insight.type) {
      case 'pattern':
        return 'from-blue-500 to-cyan-500';
      case 'suggestion':
        return 'from-green-500 to-emerald-500';
      case 'achievement':
        return 'from-amber-500 to-orange-500';
      case 'warning':
        return 'from-red-500 to-pink-500';
      default:
        return 'from-gray-500 to-gray-700';
    }
  };

  return (
    <div className={`bg-gradient-to-br ${getBackgroundColor()} rounded-2xl shadow-md p-6 text-white`}>
      <h3 className="text-xl font-bold mb-2">{insight.title}</h3>
      <p className="text-sm opacity-90">{insight.message}</p>
    </div>
  );
}

