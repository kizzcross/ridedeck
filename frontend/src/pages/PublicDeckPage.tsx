import { useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toPng } from "html-to-image";
import { Copy, Download, GitFork, Home, Scale, Share2 } from "lucide-react";
import { decksApi } from "@/api/decks";
import { DeckShowcase } from "@/features/showcase/DeckShowcase";
import { useAuth } from "@/hooks/useAuth";
import { Button, Skeleton, useToast } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";

export function PublicDeckPage() {
  const { uuid = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const user = useAuth((s) => s.user);
  const showcaseRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState(false);

  const { data: deck, isLoading, isError } = useQuery({
    queryKey: ["public-deck", uuid],
    queryFn: () => decksApi.detail(uuid),
    retry: false,
  });

  const fork = useMutation({
    mutationFn: () => decksApi.fork(uuid),
    onSuccess: (d) => { toast.success("Deck copiado para você!"); navigate(`/app/decks/${d.uuid}`); },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  const share = async () => {
    const url = window.location.href;
    try {
      if (navigator.share) await navigator.share({ title: deck?.title, url });
      else { await navigator.clipboard.writeText(url); toast.success("Link copiado!"); }
    } catch { /* user cancelled */ }
  };

  const download = async () => {
    if (!showcaseRef.current) return;
    setExporting(true);
    try {
      const dataUrl = await toPng(showcaseRef.current, {
        pixelRatio: 2,
        cacheBust: true,
        backgroundColor: getComputedStyle(document.documentElement).getPropertyValue("--color-bg") || "#0e0e14",
      });
      const a = document.createElement("a");
      a.download = `${(deck?.title ?? "deck").replace(/[^\w-]+/g, "_").toLowerCase()}.png`;
      a.href = dataUrl;
      a.click();
      toast.success("Imagem gerada!");
    } catch (e) {
      toast.error("Não foi possível gerar a imagem", String(e));
    } finally {
      setExporting(false);
    }
  };

  if (isLoading) {
    return <div className="mx-auto max-w-5xl p-4"><Skeleton className="h-[80vh] w-full" /></div>;
  }
  if (isError || !deck) {
    return (
      <div className="grid min-h-dvh place-items-center p-6 text-center">
        <div>
          <p className="font-display text-xl">Deck não encontrado</p>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">Ele pode ser privado ou ter sido removido.</p>
          <Link to="/app" className="mt-4 inline-block"><Button variant="secondary"><Home className="h-4 w-4" /> Ir para o app</Button></Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-dvh bg-[var(--color-bg)]">
      {/* Action bar */}
      <div className="sticky top-0 z-10 border-b-2 border-[var(--color-border)] bg-[var(--color-surface)]/90 backdrop-blur">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-2 px-4 py-3">
          <Link to="/app" className="font-display text-lg tracking-tight text-[var(--color-accent)]">
            RIDE<span className="text-[var(--color-ink)]">DECK</span>
          </Link>
          <div className="ml-auto flex flex-wrap items-center gap-2">
            {deck.check_banlist_uuid && (
              <Link to={`/app/banlists/${deck.check_banlist_uuid}`}>
                <Button variant="ghost" size="sm"><Scale className="h-4 w-4" /> Banlist</Button>
              </Link>
            )}
            <Button variant="ghost" size="sm" onClick={share}><Share2 className="h-4 w-4" /> Compartilhar</Button>
            <Button variant="secondary" size="sm" loading={exporting} onClick={download}>
              <Download className="h-4 w-4" /> Imagem
            </Button>
            {user ? (
              deck.is_owner ? (
                <Link to={`/app/decks/${deck.uuid}`}><Button size="sm"><Copy className="h-4 w-4" /> Editar</Button></Link>
              ) : (
                <Button size="sm" loading={fork.isPending} onClick={() => fork.mutate()}>
                  <GitFork className="h-4 w-4" /> Copiar deck
                </Button>
              )
            ) : (
              <Link to={`/login?next=/d/${uuid}`}><Button size="sm"><GitFork className="h-4 w-4" /> Entrar para copiar</Button></Link>
            )}
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-5xl p-4 sm:p-6">
        <DeckShowcase ref={showcaseRef} deck={deck} />
        {deck.guide && (
          <div className="mt-6 rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <h3 className="font-display mb-2 text-sm uppercase text-[var(--color-ink-muted)]">Guia do piloto</h3>
            <p className="whitespace-pre-wrap text-sm text-[var(--color-ink-muted)]">{deck.guide}</p>
          </div>
        )}
      </div>
    </div>
  );
}
