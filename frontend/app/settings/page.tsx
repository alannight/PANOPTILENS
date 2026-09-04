import { Settings as SettingsIcon, Eye } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        <div className="mb-8">
          <div className="mb-2 flex items-center gap-2">
            <Eye className="h-6 w-6 text-accent" />
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Settings
            </h1>
          </div>
          <p className="text-muted-foreground">
            Application settings and preferences
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            Application Info
          </h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between border-b border-border pb-2">
              <span className="text-muted-foreground">Version</span>
              <span className="font-mono text-foreground">0.1.0</span>
            </div>
            <div className="flex justify-between border-b border-border pb-2">
              <span className="text-muted-foreground">Build</span>
              <span className="font-mono text-foreground">DEMO</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Status</span>
              <span className="font-mono text-success">ACTIVE</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
