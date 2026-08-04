import { useEffect, useState } from "react";
import { AlertTriangle, X } from "lucide-react";
import { Button } from "./Button";

/**
 * Destructive-action confirmation. The confirm button stays disabled until the
 * user types the exact keyword (default "excluir") — prevents accidental deletes.
 */
export function ConfirmDeleteDialog({
  open,
  title,
  description,
  keyword = "excluir",
  confirmLabel = "Excluir",
  loading = false,
  onConfirm,
  onClose,
}: {
  open: boolean;
  title: string;
  description?: string;
  keyword?: string;
  confirmLabel?: string;
  loading?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}) {
  const [value, setValue] = useState("");

  useEffect(() => {
    if (open) setValue("");
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;
  const matches = value.trim().toLowerCase() === keyword.toLowerCase();

  return (
    <div className="fixed inset-0 z-[60] grid place-items-center p-4" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} aria-hidden />
      <div className="rd-fade-in relative w-full max-w-sm rounded-[var(--radius-card)] border-2 border-[var(--color-danger)] bg-[var(--color-surface)] p-5 shadow-[var(--shadow-hard)]">
        <button
          onClick={onClose}
          aria-label="Fechar"
          className="absolute right-3 top-3 rounded-lg p-1 text-[var(--color-ink-subtle)] hover:text-[var(--color-ink)]"
        >
          <X className="h-4 w-4" />
        </button>
        <div className="mb-3 flex items-center gap-2">
          <AlertTriangle className="h-6 w-6 text-[var(--color-danger)]" />
          <h2 className="font-display text-lg">{title}</h2>
        </div>
        {description && <p className="mb-3 text-sm text-[var(--color-ink-muted)]">{description}</p>}
        <label className="mb-1 block text-xs text-[var(--color-ink-muted)]">
          Digite <b className="text-[var(--color-danger)]">{keyword}</b> para confirmar:
        </label>
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && matches && onConfirm()}
          autoFocus
          aria-label={`Digite ${keyword} para confirmar`}
          className="mb-4 h-10 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 text-sm focus:border-[var(--color-danger)]"
        />
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>Cancelar</Button>
          <Button variant="danger" disabled={!matches} loading={loading} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
