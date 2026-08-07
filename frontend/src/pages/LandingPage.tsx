import { Link } from "react-router-dom";
import { ArrowRight, Layers, Shield, Swords, Sparkles, Library, ListChecks } from "lucide-react";
import { Badge, Button, Panel } from "@/components/ui";

const FEATURES = [
  { icon: Library, title: "Catálogo completo", body: "Todas as cartas com identidade canônica separada de cada printing." },
  { icon: Layers, title: "Deck builder", body: "Drag-and-drop acessível, undo/redo, autosave e validação em tempo real." },
  { icon: ListChecks, title: "Coleção", body: "Owned vs. faltando, lista de compras — sem nunca invalidar seu deck." },
  { icon: Shield, title: "Banlists", body: "Oficiais e comunitárias, com Choice Restriction modelada de verdade." },
  { icon: Sparkles, title: "Nível do deck", body: "Você avalia a força do seu deck de 1 a 5 estrelas — usada como orçamento nos torneios de pool." },
  { icon: Swords, title: "Torneios", body: "Inscrições, snapshots imutáveis, brackets interativos e reporte de resultados." },
];

export function LandingPage() {
  return (
    <div className="min-h-dvh">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-4 py-5">
        <div className="flex items-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-500 font-display text-base font-bold text-white">
            R
          </span>
          <span className="font-display text-xl font-bold">RideDeck</span>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/login">
            <Button variant="ghost">Entrar</Button>
          </Link>
          <Link to="/register">
            <Button>Criar conta</Button>
          </Link>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-4 pb-16 pt-10 text-center md:pt-20">
        <Badge tone="accent" className="mx-auto mb-5">
          Plataforma competitiva de Cardfight!! Vanguard
        </Badge>
        <h1 className="mx-auto max-w-3xl font-display text-4xl leading-tight md:text-6xl">
          <span className="text-gradient">Construa, valide e dispute</span>
          <br />
          os melhores decks
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-[var(--color-ink-muted)]">
          Deck builder de nível profissional, controle de coleção, banlists da comunidade,
          nível de deck por estrelas e torneios com brackets — tudo em um só lugar.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link to="/register">
            <Button size="lg" className="gap-2">
              Começar agora <ArrowRight className="h-5 w-5" />
            </Button>
          </Link>
          <Link to="/login">
            <Button size="lg" variant="outline">
              Já tenho conta
            </Button>
          </Link>
        </div>

        <div className="mt-16 grid gap-4 text-left sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <Panel key={title} className="rd-card group p-5">
              <div className="mb-3 grid h-11 w-11 place-items-center rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-accent)]/12 text-[var(--color-accent)] transition-colors group-hover:bg-[var(--color-accent)]/20">
                <Icon className="h-6 w-6" />
              </div>
              <h3 className="font-display text-base">{title}</h3>
              <p className="mt-1.5 text-sm text-[var(--color-ink-muted)]">{body}</p>
            </Panel>
          ))}
        </div>
      </section>

      <footer className="border-t border-[var(--color-border)] py-8 text-center text-sm text-[var(--color-ink-subtle)]">
        RideDeck é um projeto de fã, não afiliado à Bushiroad. Dados de cartas são fictícios em ambiente de desenvolvimento.
      </footer>
    </div>
  );
}
