"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, Eye, Loader2, Network } from "lucide-react";
import { APIError, getImages, ImageResponse } from "@/lib/api-client";

interface GraphNode { id: string; label: string; kind: string }
interface GraphEdge { id: string; from: string; to: string; label: string }

export default function GraphPage() {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    getImages().then((rows) => { if (active) setImages(rows); })
      .catch((cause: unknown) => { if (active) setError(cause instanceof APIError && cause.status === 0 ? "Cannot connect to the image service." : "Unable to load graph source records."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  for (const image of images) {
    const imageNode = `image:${image.id}`;
    nodes.push({ id: imageNode, label: image.filename, kind: "Image" });
    const hashNode = `sha256:${image.hash.sha256}`;
    nodes.push({ id: hashNode, label: `SHA-256 ${image.hash.sha256.slice(0, 16)}…`, kind: "File identifier" });
    edges.push({ id: `${imageNode}-${hashNode}`, from: imageNode, to: hashNode, label: "identified by" });
    if (image.metadata.status === "PRESENT") {
      const metadataNode = `metadata:${image.id}`;
      nodes.push({ id: metadataNode, label: "EXIF metadata", kind: "Metadata record" });
      edges.push({ id: `${imageNode}-${metadataNode}`, from: imageNode, to: metadataNode, label: "has stored" });
    }
    if (image.metadata.geographic) {
      const gpsNode = `gps:${image.metadata.geographic.latitude},${image.metadata.geographic.longitude}`;
      nodes.push({ id: gpsNode, label: `GPS ${image.metadata.geographic.latitude.toFixed(5)}, ${image.metadata.geographic.longitude.toFixed(5)}`, kind: "EXIF location" });
      edges.push({ id: `${imageNode}-${gpsNode}`, from: imageNode, to: gpsNode, label: "contains coordinates" });
    }
  }
  const uniqueNodes = [...new Map(nodes.map((node) => [node.id, node])).values()];

  return <div className="h-full overflow-auto"><div className="p-8">
    <header className="mb-8"><div className="mb-2 flex items-center gap-2"><Eye className="h-6 w-6 text-accent" /><h1 className="text-3xl font-bold tracking-tight text-foreground">Knowledge Graph</h1></div><p className="text-muted-foreground">Image, file hash, and stored metadata relationships. No inferred entities are added.</p></header>
    {loading ? <div role="status" className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Loading image relationships...</div>
      : error ? <div role="alert" className="flex items-center gap-2 text-sm text-destructive"><AlertCircle className="h-4 w-4" />{error}</div>
      : images.length === 0 ? <State title="No image relationships" message="Upload an image to create source-backed graph relationships." />
      : edges.length === 0 ? <State title="No metadata relationships available" message={`${images.length} images are stored, but they currently have no extracted EXIF/GPS relationships. File identity remains available in Forensics.`} />
      : <div className="grid gap-8 lg:grid-cols-[1fr_1.3fr]">
        <section><h2 className="mb-3 text-sm font-semibold text-foreground">Nodes ({uniqueNodes.length})</h2><div className="divide-y divide-border border-y border-border">{uniqueNodes.map((node) => <div key={node.id} className="py-3"><p className="break-all text-sm text-foreground">{node.label}</p><p className="text-xs text-muted-foreground">{node.kind}</p>{node.kind === "Image" && <Link href={`/images/${node.id.slice(6)}`} className="text-xs text-accent underline underline-offset-4">Open image</Link>}</div>)}</div></section>
        <section><h2 className="mb-3 text-sm font-semibold text-foreground">Observed relationships ({edges.length})</h2><div className="divide-y divide-border border-y border-border">{edges.map((edge) => { const from = uniqueNodes.find((node) => node.id === edge.from); const to = uniqueNodes.find((node) => node.id === edge.to); return <div key={edge.id} className="grid gap-2 py-3 sm:grid-cols-[1fr_auto_1fr] sm:items-center"><span className="break-all text-sm text-foreground">{from?.label}</span><span className="text-xs text-muted-foreground">{edge.label}</span><span className="break-all font-mono text-xs text-foreground">{to?.label}</span></div>; })}</div></section>
      </div>}
  </div></div>;
}

function State({ title, message }: { title: string; message: string }) {
  return <div className="flex min-h-64 flex-col items-center justify-center border border-border bg-card p-8 text-center"><Network className="mb-4 h-10 w-10 text-muted-foreground" /><h2 className="mb-2 text-lg font-semibold text-foreground">{title}</h2><p className="max-w-lg text-sm text-muted-foreground">{message}</p></div>;
}