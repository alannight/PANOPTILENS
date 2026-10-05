"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, Clock, Eye, Loader2 } from "lucide-react";
import { APIError, getImages, ImageResponse } from "@/lib/api-client";

interface EventRow { image: ImageResponse; label: string; source: string; timestamp: string; value: number }

export default function TimelinePage() {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    getImages().then((rows) => { if (active) setImages(rows); })
      .catch((cause: unknown) => { if (active) setError(cause instanceof APIError && cause.status === 0 ? "Cannot connect to the image service." : "Unable to load image timestamps."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const events: EventRow[] = images.flatMap((image) => {
    const rows: EventRow[] = [];
    const capture = image.metadata.capture.dateTimeOriginal;
    if (capture) {
      const parsed = Date.parse(capture.replace(/^(\d{4}):(\d{2}):(\d{2})/, "$1-$2-$3"));
      if (Number.isFinite(parsed)) rows.push({ image, label: "Capture time", source: "EXIF DateTimeOriginal", timestamp: capture, value: parsed });
    }
    const uploaded = Date.parse(image.uploadedAt);
    if (Number.isFinite(uploaded)) rows.push({ image, label: "Uploaded", source: "Application upload timestamp", timestamp: image.uploadedAt, value: uploaded });
    if (image.processedAt) {
      const processed = Date.parse(image.processedAt);
      if (Number.isFinite(processed)) rows.push({ image, label: "Image processed", source: "Application processing timestamp", timestamp: image.processedAt, value: processed });
    }
    if (image.metadataExtractedAt) {
      const extracted = Date.parse(image.metadataExtractedAt);
      if (Number.isFinite(extracted)) rows.push({ image, label: "Metadata extraction completed", source: "Metadata record timestamp", timestamp: image.metadataExtractedAt, value: extracted });
    }
    return rows;
  }).sort((a, b) => a.value - b.value);

  return <div className="h-full overflow-auto"><div className="p-8">
    <header className="mb-8"><div className="mb-2 flex items-center gap-2"><Eye className="h-6 w-6 text-accent" /><h1 className="text-3xl font-bold tracking-tight text-foreground">Timeline</h1></div><p className="text-muted-foreground">Capture and upload timestamps are separate events with explicit sources.</p></header>
    {loading ? <div role="status" className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Loading timestamps...</div>
      : error ? <div role="alert" className="flex items-center gap-2 text-sm text-destructive"><AlertCircle className="h-4 w-4" />{error}</div>
      : images.length === 0 ? <State title="No images available" message="Upload an image to begin a source-based timeline." />
      : events.length === 0 ? <State title="No timeline timestamps available" message={`${images.length} images are stored, but no valid capture, upload, processing, or extraction timestamp was returned.`} />
      : <div className="border-l border-border">{events.map((event, index) => <article key={`${event.image.id}-${event.label}-${index}`} className="relative ml-5 border-b border-border py-4 pl-5"><span className="absolute -left-[1.65rem] top-5 h-3 w-3 rounded-full border-2 border-accent bg-background" /><time className="font-mono text-xs text-muted-foreground">{new Date(event.value).toLocaleString()}</time><h2 className="mt-1 text-sm font-semibold text-foreground">{event.label}</h2><p className="text-xs text-muted-foreground">Source: {event.source}</p><Link href={`/images/${event.image.id}`} className="mt-1 inline-block text-sm text-accent underline underline-offset-4">{event.image.filename}</Link></article>)}</div>}
    <p className="mt-6 text-xs text-muted-foreground">Capture, upload, processing, and metadata extraction are labeled separately. Analyst-created events are not implemented. Capture time is never inferred from upload time.</p>
  </div></div>;
}

function State({ title, message }: { title: string; message: string }) {
  return <div className="flex min-h-64 flex-col items-center justify-center border border-border bg-card p-8 text-center"><Clock className="mb-4 h-10 w-10 text-muted-foreground" /><h2 className="mb-2 text-lg font-semibold text-foreground">{title}</h2><p className="max-w-lg text-sm text-muted-foreground">{message}</p></div>;
}