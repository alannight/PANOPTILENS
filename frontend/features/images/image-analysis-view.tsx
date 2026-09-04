"use client";

import { useState, useEffect } from "react";
import { Eye, ArrowLeft, MapPin, Loader2, AlertCircle } from "lucide-react";
import Link from "next/link";
import { ImageMetadata } from "./image-metadata";
import { ForensicAnalysis } from "./forensic-analysis";
import { LocationMap } from "@/components/location-map";
import { getImage, ImageResponse, APIError } from "@/lib/api-client";

interface ImageAnalysisViewProps {
  imageId: string;
}

export function ImageAnalysisView({ imageId }: ImageAnalysisViewProps) {
  const [imageData, setImageData] = useState<ImageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function fetchImage() {
      try {
        setLoading(true);
        setError(null);
        
        const data = await getImage(imageId);
        
        if (mounted) {
          setImageData(data);
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

        {/* Split View */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Left: Image Preview */}
          <div>
            <div className="sticky top-8">
              <div className="overflow-hidden rounded-lg border border-border bg-card">
                <div className="aspect-[4/3] overflow-hidden bg-secondary">
                  <img
                    src={imageData.url}
                    alt={imageData.filename}
                    className="h-full w-full object-contain"
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
                  altitude={imageData.metadata.geographic.altitude}
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
