"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, Eye, Loader2, Shield } from "lucide-react";
import { APIError, getImages, ImageResponse } from "@/lib/api-client";

export default function EvidencePage() {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    getImages().then((rows) => { if (active) setImages(rows); })
      .catch((cause: unknown) => { if (active) setError(cause instanceof APIError && cause.status === 0 ? "Cannot connect to the image service." : "Unable to load stored image records."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  return <div className="h-full overflow-auto"><div className="p-8">
    <header className="mb-8"><div className="mb-2 flex items-center gap-2"><Eye className="h-6 w-6 text-accent" /><h1 className="text-3xl font-bold tracking-tight text-foreground">Evidence Sources</h1></div><p className="text-muted-foreground">Stored uploaded images and hashes. These are source records, not formal case EvidenceItems.</p></header>
    {loading ? <div role="status" className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Loading image records...</div>
      : error ? <div role="alert" className="flex items-center gap-2 text-sm text-destructive"><AlertCircle className="h-4 w-4" />{error}</div>
      : images.length === 0 ? <div className="flex min-h-64 flex-col items-center justify-center border border-border bg-card p-8 text-center"><Shield className="mb-4 h-10 w-10 text-muted-foreground" /><h2 className="mb-2 text-lg font-semibold text-foreground">No image source records</h2><p className="mb-4 text-sm text-muted-foreground">Upload an image to add a source record.</p><Link href="/images" className="text-sm text-accent underline underline-offset-4">Open Images</Link></div>
      : <div className="divide-y divide-border border-y border-border">{images.map((image) => <article key={image.id} className="grid gap-3 py-4 md:grid-cols-[1fr_1.5fr_auto] md:items-center"><div><Link href={`/images/${image.id}`} className="font-medium text-accent underline underline-offset-4">{image.filename}</Link><p className="text-xs text-muted-foreground">Stored original · {image.format ?? image.type} · {image.size.toLocaleString()} bytes</p></div><div><p className="text-xs text-muted-foreground">SHA-256</p><p className="break-all font-mono text-xs text-foreground">{image.hash.sha256}</p></div><time className="text-xs text-muted-foreground">Uploaded {new Date(image.uploadedAt).toLocaleString()}</time></article>)}</div>}
    <p className="mt-6 text-xs text-muted-foreground">Formal evidence collection, case association, acquisition notes, and review status are not implemented.</p>
  </div></div>;
}