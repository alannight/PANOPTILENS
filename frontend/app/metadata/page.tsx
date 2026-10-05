"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, Eye, FileText, Loader2 } from "lucide-react";
import { APIError, getImages, ImageResponse } from "@/lib/api-client";
import { ImageMetadata } from "@/features/images/image-metadata";
import { ForensicAnalysis } from "@/features/images/forensic-analysis";

export default function MetadataPage() {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const selectedImage = images.find((image) => image.id === selectedId) ?? null;

  useEffect(() => {
    let active = true;
    getImages()
      .then((items) => {
        if (!active) return;
        setImages(items);
        setSelectedId((current) => current || items[0]?.id || "");
      })
      .catch((cause: unknown) => {
        if (!active) return;
        setError(cause instanceof APIError && cause.status === 0
          ? "Cannot connect to the image service. Check that the backend is running."
          : "Unable to load saved image metadata. Retry the request.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  function retry() {
    setLoading(true);
    setError(null);
    getImages()
      .then((items) => {
        setImages(items);
        setSelectedId((current) => items.some((image) => image.id === current) ? current : items[0]?.id || "");
      })
      .catch(() => setError("Unable to load saved image metadata. Retry the request."))
      .finally(() => setLoading(false));
  }

  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        <header className="mb-8">
          <div className="mb-2 flex items-center gap-2">
            <Eye className="h-6 w-6 text-accent" />
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Metadata</h1>
          </div>
          <p className="text-muted-foreground">Inspect metadata already extracted and stored for uploaded images.</p>
        </header>

        {loading ? (
          <div role="status" className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading saved images...
          </div>
        ) : error ? (
          <div role="alert" className="flex items-start gap-3 border border-destructive/40 bg-destructive/5 p-4 text-sm">
            <AlertCircle className="mt-0.5 h-4 w-4 text-destructive" />
            <div className="space-y-2">
              <p className="text-foreground">{error}</p>
              <button onClick={retry} className="text-accent underline underline-offset-4">Retry</button>
            </div>
          </div>
        ) : images.length === 0 ? (
          <div className="flex min-h-72 flex-col items-center justify-center border border-border bg-card p-8 text-center">
            <FileText className="mb-4 h-10 w-10 text-muted-foreground" />
            <h2 className="mb-2 text-lg font-semibold text-foreground">No images available</h2>
            <p className="mb-4 max-w-md text-sm text-muted-foreground">Upload an image from the Images page to begin metadata analysis.</p>
            <Link href="/images" className="text-sm text-accent underline underline-offset-4">Open Images</Link>
          </div>
        ) : selectedImage ? (
          <>
            <div className="mb-6 grid gap-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
              <label className="block text-sm font-medium text-foreground">
                Select image
                <select
                  value={selectedImage.id}
                  onChange={(event) => setSelectedId(event.target.value)}
                  className="mt-2 block h-11 w-full border border-border bg-card px-3 font-mono text-sm text-foreground"
                >
                  {images.map((image) => (
                    <option key={image.id} value={image.id}>{image.filename}</option>
                  ))}
                </select>
              </label>
              <Link href={`/images/${selectedImage.id}`} className="text-sm text-accent underline underline-offset-4">
                Open image detail
              </Link>
            </div>

            <section className="mb-6 border-y border-border py-5">
              <h2 className="mb-4 text-lg font-semibold text-foreground">File information</h2>
              <div className="grid gap-x-8 gap-y-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
                <SummaryField label="Filename" value={selectedImage.filename} />
                <SummaryField label="Format" value={selectedImage.format ?? selectedImage.type} />
                <SummaryField label="File size" value={`${selectedImage.size.toLocaleString()} bytes`} />
                <SummaryField label="Dimensions" value={selectedImage.metadata.image.width && selectedImage.metadata.image.height ? `${selectedImage.metadata.image.width} × ${selectedImage.metadata.image.height}` : null} />
              </div>
            </section>

            <div className="grid gap-6 xl:grid-cols-2">
              <ForensicAnalysis hashes={selectedImage.hash} imageData={selectedImage} />
              <ImageMetadata metadata={selectedImage.metadata} />
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}

function SummaryField({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="min-w-0">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="break-all font-mono text-foreground">{value ?? "Not available"}</p>
    </div>
  );
}