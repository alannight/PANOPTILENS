"use client";

import { MapPin, AlertCircle } from "lucide-react";

interface LocationMapProps {
  latitude: number;
  longitude: number;
  altitude?: number;
}

export function LocationMap({ latitude, longitude, altitude }: LocationMapProps) {
  // Generate static map URL (using OpenStreetMap-based service)
  const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${longitude - 0.01},${latitude - 0.01},${longitude + 0.01},${latitude + 0.01}&layer=mapnik&marker=${latitude},${longitude}`;
  
  const osmLink = `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=15/${latitude}/${longitude}`;
  
  return (
    <div className="space-y-4">
      {/* Map Display */}
      <div className="overflow-hidden rounded-lg border border-border bg-secondary">
        <iframe
          width="100%"
          height="400"
          frameBorder="0"
          scrolling="no"
          src={mapUrl}
          className="w-full"
          title="Location Map"
        />
      </div>

      {/* Coordinates Display */}
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="mb-3 flex items-center gap-2">
          <MapPin className="h-5 w-5 text-accent" />
          <h3 className="font-semibold text-foreground">Coordinates</h3>
        </div>
        
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Latitude</span>
            <span className="font-mono text-foreground">
              {latitude.toFixed(6)}°
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Longitude</span>
            <span className="font-mono text-foreground">
              {longitude.toFixed(6)}°
            </span>
          </div>
          {altitude !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Altitude</span>
              <span className="font-mono text-foreground">{altitude}m</span>
            </div>
          )}
        </div>

        <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
          <a
            href={osmLink}
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            View on OpenStreetMap ↗
          </a>
        </div>
      </div>

      {/* Attribution Notice */}
      <div className="rounded-md border border-warning/50 bg-warning/10 p-3">
        <div className="flex items-start gap-2">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-warning" />
          <div className="text-xs text-foreground/90">
            <strong>Location derived from image metadata.</strong> GPS coordinates
            can be altered or removed. This does not confirm the actual capture
            location.
          </div>
        </div>
      </div>
    </div>
  );
}
