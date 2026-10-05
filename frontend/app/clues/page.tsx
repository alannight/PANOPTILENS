"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, Eye, Lightbulb, Loader2 } from "lucide-react";
import { APIError, getImages, ImageResponse } from "@/lib/api-client";

export default function CluesPage() {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    getImages().then((rows) => { if (active) setImages(rows); })
      .catch((cause: unknown) => { if (active) setError(cause instanceof APIError && cause.status === 0 ? "Cannot connect to the image service." : "Unable to load image observations."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const observations = images.flatMap((image) => {
    const rows: { image: ImageResponse; label: string; value: string; source: string }[] = [];
    const add = (label: string, value: unknown, source: string) => {
      if (value !== null && value !== undefined && String(value).trim()) rows.push({ image, label, value: String(value), source });
    };
    add("Camera make", image.metadata.camera.make, "EXIF Make");
    add("Camera model", image.metadata.camera.model, "EXIF Model");
    add("Lens", image.metadata.camera.lens, "EXIF LensModel");
    add("Software tag", image.metadata.camera.software, "EXIF Software");
    add("Capture time", image.metadata.capture.dateTimeOriginal, "EXIF DateTimeOriginal");
    if (image.metadata.geographic) add("GPS coordinates", `${image.metadata.geographic.latitude}, ${image.metadata.geographic.longitude}`, "EXIF GPS");
    return rows;
  });

  return (
    <div className="h-full overflow-auto"><div className="p-8">
      <header className="mb-8"><div className="mb-2 flex items-center gap-2"><Eye className="h-6 w-6 text-accent" /><h1 className="text-3xl font-bold tracking-tight text-foreground">Clues</h1></div><p className="text-muted-foreground">Observed indicators derived from persisted image metadata. These are not verified conclusions.</p></header>
      {loading ? <div role="status" className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Loading image observations...</div>
        : error ? <div role="alert" className="flex items-center gap-2 text-sm text-destructive"><AlertCircle className="h-4 w-4" />{error}</div>
        : images.length === 0 ? <Empty title="No images available" description="Upload an image to inspect observed metadata indicators." />
        : observations.length === 0 ? <Empty title="No metadata indicators available" description={`${images.length} image${images.length === 1 ? "" : "s"} loaded. No camera, capture-time, or valid GPS tags were extracted from them.`} />
        : <div className="divide-y divide-border border-y border-border">{observations.map((item, index) => <article key={`${item.image.id}-${item.label}-${index}`} className="grid gap-2 py-4 md:grid-cols-[1fr_2fr_1fr] md:items-center"><div><h2 className="text-sm font-medium text-foreground">{item.label}</h2><p className="text-xs text-muted-foreground">{item.source} · Observed, unverified</p></div><p className="break-all font-mono text-sm text-foreground">{item.value}</p><Link href={`/images/${item.image.id}`} className="text-sm text-accent underline underline-offset-4">{item.image.filename}</Link></article>)}</div>}
      <p className="mt-6 text-xs text-muted-foreground">Clue records, confidence scoring, and review workflows are not persisted or implemented yet.</p>
    </div></div>
  );
}

function Empty({ title, description }: { title: string; description: string }) {
  return <div className="flex min-h-64 flex-col items-center justify-center border border-border bg-card p-8 text-center"><Lightbulb className="mb-4 h-10 w-10 text-muted-foreground" /><h2 className="mb-2 text-lg font-semibold text-foreground">{title}</h2><p className="max-w-lg text-sm text-muted-foreground">{description}</p></div>;
}