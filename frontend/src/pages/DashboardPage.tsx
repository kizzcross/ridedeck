import { Link } from "react-router-dom";
import { Library, Layers, Shield, Swords, ArrowRight } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Badge, Panel } from "@/components/ui";

const SHORTCUTS = [
  { to: "/app/cards", icon: Library, title: "Explorar cartas", desc: "Catálogo com busca e filtros", phase: "Fase 2" },
  { to: "/app/decks", icon: Layers, title: "Meus decks", desc: "Builder interativo drag-and-drop", phase: "Fase 3" },
  { to: "/app/banlists", icon: Shield, title: "Banlists", desc: "Oficiais e da comunidade", phase: "Fase 6" },
  { to: "/app/tournaments", icon: Swords, title: "Torneios", desc: "Crie e participe", phase: "Fase 7" },
];

export function DashboardPage() {
  const { user } = useAuth();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold">
          Olá, {user?.username} 👋
        </h1>
        <p className="mt-1 text-[var(--color-ink-muted)]">
          Bem-vindo ao RideDeck. A fundação está no ar — as próximas fases habilitam cada área abaixo.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {SHORTCUTS.map(({ to, icon: Icon, title, desc, phase }) => (
          <Link key={to} to={to}>
            <Panel className="group h-full p-5 transition-transform hover:-translate-y-0.5">
              <div className="flex items-start justify-between">
                <Icon className="h-7 w-7 text-[var(--color-accent)]" />
                <Badge tone="neutral">{phase}</Badge>
              </div>
              <h3 className="mt-3 font-display text-lg font-semibold">{title}</h3>
              <p className="mt-1 text-sm text-[var(--color-ink-muted)]">{desc}</p>
              <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-[var(--color-accent)]">
                Abrir <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </span>
            </Panel>
          </Link>
        ))}
      </div>

      {user?.is_platform_admin && (
        <Panel className="border-[var(--color-violet)]/40 p-5">
          <div className="flex items-center gap-2">
            <Badge tone="official">Platform Admin</Badge>
            <h3 className="font-display text-lg font-semibold">Ferramentas administrativas</h3>
          </div>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
            Editor de power level, banlists oficiais, sincronização de catálogo e auditoria — habilitados nas Fases 2 e 5.
          </p>
        </Panel>
      )}
    </div>
  );
}
