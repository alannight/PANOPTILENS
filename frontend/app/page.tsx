import { StatsCard } from "@/components/stats-card";
import { AnalysisStatus } from "@/components/analysis-status";
import { RecentFindings } from "@/components/recent-findings";
import { Eye } from "lucide-react";

export default function OverviewPage() {
  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="mb-2 text-3xl font-bold tracking-tight text-foreground">
            Overview
          </h1>
          <p className="text-muted-foreground">
            Intelligence dashboard for case PL-2026-001
          </p>
        </div>

        {/* Case Summary */}
        <div className="mb-8">
          <div className="mb-4 flex items-center gap-2">
            <Eye className="h-5 w-5 text-accent" />
            <h2 className="text-lg font-semibold text-foreground">
              Case Summary
            </h2>
          </div>
          
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            <StatsCard
              label="Case ID"
              value="PL-2026-001"
              mono
            />
            <StatsCard
              label="Status"
              value="ACTIVE"
              variant="success"
            />
            <StatsCard
              label="Images"
              value="1"
              description="DEMO DATA"
            />
            <StatsCard
              label="Metadata Fields"
              value="12"
              description="DEMO DATA"
            />
            <StatsCard
              label="Clues"
              value="3"
              description="DEMO DATA"
            />
            <StatsCard
              label="Evidence"
              value="4"
              description="DEMO DATA"
            />
          </div>
        </div>

        {/* Analysis Status */}
        <div className="mb-8">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-foreground">
              Analysis Status
            </h2>
          </div>
          <AnalysisStatus />
        </div>

        {/* Recent Findings */}
        <div>
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-foreground">
              Recent Findings
            </h2>
          </div>
          <RecentFindings />
        </div>
      </div>
    </div>
  );
}
