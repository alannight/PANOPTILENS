import { Lightbulb, Eye } from "lucide-react";
import { EmptyState } from "@/components/empty-state";

export default function CluesPage() {
  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        <div className="mb-8">
          <div className="mb-2 flex items-center gap-2">
            <Eye className="h-6 w-6 text-accent" />
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Clues
            </h1>
          </div>
          <p className="text-muted-foreground">
            Investigation clues extracted from images and metadata
          </p>
        </div>

        <EmptyState
          icon={Lightbulb}
          title="No Investigation Clues"
          description="No investigation clues have been extracted yet"
        />
      </div>
    </div>
  );
}
