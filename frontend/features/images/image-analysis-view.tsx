"use client";

import { useState, useEffect } from "react";
import { Eye, ArrowLeft, MapPin, Loader2, AlertCircle, Download, Save, ShieldCheck, ShieldAlert, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ImageMetadata } from "./image-metadata";
import { ForensicAnalysis } from "./forensic-analysis";
import { LocationMap } from "@/components/location-map";
import {
  APIError,
  deleteImage,
  getImage,
  imageReportUrl,
  ImageResponse,
  IntegrityVerification,
  updateImageAnnotations,
  verifyImageIntegrity,
} from "@/lib/api-client";
import { getExifOrientationStyle } from "./image-orientation";

interface ImageAnalysisViewProps {
  imageId: string;
}

export function ImageAnalysisView({ imageId }: ImageAnalysisViewProps) {
  const router = useRouter();
  const [imageData, setImageData] = useState<ImageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [tags, setTags] = useState("");
  const [savingAnnotations, setSavingAnnotations] = useState(false);
  const [integrity, setIntegrity] = useState<IntegrityVerification | null>(null);
  const [integrityError, setIntegrityError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function fetchImage() {
      try {
        setLoading(true);
        setError(null);
        
        const data = await getImage(imageId);
        
        if (mounted) {
          setImageData(data);
          setNotes(data.analystNotes ?? "");
          setTags((data.tags ?? []).join(", "));
          setLoading(false);
        }
      } catch (err) {
        if (!mounted) return;
        
        if (err instanceof APIError) {
          if (err.status === 404) {
            setError("Image not found");
          } else if (err.status === 0) {
            setError("Cannot connect to server - is the backend running?");
          } else {
            setError(err.message || "Failed to load image");
          }
        } else {
          setError("An unexpected error occurred");
        }
        setLoading(false);
      }
    }

    fetchImage();

    return () => {
      mounted = false;
    };
  }, [imageId]);

  const saveAnnotations = async () => {
    setSavingAnnotations(true);
    try {
      const updated = await updateImageAnnotations(imageId, {
        tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean),
        analystNotes: notes,
      });
      setImageData((current) => current ? { ...current, ...updated } : current);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save annotations.");
    } finally {
      setSavingAnnotations(false);
    }
  };

  const checkIntegrity = async () => {
    setIntegrityError(null);
    try {
      setIntegrity(await verifyImageIntegrity(imageId));
    } catch (err) {
      setIntegrityError(err instanceof Error ? err.message : "Integrity check failed.");
    }
  };

  const moveToTrash = async () => {
    if (!window.confirm("Move this image to Trash? It can be restored later.")) return;
    try {
      await deleteImage(imageId);
      router.push("/images");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to move image to Trash.");
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-12 w-12 animate-spin text-accent" />
          <p className="mt-4 text-sm text-muted-foreground">Loading image analysis...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !imageData) {
    return (
      <div className="h-full overflow-auto">
        <div className="p-8">
          <Link
            href="/images"
            className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Images
          </Link>

          <div className="flex min-h-[400px] items-center justify-center rounded-lg border border-border bg-card">
            <div className="text-center">
              <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
              <h3 className="mt-4 text-lg font-semibold text-foreground">
                {error || "Image not found"}
              </h3>
              <p className="mt-2 text-sm text-muted-foreground">
                The requested image could not be loaded.
              </p>
              <Link
                href="/images"
                className="mt-4 inline-block text-sm text-accent hover:underline"
              >
                Return to image gallery
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Success state with real data
  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        {/* Back Button */}
        <Link
          href="/images"
          className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Images
        </Link>

        {/* Header */}
        <div className="mb-8">
          <div className="mb-2 flex items-center gap-2">
            <Eye className="h-6 w-6 text-accent" />
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Image Analysis
            </h1>
          </div>
          <p className="font-mono text-sm text-muted-foreground">
            {imageData.filename}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            ID: <span className="font-mono">{imageData.id}</span>
          </p>
        </div>

        {error && <p role="alert" className="mb-4 text-sm text-destructive">{error}</p>}
        <div className="mb-6 flex flex-wrap items-center gap-3 border-y border-border py-4">
          <button type="button" onClick={checkIntegrity} className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm hover:bg-secondary">
            <ShieldCheck className="h-4 w-4" /> Verify Integrity
          </button>
          <a href={imageReportUrl(imageData.id)} className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm hover:bg-secondary">
            <Download className="h-4 w-4" /> Export JSON
          </a>
          <button type="button" onClick={moveToTrash} className="inline-flex items-center gap-2 rounded-md border border-destructive/50 px-3 py-2 text-sm text-destructive hover:bg-destructive/10">
            <Trash2 className="h-4 w-4" /> Move to Trash
          </button>
          {integrity && (
            <div className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium ${integrity.status === "VERIFIED" ? "bg-success/15 text-success" : integrity.status === "TAMPERED" || integrity.status === "MISSING" ? "bg-destructive/15 text-destructive" : "bg-warning/15 text-warning"}`}>
              {integrity.status === "VERIFIED" ? <ShieldCheck className="h-4 w-4" /> : <ShieldAlert className="h-4 w-4" />}
              {integrity.status === "VERIFIED" ? "Verified / Intact" : integrity.status === "TAMPERED" ? "Tampered / Corrupted" : integrity.status}
            </div>
          )}
          {integrityError && <span role="alert" className="text-sm text-destructive">{integrityError}</span>}
        </div>

        {/* Split View */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Left: Image Preview */}
          <div>
            <div className="sticky top-8">
              <div className="overflow-hidden rounded-lg border border-border bg-card">
                <div className="aspect-[4/3] overflow-hidden bg-secondary">
                  <img
                    src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${imageData.url}`}
                    alt={imageData.filename}
                    className="h-full w-full object-contain"
                    style={getExifOrientationStyle(imageData.metadata.image.orientation)}
                  />
                </div>
                <div className="border-t border-border p-4">
                  <h3 className="mb-3 font-semibold text-foreground">
                    File Information
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">File Name</span>
                      <span className="font-mono text-foreground">
                        {imageData.filename}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">File Type</span>
                      <span className="font-mono text-foreground">
                        {imageData.type}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">File Size</span>
                      <span className="font-mono text-foreground">
                        {(imageData.size / 1024 / 1024).toFixed(2)} MB
                      </span>
                    </div>
                    {imageData.metadata.image.width && imageData.metadata.image.height && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Dimensions</span>
                        <span className="font-mono text-foreground">
                          {imageData.metadata.image.width} × {imageData.metadata.image.height}
                        </span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Uploaded</span>
                      <span className="font-mono text-xs text-foreground">
                        {new Date(imageData.uploadedAt).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Analysis Tabs */}
          <div className="space-y-6">
            <section className="rounded-lg border border-border bg-card p-6">
              <h2 className="mb-4 text-lg font-semibold text-foreground">Analyst Annotations</h2>
              <label htmlFor="image-tags" className="mb-2 block text-sm text-muted-foreground">Tags, comma separated</label>
              <input
                id="image-tags"
                value={tags}
                onChange={(event) => setTags(event.target.value)}
                className="mb-4 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
                placeholder="suspicious, network"
              />
              <label htmlFor="analyst-notes" className="mb-2 block text-sm text-muted-foreground">Findings and notes</label>
              <textarea
                id="analyst-notes"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                rows={5}
                className="w-full resize-y rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
                placeholder="Record observations for this evidence item"
              />
              <div className="mt-4 flex justify-end">
                <button type="button" onClick={saveAnnotations} disabled={savingAnnotations} className="inline-flex items-center gap-2 rounded-md bg-accent px-3 py-2 text-sm text-accent-foreground disabled:opacity-60">
                  <Save className="h-4 w-4" /> {savingAnnotations ? "Saving..." : "Save Annotations"}
                </button>
              </div>
            </section>
            <ForensicAnalysis hashes={imageData.hash} imageData={imageData} />
            
            {/* GPS Location Map */}
            {imageData.metadata.geographic && (
              <div className="rounded-lg border border-border bg-card p-6">
                <div className="mb-4 flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-accent" />
                  <h2 className="text-lg font-semibold text-foreground">
                    Geographic Location
                  </h2>
                </div>
                <LocationMap
                  latitude={imageData.metadata.geographic.latitude}
                  longitude={imageData.metadata.geographic.longitude}
                  altitude={imageData.metadata.geographic.altitude ?? undefined}
                />
              </div>
            )}
            
            <ImageMetadata metadata={imageData.metadata} />
          </div>
        </div>
      </div>
    </div>
  );
}
