import { Search, Eye } from "lucide-react";
import { EmptyState } from "@/components/empty-state";

export default function ReconPage() {
  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        <div className="mb-8">
          <div className="mb-2 flex items-center gap-2">
            <Eye className="h-6 w-6 text-accent" />
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Recon
            </h1>
          </div>
          <p className="text-muted-foreground">
            OSINT research and public source investigation
          </p>
        </div>

        <EmptyState
          icon={Search}
          title="No Research Performed"
          description="Research clues using publicly available information"
        />
      </div>
    </div>
  );
}
