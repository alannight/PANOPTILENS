"use client";

import { useState, useCallback } from "react";
import { Upload, FileImage, AlertCircle, Loader2, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { uploadImages, APIError, ImageResponse } from "@/lib/api-client";

interface ImageUploadProps {
  onUploadComplete: (imageData: ImageResponse) => void;
  caseId?: string;
}

export function ImageUpload({ onUploadComplete, caseId }: ImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<string>("Preparing upload...");

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const processImages = useCallback(async (files: File[]) => {
    if (files.length === 0) return;
    if (files.length > 20) {
      setError("Choose no more than 20 images per upload.");
      return;
    }
    setIsProcessing(true);
    setError(null);
    setUploadProgress(`Preparing ${files.length} image${files.length === 1 ? "" : "s"}...`);

    try {
      setUploadProgress(`Uploading ${files.length} image${files.length === 1 ? "" : "s"}...`);
      const result = await uploadImages(files, caseId);
      result.results.forEach(onUploadComplete);
      setUploadProgress(`Upload complete: ${result.results.length} saved`);
      if (result.errors.length > 0) {
        setError(`${result.errors.length} file${result.errors.length === 1 ? "" : "s"} failed: ${result.errors.map((item) => item.filename ?? "unnamed file").join(", ")}`);
      }
      
      setTimeout(() => {
        setIsProcessing(false);
        setUploadProgress("");
      }, 1000);

    } catch (err) {
      if (err instanceof APIError) {
        // Handle specific API errors
        if (err.status === 413) {
          setError("File size exceeds the configured server limit.");
        } else if (err.status === 400) {
          setError(err.message || "Invalid file format");
        } else if (err.status === 408) {
          setError("Upload timeout - please try again");
        } else if (err.status === 0) {
          setError("Cannot connect to server - is the backend running?");
        } else {
          setError(err.message || "Upload failed");
        }
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Upload failed - unknown error");
      }
      setIsProcessing(false);
      setUploadProgress("");
    }
  }, [caseId, onUploadComplete]);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      await processImages(Array.from(e.dataTransfer.files));
    },
    [processImages]
  );

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    await processImages(Array.from(e.target.files ?? []));
    e.target.value = "";
  };

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      {!isProcessing && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "relative flex min-h-[300px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors",
            isDragging
              ? "border-accent bg-accent/10"
              : "border-border bg-secondary/50 hover:bg-secondary"
          )}
        >
          <input
            type="file"
            onChange={handleFileSelect}
            accept=".jpg,.jpeg,.png,.webp,.gif,.heic,.heif,.dng,.cr2,.nef,.arw"
            multiple
            className="absolute inset-0 cursor-pointer opacity-0"
          />
          
          <Upload className="mb-4 h-12 w-12 text-muted-foreground" />
          
          <h3 className="mb-2 text-lg font-semibold text-foreground">
            Upload Image
          </h3>
          
          <p className="mb-4 text-sm text-muted-foreground">
            Drag and drop or click to select
          </p>
          
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <FileImage className="h-4 w-4" />
            <span>JPG, PNG, WEBP, GIF, HEIC, HEIF, DNG, CR2, NEF, ARW • Up to 20 files</span>
          </div>
        </div>
      )}

      {isProcessing && (
        <div className="flex min-h-[300px] flex-col items-center justify-center">
          {uploadProgress.startsWith("Upload complete") ? (
            <CheckCircle2 className="mb-4 h-12 w-12 text-success" />
          ) : (
            <Loader2 className="mb-4 h-12 w-12 animate-spin text-accent" />
          )}
          
          <h3 className="mb-2 text-lg font-semibold text-foreground">
            {uploadProgress.startsWith("Upload complete") ? "Upload complete" : "Processing images"}
          </h3>
          
          <p className="font-mono text-sm text-accent">
            {uploadProgress}
          </p>
          
          {!uploadProgress.startsWith("Upload complete") && (
            <div className="mt-6 text-center text-xs text-muted-foreground">
              <p>Server is processing your image</p>
              <p className="mt-1">This includes:</p>
              <ul className="mt-2 space-y-1">
                <li>• File validation and storage</li>
                <li>• Cryptographic hash calculation</li>
                <li>• EXIF metadata extraction</li>
                <li>• Forensic file analysis</li>
              </ul>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="mt-4 flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}
    </div>
  );
}
