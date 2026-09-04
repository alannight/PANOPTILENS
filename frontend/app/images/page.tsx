"use client";

import { useState } from "react";
import { ImageUpload } from "@/features/images/image-upload";
import { ImageGallery } from "@/features/images/image-gallery";
import { Eye } from "lucide-react";

export default function ImagesPage() {
  const [images, setImages] = useState<any[]>([]);

  const handleUploadComplete = (imageData: any) => {
    setImages((prev) => [...prev, imageData]);
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

        {/* Image Gallery */}
        {images.length > 0 && (
          <div>
            <h2 className="mb-4 text-lg font-semibold text-foreground">
              Uploaded Images
            </h2>
            <ImageGallery images={images} />
          </div>
        )}
      </div>
    </div>
  );
}
