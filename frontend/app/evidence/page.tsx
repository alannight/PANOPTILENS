import { Shield, Eye } from "lucide-react";
import { EmptyState } from "@/components/empty-state";

export default function EvidencePage() {
  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        <div className="mb-8">
          <div className="mb-2 flex items-center gap-2">
            <Eye className="h-6 w-6 text-accent" />
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Evidence
            </h1>
          </div>
          <p className="text-muted-foreground">
            Evidence repository with source attribution
          </p>
        </div>

        <EmptyState
          icon={Shield}
          title="No Evidence Collected"
          description="No evidence has been attached to this case"
        />
      </div>
    </div>
  );
}
