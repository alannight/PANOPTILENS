import { Fingerprint, Eye } from "lucide-react";

export default function ForensicsPage() {
  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        <div className="mb-8">
          <div className="mb-2 flex items-center gap-2">
            <Eye className="h-6 w-6 text-accent" />
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Forensics
            </h1>
          </div>
          <p className="text-muted-foreground">
            Technical forensic analysis and file structure examination
          </p>
        </div>

        <div className="flex min-h-[400px] items-center justify-center rounded-lg border border-border bg-card">
          <div className="text-center">
            <Fingerprint className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
            <h3 className="mb-2 text-lg font-semibold text-foreground">
              No Forensic Analysis Available
            </h3>
            <p className="text-sm text-muted-foreground">
              Upload an image to perform forensic analysis
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
