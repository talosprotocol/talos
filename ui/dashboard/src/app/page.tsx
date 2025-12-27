
"use client";

import { useRef } from "react";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { KPIGrid } from "@/components/dashboard/KPIGrid";
import { StatusBanners } from "@/components/dashboard/StatusBanners";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useDataSource } from "@/lib/hooks/useDataSource";
import { Shield } from "lucide-react";

export default function OverviewPage() {
  const { stats, events, loading, hasMore, loadMore, loadingMore } = useDataSource();

  return (
    <main className="min-h-screen bg-[var(--bg)] p-8 font-sans text-zinc-100">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* Header */}
        <header className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[var(--accent)]/10 rounded-lg border border-[var(--accent)]/20">
                <Shield className="w-8 h-8 text-[var(--accent)]" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Security Console</h1>
                <p className="text-zinc-500 text-sm">Talos Protocol v3.0 // Dashboard</p>
              </div>
            </div>
            <StatusBanners />
          </div>
        </header>

        {/* Content */}
        {loading || !stats ? (
          <div className="space-y-6 animate-pulse">
            <GlassPanel className="h-32 w-full bg-zinc-900/50" />
            <GlassPanel className="h-96 w-full bg-zinc-900/50" />
          </div>
        ) : (
          <>
            <KPIGrid stats={stats} />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Main Feed */}
              <div className="lg:col-span-2">
                <ActivityFeed
                  events={events}
                  hasMore={hasMore}
                  onLoadMore={loadMore}
                  isLoading={loadingMore}
                />
              </div>

              {/* Sidebar (Placeholder for charts/filters) */}
              <div className="space-y-6">
                <GlassPanel className="p-4 h-64 flex items-center justify-center text-zinc-600 text-sm border-dashed bg-zinc-900/20">
                  Chart: Denial Taxonomy
                </GlassPanel>
                <GlassPanel className="p-4 h-64 flex items-center justify-center text-zinc-600 text-sm border-dashed bg-zinc-900/20">
                  Chart: Request Volume (24h)
                </GlassPanel>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
