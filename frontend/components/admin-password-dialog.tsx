"use client";

import { FormEvent, useState } from "react";

interface AdminPasswordDialogProps {
  title: string;
  description: string;
  onCancel: () => void;
  onConfirm: (password: string) => Promise<void>;
}

export function AdminPasswordDialog({ title, description, onCancel, onConfirm }: AdminPasswordDialogProps) {
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!password) return;
    setSubmitting(true);
    setError(null);
    try {
      await onConfirm(password);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Deletion was not authorized.");
    } finally {
      setSubmitting(false);
      setPassword("");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" role="presentation">
      <section role="dialog" aria-modal="true" aria-labelledby="admin-password-title" className="w-full max-w-md rounded-lg border border-border bg-background p-6 shadow-xl">
        <h2 id="admin-password-title" className="text-lg font-semibold text-foreground">{title}</h2>
        <p className="mt-2 text-sm text-muted-foreground">{description}</p>
        <form onSubmit={submit} className="mt-5 space-y-4">
          <label htmlFor="admin-password" className="block text-sm font-medium text-foreground">Admin Password</label>
          <input
            id="admin-password"
            type="password"
            autoComplete="current-password"
            autoFocus
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
          />
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onCancel} disabled={submitting} className="rounded-md border border-border px-3 py-2 text-sm hover:bg-secondary">Cancel</button>
            <button type="submit" disabled={submitting || !password} className="rounded-md bg-destructive px-3 py-2 text-sm text-destructive-foreground disabled:opacity-50">
              {submitting ? "Verifying..." : "Confirm Delete"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}