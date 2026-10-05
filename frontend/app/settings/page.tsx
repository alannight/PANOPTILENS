"use client";

import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Eye, Loader2, Settings as SettingsIcon } from "lucide-react";
import { APIError, healthCheck } from "@/lib/api-client";

type ApiState = "loading" | "available" | "unavailable";

export default function SettingsPage() {
  const [apiState, setApiState] = useState<ApiState>("loading");
  const [apiError, setApiError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    healthCheck().then(() => { if (active) setApiState("available"); })
      .catch((cause: unknown) => {
        if (!active) return;
        setApiState("unavailable");
        setApiError(cause instanceof APIError && cause.status === 0 ? "Backend is not reachable." : "Backend health check failed.");
      });
    return () => { active = false; };
  }, []);

  return <div className="h-full overflow-auto"><div className="p-8">
    <header className="mb-8"><div className="mb-2 flex items-center gap-2"><Eye className="h-6 w-6 text-accent" /><h1 className="text-3xl font-bold tracking-tight text-foreground">Settings</h1></div><p className="text-muted-foreground">Runtime status and active security limitations.</p></header>
    <section className="max-w-2xl border-y border-border py-5"><div className="mb-4 flex items-center gap-2"><SettingsIcon className="h-5 w-5 text-accent" /><h2 className="font-semibold text-foreground">Services</h2></div><div className="flex items-center justify-between border-b border-border/50 py-3 text-sm"><span className="text-muted-foreground">Image API</span><span className="inline-flex items-center gap-2 font-mono">{apiState === "loading" ? <><Loader2 className="h-4 w-4 animate-spin" />Checking</> : apiState === "available" ? <><CheckCircle2 className="h-4 w-4 text-success" />Available</> : <><AlertCircle className="h-4 w-4 text-destructive" />Unavailable</>}</span></div>{apiError && <p role="alert" className="mt-2 text-sm text-destructive">{apiError}</p>}</section>
    <section className="mt-8 max-w-2xl border-y border-border py-5"><h2 className="mb-3 font-semibold text-foreground">Security</h2><p className="text-sm text-muted-foreground">Authentication and per-user authorization are not implemented. Image API access is enabled only in local development mode. Do not expose the development server to a network.</p></section>
    <section className="mt-8 max-w-2xl border-y border-border py-5"><h2 className="mb-3 font-semibold text-foreground">Configuration</h2><p className="text-sm text-muted-foreground">API URL, storage location, and upload limits are read from environment configuration. Editing them from this page is not implemented.</p></section>
  </div></div>;
}