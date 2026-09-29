import { Copy, CheckCircle2 } from "lucide-react";
import { useState } from "react";
import type { ImageResponse } from "@/lib/api-client";

interface ForensicAnalysisProps {
  hashes: {
    md5: string;
    sha1: string;
    sha256: string;
    sha512: string;
  };
  imageData: ImageResponse;
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
              {imageData.filename.split(".").pop()?.toUpperCase()}
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
        <h3 className="mb-3 text-sm font-semibold text-foreground">Validation Status</h3>
        <div className="space-y-2 text-xs">
          <ValidationRow label="File signature" value={imageData.forensic.magic_bytes_validated} />
          <ValidationRow label="Image decoded" value={imageData.forensic.image_decoded} />
          <ValidationRow label="Extension matches content" value={imageData.forensic.extension_match} />
          <div className="flex justify-between">
            <span className="text-muted-foreground">Metadata consistency</span>
            <span className="font-mono text-foreground">{imageData.forensic.metadata_consistency}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function ValidationRow({ label, value }: { label: string; value: boolean | null }) {
  const text = value === true ? "VALIDATED" : value === false ? "FAILED" : "NOT CHECKED";
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono text-foreground">{text}</span>
    </div>
  );
}
