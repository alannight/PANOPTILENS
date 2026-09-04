import { cn } from "@/lib/utils";

interface StatsCardProps {
  label: string;
  value: string | number;
  description?: string;
  variant?: "default" | "success" | "warning" | "danger";
  mono?: boolean;
}

export function StatsCard({
  label,
  value,
  description,
  variant = "default",
  mono = false,
}: StatsCardProps) {
  const variants = {
    default: "text-foreground",
    success: "text-success",
    warning: "text-warning",
    danger: "text-destructive",
  };

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div
        className={cn(
          "text-2xl font-bold",
          mono && "font-mono",
          variants[variant]
        )}
      >
        {value}
      </div>
      {description && (
        <div className="mt-1 text-xs text-muted-foreground">
          {description}
        </div>
      )}
    </div>
  );
}
