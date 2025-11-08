'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import FriendFeed from '@/components/social/FriendFeed';
import BadgeShowcase from '@/components/social/BadgeShowcase';

export default function SocialPage() {
  const { user } = useAuthContext();

  if (!user) return null;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Social Feed</h1>
          <p className="text-gray-600 mt-1">See what your friends are studying and share your progress.</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Feed */}
          <div className="lg:col-span-2">
            <FriendFeed userId={user.id} />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <BadgeShowcase userId={user.id} />
            
            <div className="bg-white rounded-2xl shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Add Friends</h3>
              <input
                type="text"
                placeholder="Search by email..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

