"use client";

import { useEffect, useState } from "react";
import { ImageUpload } from "@/features/images/image-upload";
import { ImageGallery } from "@/features/images/image-gallery";
import { APIError, getImages, ImageResponse } from "@/lib/api-client";
import { AlertCircle, Eye, Loader2 } from "lucide-react";

export default function ImagesPage() {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getImages()
      .then((items) => {
        if (active) setImages(items);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setError(err instanceof APIError && err.status === 0
          ? "Cannot connect to server - is the backend running?"
          : "Unable to load saved images.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  const handleUploadComplete = (imageData: ImageResponse) => {
    setImages((prev) => [imageData, ...prev.filter((image) => image.id !== imageData.id)]);
    setError(null);
  };

  return (
    <div className="h-full overflow-auto">
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="mb-2 flex items-center gap-2">
            <Eye className="h-6 w-6 text-accent" />
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Images
            </h1>
          </div>
          <p className="text-muted-foreground">
            Upload and manage images for forensic analysis
          </p>
        </div>

        {/* Upload Section */}
        <div className="mb-8">
          <ImageUpload onUploadComplete={handleUploadComplete} />
        </div>

        {error && (
          <div role="alert" className="mb-6 flex items-center gap-2 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}

        {/* Image Gallery */}
        {loading ? (
          <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading saved images...
          </div>
        ) : images.length > 0 ? (
          <div>
            <h2 className="mb-4 text-lg font-semibold text-foreground">Saved Images</h2>
            <ImageGallery images={images} />
          </div>
        ) : <p className="text-sm text-muted-foreground">No images uploaded yet.</p>}
      </div>
    </div>
  );
}
