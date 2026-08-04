import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { CheckCircle2, Info, TriangleAlert, XCircle, X } from "lucide-react";
import { cn } from "@/lib/cn";

type ToastTone = "success" | "error" | "info" | "warning";
interface Toast {
  id: number;
  tone: ToastTone;
  title: string;
  description?: string;
}

interface ToastCtx {
  push: (t: Omit<Toast, "id">) => void;
  success: (title: string, description?: string) => void;
  error: (title: string, description?: string) => void;
  info: (title: string, description?: string) => void;
}

const Ctx = createContext<ToastCtx | null>(null);

const icons = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
  warning: TriangleAlert,
};

const toneClass: Record<ToastTone, string> = {
  success: "border-[var(--color-success)]/40",
  error: "border-[var(--color-danger)]/40",
  info: "border-[var(--color-info)]/40",
  warning: "border-[var(--color-warning)]/40",
};
const iconClass: Record<ToastTone, string> = {
  success: "text-[var(--color-success)]",
  error: "text-[var(--color-danger)]",
  info: "text-[var(--color-info)]",
  warning: "text-[var(--color-warning)]",
};

let counter = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const remove = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (t: Omit<Toast, "id">) => {
      const id = ++counter;
      setToasts((prev) => [...prev, { ...t, id }]);
      setTimeout(() => remove(id), 5000);
    },
    [remove],
  );

  const value = useMemo<ToastCtx>(
    () => ({
      push,
      success: (title, description) => push({ tone: "success", title, description }),
      error: (title, description) => push({ tone: "error", title, description }),
      info: (title, description) => push({ tone: "info", title, description }),
    }),
    [push],
  );

  return (
    <Ctx.Provider value={value}>
      {children}
      <div
        className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-[min(92vw,22rem)] flex-col gap-2"
        role="region"
        aria-live="polite"
        aria-label="Notificações"
      >
        {toasts.map((t) => {
          const Icon = icons[t.tone];
          return (
            <div
              key={t.id}
              role="status"
              className={cn(
                "pointer-events-auto flex items-start gap-3 rounded-lg border bg-[var(--color-surface-2)] p-3 shadow-[var(--shadow-panel)]",
                toneClass[t.tone],
              )}
            >
              <Icon className={cn("mt-0.5 h-5 w-5 shrink-0", iconClass[t.tone])} aria-hidden />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-[var(--color-ink)]">{t.title}</p>
                {t.description && (
                  <p className="mt-0.5 text-xs text-[var(--color-ink-muted)]">{t.description}</p>
                )}
              </div>
              <button
                onClick={() => remove(t.id)}
                className="text-[var(--color-ink-subtle)] hover:text-[var(--color-ink)]"
                aria-label="Fechar notificação"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
    </Ctx.Provider>
  );
}

export function useToast(): ToastCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
