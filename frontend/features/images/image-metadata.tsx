import { MapPin, Camera, Image as ImageIcon, Calendar, AlertTriangle } from "lucide-react";
import type { ImageMetadata as ImageMetadataType } from "@/lib/api-client";

interface ImageMetadataProps {
  metadata: ImageMetadataType;
}

export function ImageMetadata({ metadata }: ImageMetadataProps) {
  const hasDeviceMetadata = Boolean(metadata.camera.make || metadata.camera.model);
  const fileSystemTimestamps = metadata.derived?.fileSystemTimestamps as Record<string, string | null> | undefined;
  const technicalFields = [
    "LensMake", "FNumber", "ExposureTime", "ISOSpeedRatings", "FocalLength",
    "Flash", "WhiteBalance", "MeteringMode", "ExposureProgram", "DateTimeDigitized",
  ];
  return (
    <div className="space-y-6">
      {(metadata.geographic || hasDeviceMetadata) && (
        <div className="rounded-lg border border-warning/50 bg-warning/10 p-4">
          <div className="mb-2 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-warning" />
            <h3 className="font-semibold text-warning">Sensitive Metadata Detected</h3>
          </div>
          <p className="text-sm text-foreground/90">
            {metadata.geographic
              ? "GPS data may reveal where this image was captured."
              : "Camera and device information may identify equipment used to create this image."}
          </p>
        </div>
      )}

      {metadata.status === "FAILED" && (
        <p role="status" className="rounded-md border border-warning/50 bg-warning/10 p-4 text-sm text-foreground">
          Metadata extraction failed. The image was processed, but EXIF values are unavailable.
        </p>
      )}

      {/* Camera */}
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="mb-4 flex items-center gap-2">
          <Camera className="h-5 w-5 text-accent" />
          <h3 className="text-lg font-semibold text-foreground">Camera</h3>
        </div>
        <div className="space-y-2 text-sm">
          <MetadataField label="Make" value={metadata.camera.make} />
          <MetadataField label="Model" value={metadata.camera.model} />
          <MetadataField label="Lens" value={metadata.camera.lens} />
          <MetadataField label="Software" value={metadata.camera.software} />
        </div>
      </div>

      {/* Capture */}
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="mb-4 flex items-center gap-2">
          <Calendar className="h-5 w-5 text-accent" />
          <h3 className="text-lg font-semibold text-foreground">Capture</h3>
        </div>
        <div className="space-y-2 text-sm">
          <MetadataField
            label={metadata.capture.dateTimeOriginal && metadata.capture.timezoneUnknowns?.capturedAt
              ? "Captured At (timezone unknown)"
              : "Captured At"}
            value={metadata.capture.dateTimeOriginal}
            mono
          />
          <MetadataField
            label={metadata.capture.dateTimeDigitized && metadata.capture.timezoneUnknowns?.digitizedAt
              ? "Digitized At (timezone unknown)"
              : "Digitized At"}
            value={metadata.capture.dateTimeDigitized ?? metadata.capture.createDate}
            mono
          />
          <MetadataField
            label={metadata.capture.modifyDate && metadata.capture.timezoneUnknowns?.modifiedAt
              ? "Modified At (timezone unknown)"
              : "Modified At"}
            value={metadata.capture.modifyDate}
            mono
          />
          <MetadataField label="Server Received Time" value={metadata.capture.serverReceivedAt ?? null} mono />
          <MetadataField label="Server Staged File Created" value={fileSystemTimestamps?.stagedFileCreatedAt ?? null} mono />
          <MetadataField label="Staged File Metadata Changed" value={fileSystemTimestamps?.stagedFileMetadataChangedAt ?? null} mono />
          <MetadataField label="Staged File Modified" value={fileSystemTimestamps?.stagedFileModifiedAt ?? null} mono />
          <p className="pt-1 text-xs text-muted-foreground">
            Staging filesystem times describe the server-side copy, not the source device file.
          </p>
        </div>
      </div>

      {/* Geographic */}
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="mb-4 flex items-center gap-2">
          <MapPin className="h-5 w-5 text-accent" />
          <h3 className="text-lg font-semibold text-foreground">Geographic</h3>
        </div>
        {metadata.geographic ? (
          <>
            <div className="space-y-2 text-sm">
              <MetadataField label="Latitude" value={metadata.geographic.latitude.toFixed(6)} mono status="FOUND" />
              <MetadataField label="Longitude" value={metadata.geographic.longitude.toFixed(6)} mono status="FOUND" />
              <MetadataField label="Altitude" value={metadata.geographic.altitude === null ? null : `${metadata.geographic.altitude}m`} mono />
              <MetadataField label="GPS Timestamp" value={metadata.geographic.gpsTimestamp} mono />
            </div>
            <div className="mt-4 rounded-md bg-secondary p-3 text-xs text-muted-foreground">
              Location is derived from image metadata and does not establish the capture location.
            </div>
            {metadata.geographic.address && (
              <div className="mt-4 space-y-2 text-sm">
                <MetadataField label="Address" value={metadata.geographic.address.formatted} />
                <MetadataField label="Country" value={metadata.geographic.address.country} />
                <MetadataField label="Province / State" value={metadata.geographic.address.province} />
                <MetadataField label="City" value={metadata.geographic.address.city} />
                <MetadataField label="District" value={metadata.geographic.address.district} />
                <MetadataField label="Road" value={metadata.geographic.address.road} />
              </div>
            )}
          </>
        ) : (
          <p className="text-sm text-muted-foreground">
            {metadata.gpsStatus === "INVALID" ? "GPS metadata was present but invalid." : "No GPS metadata detected."}
          </p>
        )}
      </div>

      <div className="rounded-lg border border-border bg-card p-6">
        <div className="mb-4 flex items-center gap-2">
          <Camera className="h-5 w-5 text-accent" />
          <h3 className="text-lg font-semibold text-foreground">Additional EXIF</h3>
        </div>
        <div className="space-y-2 text-sm">
          {technicalFields.map((field) => (
            <MetadataField key={field} label={field} value={formatValue(metadata.raw[field])} mono />
          ))}
          <MetadataField label="EXIF status" value={metadata.status} />
        </div>
      </div>

      {/* Image */}
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="mb-4 flex items-center gap-2">
          <ImageIcon className="h-5 w-5 text-accent" />
          <h3 className="text-lg font-semibold text-foreground">Image</h3>
        </div>
        <div className="space-y-2 text-sm">
          <MetadataField
            label="Width"
            value={metadata.image.width === null ? null : `${metadata.image.width}px`}
            mono
          />
          <MetadataField
            label="Height"
            value={metadata.image.height === null ? null : `${metadata.image.height}px`}
            mono
          />
          <MetadataField label="Orientation" value={formatValue(metadata.image.orientation)} />
          <MetadataField label="Color Space" value={metadata.image.colorSpace} />
          <MetadataField label="Resolution" value={formatValue(metadata.image.resolution)} />
        </div>
      </div>
    </div>
  );
}

interface MetadataFieldProps {
  label: string;
  value: string | null;
  mono?: boolean;
  status?: "FOUND" | "NOT FOUND" | "UNKNOWN";
}

function MetadataField({ label, value, mono, status }: MetadataFieldProps) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border/50 pb-2 last:border-0">
      <span className="shrink-0 text-muted-foreground">{label}</span>
      <div className="flex min-w-0 items-center justify-end gap-2 text-right">
        {status && (
          <span
            className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
              status === "FOUND"
                ? "bg-success/20 text-success"
                : status === "NOT FOUND"
                  ? "bg-destructive/20 text-destructive"
                  : "bg-muted text-muted-foreground"
            }`}
          >
            {status}
          </span>
        )}
        <span className={`break-all ${mono ? "font-mono text-foreground" : "text-foreground"}`}>
          {value ?? "Not available"}
        </span>
      </div>
    </div>
  );
}

function formatValue(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  return typeof value === "string" || typeof value === "number"
    ? String(value)
    : JSON.stringify(value);
}
