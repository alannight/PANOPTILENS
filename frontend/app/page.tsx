"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, Eye, FileText, Image as ImageIcon, Loader2, MapPin } from "lucide-react";
import { APIError, getImages, ImageResponse } from "@/lib/api-client";

export default function OverviewPage() {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    getImages().then((rows) => { if (active) setImages(rows); })
      .catch((cause: unknown) => { if (active) setError(cause instanceof APIError && cause.status === 0 ? "Cannot connect to the image service." : "Unable to load image summary."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  const metadataCount = images.filter((image) => image.metadata.status === "PRESENT").length;
  const gpsCount = images.filter((image) => image.metadata.geographic !== null).length;

  return <div className="h-full overflow-auto"><div className="p-8">
    <header className="mb-8"><h1 className="mb-2 text-3xl font-bold tracking-tight text-foreground">Overview</h1><p className="text-muted-foreground">Summary from persisted image records and investigation cases.</p></header>
    {loading ? <div role="status" className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Loading saved images...</div>
      : error ? <div role="alert" className="flex items-center gap-2 text-sm text-destructive"><AlertCircle className="h-4 w-4" />{error}</div>
      : <>
        <div className="mb-8 grid gap-5 border-y border-border py-5 sm:grid-cols-3">
          <Metric icon={ImageIcon} label="Stored images" value={images.length} />
          <Metric icon={FileText} label="EXIF present" value={metadataCount} />
          <Metric icon={MapPin} label="Valid GPS" value={gpsCount} />
        </div>
        {images.length === 0 ? <div className="border border-border bg-card p-6 text-sm text-muted-foreground">No saved image records. <Link href="/images" className="text-accent underline underline-offset-4">Upload an image</Link> to begin.</div>
          : <section><div className="mb-4 flex items-center gap-2"><Eye className="h-5 w-5 text-accent" /><h2 className="text-lg font-semibold text-foreground">Recent image records</h2></div><div className="divide-y divide-border border-y border-border">{images.slice(0, 5).map((image) => <div key={image.id} className="grid gap-2 py-4 sm:grid-cols-[1fr_auto_auto] sm:items-center"><div><Link href={`/images/${image.id}`} className="font-medium text-accent underline underline-offset-4">{image.filename}</Link><p className="text-xs text-muted-foreground">{image.format ?? image.type} · {image.size.toLocaleString()} bytes</p></div><span className="text-xs text-muted-foreground">EXIF {image.metadata.status}</span><time className="text-xs text-muted-foreground">{new Date(image.uploadedAt).toLocaleString()}</time></div>)}</div></section>}
        <p className="mt-8 text-xs text-muted-foreground">OCR, clue review, case findings, and formal evidence workflows are not implemented.</p>
      </>}
  </div></div>;
}

function Metric({ icon: Icon, label, value }: { icon: typeof ImageIcon; label: string; value: number }) {
  return <div className="flex items-center gap-3"><Icon className="h-5 w-5 text-accent" /><div><p className="text-xs text-muted-foreground">{label}</p><p className="font-mono text-2xl font-semibold text-foreground">{value}</p></div></div>;
}