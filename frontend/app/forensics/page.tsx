"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, Eye, Fingerprint, Loader2 } from "lucide-react";
import { APIError, getImages, ImageResponse } from "@/lib/api-client";

export default function ForensicsPage() {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getImages()
      .then((items) => { if (active) setImages(items); })
      .catch((cause: unknown) => {
        if (!active) return;
        setError(cause instanceof APIError && cause.status === 0
          ? "Cannot connect to the image service. Check that the backend is running."
          : "Unable to load persisted forensic checks.");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        <header className="mb-8">
          <div className="mb-2 flex items-center gap-2">
            <Eye className="h-6 w-6 text-accent" />
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Forensics</h1>
          </div>
          <p className="text-muted-foreground">File validation and cryptographic identifiers recorded during upload.</p>
        </header>

        {loading ? (
          <div role="status" className="flex items-center gap-2 py-8 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Loading image checks...</div>
        ) : error ? (
          <div role="alert" className="flex items-center gap-2 border border-destructive/40 p-4 text-sm text-destructive"><AlertCircle className="h-4 w-4" />{error}</div>
        ) : images.length === 0 ? (
          <div className="flex min-h-72 flex-col items-center justify-center border border-border bg-card p-8 text-center">
            <Fingerprint className="mb-4 h-10 w-10 text-muted-foreground" />
            <h2 className="mb-2 text-lg font-semibold text-foreground">No images available</h2>
            <p className="mb-4 text-sm text-muted-foreground">Upload an image to record file validation and hashes.</p>
            <Link href="/images" className="text-sm text-accent underline underline-offset-4">Open Images</Link>
          </div>
        ) : (
          <div className="space-y-8">
            {images.map((image) => (
              <section key={image.id} className="border-y border-border py-5">
                <div className="mb-4 flex flex-wrap items-baseline justify-between gap-3">
                  <div>
                    <h2 className="font-mono font-semibold text-foreground">{image.filename}</h2>
                    <p className="text-xs text-muted-foreground">{image.format ?? image.type} · {image.size.toLocaleString()} bytes · {image.metadata.image.width ?? "?"} × {image.metadata.image.height ?? "?"}</p>
                  </div>
                  <Link href={`/images/${image.id}`} className="text-sm text-accent underline underline-offset-4">Open image detail</Link>
                </div>
                <div className="grid gap-6 lg:grid-cols-2">
                  <div>
                    <h3 className="mb-3 text-sm font-semibold text-foreground">Upload-time checks</h3>
                    <div className="space-y-2 text-sm">
                      <StatusRow label="Signature validated" value={image.forensic.magic_bytes_validated} />
                      <StatusRow label="Image decoded" value={image.forensic.image_decoded} />
                      <StatusRow label="Extension matches content" value={image.forensic.extension_match} />
                      <StatusRow label="Metadata extracted" value={image.forensic.metadata_extracted} />
                      <div className="flex justify-between border-b border-border/50 pb-2"><span className="text-muted-foreground">Metadata consistency</span><span className="font-mono">{image.forensic.metadata_consistency}</span></div>
                    </div>
                  </div>
                  <div>
                    <h3 className="mb-3 text-sm font-semibold text-foreground">Cryptographic hashes</h3>
                    <div className="space-y-2 text-xs">
                      {Object.entries(image.hash).map(([name, value]) => (
                        <div key={name} className="grid grid-cols-[4rem_1fr] gap-3 border-b border-border/50 pb-2">
                          <span className="uppercase text-muted-foreground">{name}</span>
                          <span className="break-all font-mono text-foreground">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <p className="mt-5 border-l-2 border-warning px-3 py-2 text-xs text-muted-foreground">
                  Advanced manipulation or authenticity analysis is not implemented. A valid decode and calculated hash do not establish authenticity.
                </p>
              </section>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusRow({ label, value }: { label: string; value: boolean | null }) {
  const result = value === true ? "VALIDATED" : value === false ? "FAILED" : "NOT CHECKED";
  return <div className="flex justify-between border-b border-border/50 pb-2"><span className="text-muted-foreground">{label}</span><span className="font-mono text-foreground">{result}</span></div>;
}