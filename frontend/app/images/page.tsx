"use client";

import { useEffect, useState } from "react";
import { ImageUpload } from "@/features/images/image-upload";
import { ImageGallery } from "@/features/images/image-gallery";
import { AdminPasswordDialog } from "@/components/admin-password-dialog";
import {
  APIError,
  CaseResponse,
  caseReportUrl,
  createCase,
  emptyTrash,
  getCases,
  getImages,
  getTrashImages,
  hardDeleteImage,
  ImageResponse,
  restoreImage,
} from "@/lib/api-client";
import { AlertCircle, Archive, Download, Eye, FolderPlus, Loader2, RotateCcw, Trash2 } from "lucide-react";

export default function ImagesPage() {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cases, setCases] = useState<CaseResponse[]>([]);
  const [caseFilter, setCaseFilter] = useState("");
  const [caseName, setCaseName] = useState("");
  const [view, setView] = useState<"images" | "trash">("images");
  const [passwordAction, setPasswordAction] = useState<{ type: "single"; imageId: string } | { type: "empty" } | null>(null);

  useEffect(() => {
    let active = true;
    getCases()
      .then((items) => { if (active) setCases(items); })
      .catch(() => undefined);
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    (view === "trash" ? getTrashImages() : getImages(caseFilter || undefined))
      .then((items) => {
        if (active) {
          setImages(items);
          setError(null);
        }
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
  }, [caseFilter, view]);

  const handleUploadComplete = (imageData: ImageResponse) => {
    setImages((prev) => [imageData, ...prev.filter((image) => image.id !== imageData.id)]);
    setError(null);
  };

  const handleCreateCase = async (event: React.FormEvent) => {
    event.preventDefault();
    const name = caseName.trim();
    if (!name) return;
    try {
      const created = await createCase(name);
      setCases((current) => [created, ...current]);
      setCaseFilter(created.id);
      setCaseName("");
      setView("images");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create case.");
    }
  };

  const handleRestore = async (imageId: string) => {
    try {
      await restoreImage(imageId);
      setImages((current) => current.filter((image) => image.id !== imageId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to restore image.");
    }
  };

  const handleHardDelete = async (imageId: string) => {
    setPasswordAction({ type: "single", imageId });
  };

  const handleEmptyTrash = async () => {
    setPasswordAction({ type: "empty" });
  };

  const confirmDelete = async (password: string) => {
    if (!passwordAction) return;
    if (passwordAction.type === "single") {
      await hardDeleteImage(passwordAction.imageId, password);
      setImages((current) => current.filter((image) => image.id !== passwordAction.imageId));
      setPasswordAction(null);
      return;
    }
    const result = await emptyTrash(password);
    setImages((current) => current.filter((image) => result.failed.some((failure) => failure.id === image.id)));
    if (result.failed.length) setError(`${result.failed.length} files could not be permanently removed.`);
    setPasswordAction(null);
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

        <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-y border-border py-4">
          <div className="flex items-center gap-2" role="tablist" aria-label="Image views">
            <button
              type="button"
              role="tab"
              aria-selected={view === "images"}
              onClick={() => setView("images")}
              className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm ${view === "images" ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-secondary"}`}
            >
              <Eye className="h-4 w-4" /> Images
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={view === "trash"}
              onClick={() => setView("trash")}
              className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm ${view === "trash" ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-secondary"}`}
            >
              <Archive className="h-4 w-4" /> Trash
            </button>
          </div>

          {view === "images" && (
            <div className="flex flex-wrap items-center gap-3">
              <label htmlFor="case-filter" className="text-sm text-muted-foreground">Case</label>
              <select
                id="case-filter"
                value={caseFilter}
                onChange={(event) => setCaseFilter(event.target.value)}
                className="min-w-48 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
              >
                <option value="">All cases</option>
                {cases.map((investigation) => (
                  <option key={investigation.id} value={investigation.id}>{investigation.name}</option>
                ))}
              </select>
              {caseFilter && (
                <a
                  href={caseReportUrl(caseFilter)}
                  className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-foreground hover:bg-secondary"
                >
                  <Download className="h-4 w-4" /> Export Case
                </a>
              )}
              <form onSubmit={handleCreateCase} className="flex items-center gap-2">
                <input
                  value={caseName}
                  onChange={(event) => setCaseName(event.target.value)}
                  aria-label="New case name"
                  placeholder="New case name"
                  className="w-44 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
                />
                <button type="submit" className="inline-flex items-center gap-2 rounded-md bg-secondary px-3 py-2 text-sm text-foreground hover:bg-secondary/80">
                  <FolderPlus className="h-4 w-4" /> Create Case
                </button>
              </form>
            </div>
          )}

          {view === "trash" && images.length > 0 && (
            <button
              type="button"
              onClick={handleEmptyTrash}
              className="inline-flex items-center gap-2 rounded-md border border-destructive/50 px-3 py-2 text-sm text-destructive hover:bg-destructive/10"
            >
              <Trash2 className="h-4 w-4" /> Empty Trash
            </button>
          )}
        </div>

        {view === "images" && (
          <div className="mb-8">
            <ImageUpload onUploadComplete={handleUploadComplete} caseId={caseFilter || undefined} />
          </div>
        )}

        {error && (
          <div role="alert" className="mb-6 flex items-center gap-2 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}

        {passwordAction && (
          <AdminPasswordDialog
            title={passwordAction.type === "empty" ? "Empty Trash?" : "Delete evidence permanently?"}
            description={passwordAction.type === "empty"
              ? `Permanently delete all ${images.length} trashed images. This cannot be undone.`
              : "Permanently delete this evidence file and its record. This cannot be undone."}
            onCancel={() => setPasswordAction(null)}
            onConfirm={confirmDelete}
          />
        )}

        {loading ? (
          <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading {view === "trash" ? "trash" : "saved images"}...
          </div>
        ) : images.length > 0 ? (
          view === "images" ? (
            <div>
              <h2 className="mb-4 text-lg font-semibold text-foreground">Saved Images</h2>
              <ImageGallery images={images} />
            </div>
          ) : (
            <div className="divide-y divide-border border-y border-border">
              {images.map((image) => (
                <div key={image.id} className="flex flex-wrap items-center justify-between gap-4 py-4">
                  <div className="min-w-0">
                    <p className="truncate font-medium text-foreground">{image.filename}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Deleted {image.deletedAt ? new Date(image.deletedAt).toLocaleString() : "time unavailable"}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button type="button" onClick={() => handleRestore(image.id)} className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm hover:bg-secondary">
                      <RotateCcw className="h-4 w-4" /> Restore
                    </button>
                    <button type="button" onClick={() => handleHardDelete(image.id)} className="inline-flex items-center gap-2 rounded-md border border-destructive/50 px-3 py-2 text-sm text-destructive hover:bg-destructive/10">
                      <Trash2 className="h-4 w-4" /> Delete Permanently
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : <p className="text-sm text-muted-foreground">{view === "trash" ? "Trash is empty." : "No images uploaded yet."}</p>}
      </div>
    </div>
  );
}
