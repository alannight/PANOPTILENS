import Link from "next/link";
import { formatBytes } from "@/lib/utils";
import { ExternalLink, Hash } from "lucide-react";

interface ImageGalleryProps {
  images: any[];
}

export function ImageGallery({ images }: ImageGalleryProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {images.map((image) => (
        <Link
          key={image.id}
          href={`/images/${image.id}`}
          className="group relative overflow-hidden rounded-lg border border-border bg-card transition-all hover:border-accent"
        >
          <div className="aspect-video overflow-hidden bg-secondary">
            <img
              src={image.url}
              alt={image.filename}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
            />
          </div>
          
          <div className="p-4">
            <div className="mb-2 flex items-start justify-between gap-2">
              <h3 className="truncate font-semibold text-foreground">
                {image.filename}
              </h3>
              <ExternalLink className="h-4 w-4 flex-shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
            </div>
            
            <div className="space-y-1 text-xs text-muted-foreground">
              <div className="flex justify-between">
                <span>Size</span>
                <span className="font-mono">{formatBytes(image.size)}</span>
              </div>
              <div className="flex justify-between">
                <span>Type</span>
                <span className="font-mono uppercase">{image.type.split("/")[1]}</span>
              </div>
              <div className="mt-2 flex items-center gap-1">
                <Hash className="h-3 w-3" />
                <span className="font-mono text-[10px]">
                  {image.hash.sha256.slice(0, 16)}...
                </span>
              </div>
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
