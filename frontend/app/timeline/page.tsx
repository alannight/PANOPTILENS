import { Clock, Eye } from "lucide-react";
import { EmptyState } from "@/components/empty-state";

export default function TimelinePage() {
  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        <div className="mb-8">
          <div className="mb-2 flex items-center gap-2">
            <Eye className="h-6 w-6 text-accent" />
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Timeline
            </h1>
          </div>
          <p className="text-muted-foreground">
            Chronological investigation timeline and event correlation
          </p>
        </div>

        <EmptyState
          icon={Clock}
          title="No Timeline Events"
          description="Timeline will be built from image metadata and investigation events"
        />
      </div>
    </div>
  );
}
