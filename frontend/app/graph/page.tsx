import { Network, Eye } from "lucide-react";
import { EmptyState } from "@/components/empty-state";

export default function GraphPage() {
  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        <div className="mb-8">
          <div className="mb-2 flex items-center gap-2">
            <Eye className="h-6 w-6 text-accent" />
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Knowledge Graph
            </h1>
          </div>
          <p className="text-muted-foreground">
            Interactive visualization of relationships and connections
          </p>
        </div>

        <EmptyState
          icon={Network}
          title="No Graph Data"
          description="Build investigation data to visualize relationships"
        />
      </div>
    </div>
  );
}
