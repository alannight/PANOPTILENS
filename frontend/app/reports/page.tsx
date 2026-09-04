import { FileBarChart, Eye } from "lucide-react";
import { EmptyState } from "@/components/empty-state";

export default function ReportsPage() {
  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        <div className="mb-8">
          <div className="mb-2 flex items-center gap-2">
            <Eye className="h-6 w-6 text-accent" />
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Reports
            </h1>
          </div>
          <p className="text-muted-foreground">
            Investigation reports and exports
          </p>
        </div>

        <EmptyState
          icon={FileBarChart}
          title="No Reports Generated"
          description="Generate comprehensive investigation reports from case data"
        />
      </div>
    </div>
  );
}
