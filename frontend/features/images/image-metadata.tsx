import { MapPin, Camera, Image as ImageIcon, Calendar, AlertTriangle } from "lucide-react";

interface ImageMetadataProps {
  metadata: {
    camera: {
      make: string;
      model: string;
      lens: string;
      software: string;
    };
    capture: {
      dateTimeOriginal: string;
      createDate: string;
      modifyDate: string;
    };
    geographic: {
      latitude: number;
      longitude: number;
      altitude: number;
      gpsTimestamp: string;
    };
    image: {
      width: number;
      height: number;
      orientation: string;
      colorSpace: string;
      resolution: string;
    };
  };
}

export function ImageMetadata({ metadata }: ImageMetadataProps) {
  return (
    <div className="space-y-6">
      {/* Privacy Warning */}
      <div className="rounded-lg border border-warning/50 bg-warning/10 p-4">
        <div className="mb-2 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-warning" />
          <h3 className="font-semibold text-warning">Privacy Risk Detected</h3>
        </div>
        <p className="text-sm text-foreground/90">
          This image contains GPS coordinates and device information that could
          expose your location and equipment details when shared.
        </p>
      </div>

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
            label="Date/Time Original"
            value={metadata.capture.dateTimeOriginal}
            mono
          />
          <MetadataField
            label="Create Date"
            value={metadata.capture.createDate}
            mono
          />
          <MetadataField
            label="Modify Date"
            value={metadata.capture.modifyDate}
            mono
          />
        </div>
      </div>

      {/* Geographic */}
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="mb-4 flex items-center gap-2">
          <MapPin className="h-5 w-5 text-accent" />
          <h3 className="text-lg font-semibold text-foreground">Geographic</h3>
        </div>
        <div className="space-y-2 text-sm">
          <MetadataField
            label="Latitude"
            value={metadata.geographic.latitude.toFixed(6)}
            mono
            status="FOUND"
          />
          <MetadataField
            label="Longitude"
            value={metadata.geographic.longitude.toFixed(6)}
            mono
            status="FOUND"
          />
          <MetadataField
            label="Altitude"
            value={`${metadata.geographic.altitude}m`}
            mono
          />
          <MetadataField
            label="GPS Timestamp"
            value={metadata.geographic.gpsTimestamp}
            mono
          />
        </div>
        <div className="mt-4 rounded-md bg-secondary p-3 text-xs text-muted-foreground">
          Location derived from image metadata. GPS data may be altered or
          removed.
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
            value={`${metadata.image.width}px`}
            mono
          />
          <MetadataField
            label="Height"
            value={`${metadata.image.height}px`}
            mono
          />
          <MetadataField label="Orientation" value={metadata.image.orientation} />
          <MetadataField label="Color Space" value={metadata.image.colorSpace} />
          <MetadataField label="Resolution" value={metadata.image.resolution} />
        </div>
      </div>
    </div>
  );
}

interface MetadataFieldProps {
  label: string;
  value: string;
  mono?: boolean;
  status?: "FOUND" | "NOT FOUND" | "UNKNOWN";
}

function MetadataField({ label, value, mono, status }: MetadataFieldProps) {
  return (
    <div className="flex items-center justify-between border-b border-border/50 pb-2 last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <div className="flex items-center gap-2">
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
        <span className={mono ? "font-mono text-foreground" : "text-foreground"}>
          {value}
        </span>
      </div>
    </div>
  );
}
