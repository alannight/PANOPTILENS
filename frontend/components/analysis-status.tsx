import { CheckCircle2, Clock, XCircle } from "lucide-react";

const analysisModules = [
  {
    name: "Metadata",
    status: "completed",
    findings: 12,
    lastAnalyzed: "2026-09-01 10:42",
  },
  {
    name: "File Forensics",
    status: "completed",
    findings: 5,
    lastAnalyzed: "2026-09-01 10:42",
  },
  {
    name: "OCR",
    status: "completed",
    findings: 3,
    lastAnalyzed: "2026-09-01 10:43",
  },
  {
    name: "Visual Analysis",
    status: "completed",
    findings: 2,
    lastAnalyzed: "2026-09-01 10:43",
  },
  {
    name: "Geographic Analysis",
    status: "completed",
    findings: 1,
    lastAnalyzed: "2026-09-01 10:42",
  },
  {
    name: "OSINT Research",
    status: "pending",
    findings: 0,
    lastAnalyzed: null,
  },
];

export function AnalysisStatus() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {analysisModules.map((module) => (
        <div
          key={module.name}
          className="rounded-lg border border-border bg-card p-4"
        >
          <div className="mb-3 flex items-start justify-between">
            <h3 className="font-semibold text-foreground">{module.name}</h3>
            {module.status === "completed" && (
              <CheckCircle2 className="h-5 w-5 text-success" />
            )}
            {module.status === "pending" && (
              <Clock className="h-5 w-5 text-muted-foreground" />
            )}
            {module.status === "failed" && (
              <XCircle className="h-5 w-5 text-destructive" />
            )}
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Findings</span>
              <span className="font-mono font-medium text-foreground">
                {module.findings}
              </span>
            </div>
            
            {module.lastAnalyzed && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Last Analyzed</span>
                <span className="font-mono text-xs text-muted-foreground">
                  {module.lastAnalyzed}
                </span>
              </div>
            )}
            
            {!module.lastAnalyzed && (
              <div className="text-sm text-muted-foreground">
                Not analyzed yet
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
