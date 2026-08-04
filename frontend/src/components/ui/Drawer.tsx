import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/cn";

/** Accessible slide-over drawer. Closes on Escape and backdrop click. */
export function Drawer({
  open,
  onClose,
  title,
  children,
  side = "right",
}: {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
  side?: "right" | "bottom";
}) {
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

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <div
        className={cn(
          "absolute bg-[var(--color-surface)] shadow-2xl",
          side === "right"
            ? "inset-y-0 right-0 w-full max-w-md animate-[slideIn_0.2s_ease]"
            : "inset-x-0 bottom-0 max-h-[85vh] rounded-t-2xl",
        )}
      >
        <div className="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3">
          <div className="min-w-0 font-display text-lg font-semibold">{title}</div>
          <button
            onClick={onClose}
            aria-label="Fechar"
            className="rounded-lg p-1.5 text-[var(--color-ink-muted)] hover:bg-[var(--color-surface-2)]"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="max-h-[calc(100dvh-3.5rem)] overflow-y-auto p-4">{children}</div>
      </div>
      <style>{`@keyframes slideIn{from{transform:translateX(100%)}to{transform:translateX(0)}}`}</style>
    </div>
  );
}
