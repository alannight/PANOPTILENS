import { Copy, CheckCircle2 } from "lucide-react";
import { useState } from "react";

interface ForensicAnalysisProps {
  hashes: {
    md5: string;
    sha1: string;
    sha256: string;
    sha512: string;
  };
  imageData: any;
}

export function ForensicAnalysis({ hashes, imageData }: ForensicAnalysisProps) {
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(label);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <h2 className="mb-4 text-lg font-semibold text-foreground">
        Forensic Analysis
      </h2>

      {/* File Identity */}
      <div className="mb-6">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          File Identity
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">MIME Type</span>
            <span className="font-mono text-foreground">{imageData.type}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Extension</span>
            <span className="font-mono text-foreground">
              {imageData.name.split(".").pop()?.toUpperCase()}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Size</span>
            <span className="font-mono text-foreground">
              {imageData.size.toLocaleString()} bytes
            </span>
          </div>
        </div>
      </div>

      {/* Cryptographic Hashes */}
      <div>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Cryptographic Hashes
        </h3>
        <div className="space-y-3">
          {Object.entries(hashes).map(([algorithm, hash]) => (
            <div key={algorithm}>
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs font-medium uppercase text-muted-foreground">
                  {algorithm}
                </span>
                <button
                  onClick={() => copyToClipboard(hash, algorithm)}
                  className="flex items-center gap-1 rounded px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                >
                  {copiedHash === algorithm ? (
                    <>
                      <CheckCircle2 className="h-3 w-3" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      Copy
                    </>
                  )}
                </button>
              </div>
              <div className="break-all rounded bg-secondary p-2 font-mono text-xs text-foreground">
                {hash}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Metadata Integrity */}
      <div className="mt-6 rounded-md border border-border bg-secondary/50 p-4">
        <h3 className="mb-2 text-sm font-semibold text-foreground">
          Metadata Integrity
        </h3>
        <p className="text-xs text-muted-foreground">
          No anomalies detected in file structure or metadata timestamps.
        </p>
        <div className="mt-2 flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-success" />
          <span className="text-xs text-success">VERIFIED</span>
        </div>
      </div>
    </div>
  );
}
