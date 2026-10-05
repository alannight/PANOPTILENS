"use client";

import { useEffect, useState } from "react";
import { AlertCircle, Download, Eye, FileBarChart, Loader2 } from "lucide-react";
import { APIError, getImages, ImageResponse } from "@/lib/api-client";

export default function ReportsPage() {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    getImages().then((rows) => { if (active) setImages(rows); })
      .catch((cause: unknown) => { if (active) setError(cause instanceof APIError && cause.status === 0 ? "Cannot connect to the image service." : "Unable to load data for export."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  function exportJson() {
    const contents = JSON.stringify({ exportedAt: new Date().toISOString(), scope: "Persisted image records; not a formal investigation report", images }, null, 2);
    const url = URL.createObjectURL(new Blob([contents], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "panoptilens-image-records.json";
    link.click();
    URL.revokeObjectURL(url);
  }

  return <div className="h-full overflow-auto"><div className="p-8">
    <header className="mb-8"><div className="mb-2 flex items-center gap-2"><Eye className="h-6 w-6 text-accent" /><h1 className="text-3xl font-bold tracking-tight text-foreground">Reports</h1></div><p className="text-muted-foreground">Export the persisted image dataset. Formal case report generation is not implemented.</p></header>
    {loading ? <div role="status" className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Loading stored image records...</div>
      : error ? <div role="alert" className="flex items-center gap-2 text-sm text-destructive"><AlertCircle className="h-4 w-4" />{error}</div>
      : <section className="max-w-2xl border-y border-border py-5"><div className="mb-5 flex items-center gap-3"><FileBarChart className="h-5 w-5 text-accent" /><div><h2 className="font-semibold text-foreground">Image records</h2><p className="text-sm text-muted-foreground">{images.length} persisted image{images.length === 1 ? "" : "s"} · Includes metadata and hashes</p></div></div><button type="button" onClick={exportJson} disabled={images.length === 0} className="inline-flex items-center gap-2 border border-border px-3 py-2 text-sm text-foreground hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50"><Download className="h-4 w-4" />Export JSON</button><p className="mt-4 text-xs text-warning">The export can contain sensitive GPS and device metadata. Review it before sharing.</p></section>}
  </div></div>;
}