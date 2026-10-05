"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, Eye, Loader2, Search } from "lucide-react";
import { APIError, getImages, ImageResponse } from "@/lib/api-client";

export default function ReconPage() {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    getImages().then((rows) => { if (active) setImages(rows); })
      .catch((cause: unknown) => { if (active) setError(cause instanceof APIError && cause.status === 0 ? "Cannot connect to the image service." : "Unable to load search indicators."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const indicators = images.flatMap((image) => {
    const values: [string, string | null][] = [
      ["Filename", image.filename], ["Camera make", image.metadata.camera.make],
      ["Camera model", image.metadata.camera.model], ["Software", image.metadata.camera.software],
      ["Capture time", image.metadata.capture.dateTimeOriginal],
      ["GPS coordinates", image.metadata.geographic ? `${image.metadata.geographic.latitude}, ${image.metadata.geographic.longitude}` : null],
    ];
    return values.filter((entry): entry is [string, string] => Boolean(entry[1])).map(([kind, value]) => ({ image, kind, value }));
  });

  return <div className="h-full overflow-auto"><div className="p-8">
    <header className="mb-8"><div className="mb-2 flex items-center gap-2"><Eye className="h-6 w-6 text-accent" /><h1 className="text-3xl font-bold tracking-tight text-foreground">Recon</h1></div><p className="text-muted-foreground">Search-ready indicators from stored image records. No automated OSINT queries are performed.</p></header>
    {loading ? <div role="status" className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Loading indicators...</div>
      : error ? <div role="alert" className="flex items-center gap-2 text-sm text-destructive"><AlertCircle className="h-4 w-4" />{error}</div>
      : images.length === 0 ? <State title="No images available" message="Upload an image before preparing research indicators." />
      : indicators.length === 0 ? <State title="No search indicators available" message={`${images.length} images loaded. Their stored metadata has no camera, capture-time, or GPS indicators.`} />
      : <div className="divide-y divide-border border-y border-border">{indicators.map(({ image, kind, value }, index) => <div key={`${image.id}-${kind}-${index}`} className="grid gap-2 py-4 md:grid-cols-[9rem_1fr_auto_auto] md:items-center"><span className="text-xs text-muted-foreground">{kind}</span><span className="break-all font-mono text-sm text-foreground">{value}</span><Link href={`/images/${image.id}`} className="text-sm text-accent underline underline-offset-4">{image.filename}</Link><a href={`https://www.google.com/search?q=${encodeURIComponent(value)}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-sm text-muted-foreground underline underline-offset-4"><Search className="h-3.5 w-3.5" />Search</a></div>)}</div>}
    <p className="mt-6 text-xs text-muted-foreground">External search opens only after you select a link. Search providers receive the selected indicator.</p>
  </div></div>;
}

function State({ title, message }: { title: string; message: string }) {
  return <div className="flex min-h-64 flex-col items-center justify-center border border-border bg-card p-8 text-center"><Search className="mb-4 h-10 w-10 text-muted-foreground" /><h2 className="mb-2 text-lg font-semibold text-foreground">{title}</h2><p className="max-w-lg text-sm text-muted-foreground">{message}</p></div>;
}