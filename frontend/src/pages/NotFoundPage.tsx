import { Link } from "react-router-dom";
import { Button } from "@/components/ui";

export function NotFoundPage() {
  return (
    <div className="grid min-h-dvh place-items-center px-4 text-center">
      <div>
        <p className="font-display text-6xl font-bold text-[var(--color-accent)]">404</p>
        <h1 className="mt-2 font-display text-2xl font-bold">Página não encontrada</h1>
        <p className="mt-1 text-[var(--color-ink-muted)]">Essa carta não está no catálogo.</p>
        <Link to="/app" className="mt-6 inline-block">
          <Button>Voltar ao início</Button>
        </Link>
      </div>
    </div>
  );
}
