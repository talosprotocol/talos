"use client";

import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { KPIGrid } from "@/components/dashboard/KPIGrid";
import { StatusBanners } from "@/components/dashboard/StatusBanners";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { TalosLogo } from "@/components/ui/TalosLogo";

import { ThemeToggle } from "@/components/ThemeToggle";
import { useDataSource } from "@/lib/hooks/useDataSource";

export default function OverviewPage() {
  const { stats, events, loading, hasMore, loadMore, loadingMore } = useDataSource();

  return (
    <main className="min-h-screen bg-[var(--bg)] p-8 font-sans text-[var(--text-primary)]">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* Header */}
        <header className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[var(--accent)]/10 rounded-lg border border-[var(--accent)]/20 shadow-sm">
                <TalosLogo className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Security Console</h1>
                <p className="text-[var(--text-muted)] text-sm">Talos Protocol v3.0 // Dashboard</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <StatusBanners />
              <ThemeToggle />
            </div>
          </div>
        </header>

        {/* Content */}
        {loading || !stats ? (
          <div className="space-y-6 animate-pulse">
            <GlassPanel className="h-32 w-full bg-[var(--panel)]" />
            <GlassPanel className="h-96 w-full bg-[var(--panel)]" />
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
                <GlassPanel className="p-4 h-64 flex items-center justify-center text-[var(--text-muted)] text-sm border-dashed bg-[var(--glass-border)]/10">
                  Chart: Denial Taxonomy
                </GlassPanel>
                <GlassPanel className="p-4 h-64 flex items-center justify-center text-[var(--text-muted)] text-sm border-dashed bg-[var(--glass-border)]/10">
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
