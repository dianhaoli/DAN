'use client';

import { TrendingUp, Clock, Flame, Target } from "lucide-react"
import { useSessionStats } from "@/hooks/useStats"
import { useAuthContext } from "@/contexts/AuthContext"

export function StatsCards() {
  const { user } = useAuthContext();
  const { stats, loading } = useSessionStats(7); // Last 7 days
  const allTimeStats = useSessionStats(365); // All time for comparison

  // Calculate growth (comparing last 7 days to previous 7 days)
  const previousWeekStats = useSessionStats(14);
  const currentWeekHours = stats?.total_hours || 0;
  // Previous week = days 8-14 (subtract current week from 14-day total)
  const previousWeekHours = (previousWeekStats.stats?.total_hours || 0) - currentWeekHours;
  const growth = previousWeekHours > 0 
    ? ((currentWeekHours - previousWeekHours) / previousWeekHours * 100).toFixed(0)
    : currentWeekHours > 0 ? '100' : '0';

  const statsData = [
    {
      label: "Current Streak",
      value: loading ? "..." : (user?.streak?.toString() || "0"),
      unit: "days",
      icon: Flame,
      trend: user?.streak ? `Keep it up!` : "Start your streak today",
      gradient: "from-[#c9f2c7] to-[#aceca1]",
    },
    {
      label: "Study Time",
      value: loading ? "..." : (stats?.total_hours?.toFixed(1) || "0.0"),
      unit: "hours",
      icon: Clock,
      trend: "This week",
      gradient: "from-[#aceca1] to-[#96be8c]",
    },
    {
      label: "Sessions",
      value: loading ? "..." : (stats?.total_sessions?.toString() || "0"),
      unit: "completed",
      icon: Target,
      trend: `This week`,
      gradient: "from-[#96be8c] to-[#629460]",
    },
    {
      label: "Growth",
      value: loading ? "..." : `${growth > 0 ? '+' : ''}${growth}%`,
      unit: "progress",
      icon: TrendingUp,
      trend: "Week over week",
      gradient: "from-[#629460] to-[#243119]",
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {statsData.map((stat) => {
        const Icon = stat.icon
        return (
          <div
            key={stat.label}
            className="group relative overflow-hidden rounded-2xl bg-card border border-border/40 p-6 transition-all hover:shadow-lg hover:shadow-primary/5 hover:border-primary/20"
          >
            {/* Subtle gradient background */}
            <div
              className={`absolute inset-0 bg-gradient-to-br ${stat.gradient} opacity-[0.03] group-hover:opacity-[0.06] transition-opacity`}
            />

            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-2.5 rounded-xl bg-gradient-to-br ${stat.gradient} bg-opacity-10`}>
                  <Icon className="w-5 h-5 text-primary" strokeWidth={2} />
                </div>
              </div>

              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-semibold text-foreground tracking-tight">{stat.value}</p>
                  <span className="text-sm text-muted-foreground">{stat.unit}</span>
                </div>
                <p className="text-xs text-muted-foreground pt-1">{stat.trend}</p>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
