import { useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toPng } from "html-to-image";
import { Download, GitFork, Home, Share2 } from "lucide-react";
import { banlistsApi } from "@/api/banlists";
import { BanlistShowcase } from "@/features/showcase/BanlistShowcase";
import { useAuth } from "@/hooks/useAuth";
import { Button, Skeleton, useToast } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";

export function PublicBanlistPage() {
  const { uuid = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const user = useAuth((s) => s.user);
  const ref = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState(false);

  const { data: bl, isLoading, isError } = useQuery({
    queryKey: ["public-banlist", uuid],
    queryFn: () => banlistsApi.detail(uuid),
    retry: false,
  });

  const fork = useMutation({
    mutationFn: () => banlistsApi.fork(uuid),
    onSuccess: (b) => { toast.success("Cópia criada!"); navigate(`/app/banlists/${b.uuid}`); },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  const share = async () => {
    const url = window.location.href;
    try {
      if (navigator.share) await navigator.share({ title: bl?.name, url });
      else { await navigator.clipboard.writeText(url); toast.success("Link copiado!"); }
    } catch { /* cancelled */ }
  };

  const download = async () => {
    if (!ref.current) return;
    setExporting(true);
    try {
      const dataUrl = await toPng(ref.current, {
        pixelRatio: 2,
        cacheBust: true,
        backgroundColor: getComputedStyle(document.documentElement).getPropertyValue("--color-bg") || "#0e0e14",
      });
      const a = document.createElement("a");
      a.download = `banlist-${(bl?.name ?? "banlist").replace(/[^\w-]+/g, "_").toLowerCase()}.png`;
      a.href = dataUrl;
      a.click();
      toast.success("Imagem gerada!");
    } catch (e) {
      toast.error("Não foi possível gerar a imagem", String(e));
    } finally {
      setExporting(false);
    }
  };

  if (isLoading) return <div className="mx-auto max-w-4xl p-4"><Skeleton className="h-[80vh] w-full" /></div>;
  if (isError || !bl) {
    return (
      <div className="grid min-h-dvh place-items-center p-6 text-center">
        <div>
          <p className="font-display text-xl">Banlist não encontrada</p>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">Ela pode ser privada ou ter sido removida.</p>
          <Link to="/app" className="mt-4 inline-block"><Button variant="secondary"><Home className="h-4 w-4" /> Ir para o app</Button></Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-dvh bg-[var(--color-bg)]">
      <div className="sticky top-0 z-10 border-b-2 border-[var(--color-border)] bg-[var(--color-surface)]/90 backdrop-blur">
        <div className="mx-auto flex max-w-4xl flex-wrap items-center gap-2 px-4 py-3">
          <Link to="/app" className="font-display text-lg tracking-tight text-[var(--color-accent)]">
            RIDE<span className="text-[var(--color-ink)]">DECK</span>
          </Link>
          <div className="ml-auto flex flex-wrap items-center gap-2">
            <Button variant="ghost" size="sm" onClick={share}><Share2 className="h-4 w-4" /> Compartilhar</Button>
            <Button variant="secondary" size="sm" loading={exporting} onClick={download}>
              <Download className="h-4 w-4" /> Imagem
            </Button>
            {user ? (
              bl.is_owner ? (
                <Link to={`/app/banlists/${bl.uuid}`}><Button size="sm">Editar</Button></Link>
              ) : (
                <Button size="sm" loading={fork.isPending} onClick={() => fork.mutate()}>
                  <GitFork className="h-4 w-4" /> Copiar
                </Button>
              )
            ) : (
              <Link to={`/login?next=/b/${uuid}`}><Button size="sm"><GitFork className="h-4 w-4" /> Entrar para copiar</Button></Link>
            )}
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-4xl p-4 sm:p-6">
        <BanlistShowcase ref={ref} banlist={bl} />
        {bl.description && (
          <div className="mt-6 rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <h3 className="font-display mb-2 text-sm uppercase text-[var(--color-ink-muted)]">Sobre esta banlist</h3>
            <p className="whitespace-pre-wrap text-sm text-[var(--color-ink-muted)]">{bl.description}</p>
          </div>
        )}
      </div>
    </div>
  );
}
