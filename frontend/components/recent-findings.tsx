import { MapPin, FileText, Eye, Hash } from "lucide-react";

const findings = [
  {
    time: "10:42",
    message: "GPS metadata detected",
    type: "geographic",
    icon: MapPin,
  },
  {
    time: "10:42",
    message: "EXIF data extracted successfully",
    type: "metadata",
    icon: FileText,
  },
  {
    time: "10:43",
    message: "OCR detected location-related text",
    type: "visual",
    icon: Eye,
  },
  {
    time: "10:42",
    message: "Cryptographic hashes calculated",
    type: "forensic",
    icon: Hash,
  },
];

export function RecentFindings() {
  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="divide-y divide-border">
        {findings.map((finding, index) => (
          <div
            key={index}
            className="flex items-center gap-4 p-4 transition-colors hover:bg-secondary/50"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-secondary">
              <finding.icon className="h-5 w-5 text-accent" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground">
                {finding.message}
              </p>
              <p className="text-xs text-muted-foreground">
                Source: {finding.type}
              </p>
            </div>
            <div className="font-mono text-sm text-muted-foreground">
              {finding.time}
            </div>
          </div>
        ))}
      </div>
      
      {findings.length === 0 && (
        <div className="p-8 text-center text-sm text-muted-foreground">
          No findings have been recorded yet.
        </div>
      )}
    </div>
  );
}
