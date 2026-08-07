import { Suspense } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutGrid,
  Library,
  ListChecks,
  Moon,
  Sun,
  Swords,
  Shield,
  LogOut,
  Layers,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useTheme } from "./theme";
import { Button } from "@/components/ui";
import { Avatar } from "@/components/Avatar";
import { ReduceMotionToggle } from "@/features/championship/ReduceMotionToggle";
import { cn } from "@/lib/cn";

const NAV = [
  { to: "/app", label: "Início", icon: LayoutGrid, end: true },
  { to: "/app/cards", label: "Cartas", icon: Library },
  { to: "/app/decks", label: "Decks", icon: Layers },
  { to: "/app/collection", label: "Coleção", icon: ListChecks },
  { to: "/app/banlists", label: "Banlists", icon: Shield },
  { to: "/app/tournaments", label: "Torneios", icon: Swords },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();

  return (
    <div className="min-h-dvh">
      <a
        href="#main-content"
        className="font-display sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded-[6px] focus:border-2 focus:border-[var(--color-border)] focus:bg-[var(--color-accent)] focus:px-3 focus:py-2 focus:text-xs focus:uppercase focus:text-[#1a1400]"
      >
        Pular para o conteúdo
      </a>
      {/* Top bar */}
      <header className="sticky top-0 z-40 border-b-2 border-[var(--color-border)] bg-[var(--color-canvas)]/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4">
          <NavLink to="/app" className="rd-press flex items-center gap-2">
            <span className="font-display grid h-8 w-8 place-items-center rounded-[4px] border-2 border-[var(--color-border)] bg-brand-400 text-sm text-[#2a1a00] shadow-[var(--shadow-hard-sm)]">
              R
            </span>
            <span className="font-display text-base tracking-tight">RideDeck</span>
          </NavLink>

          <nav className="ml-4 hidden items-center gap-1 md:flex">
            {NAV.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    "font-display flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-[11px] uppercase tracking-wide transition-colors",
                    isActive
                      ? "border-2 border-[var(--color-border)] bg-[var(--color-accent)] text-[#1a1400]"
                      : "border-2 border-transparent text-[var(--color-ink-muted)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-ink)]",
                  )
                }
              >
                <Icon className="h-4 w-4" /> {label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <ReduceMotionToggle className="hidden sm:grid" />
            <Button variant="ghost" size="icon" onClick={toggle} aria-label="Alternar tema">
              {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>
            <NavLink to="/app/profile" className="rd-press flex items-center gap-2" aria-label="Meu perfil">
              <Avatar avatarKey={user?.profile.avatar_key} username={user?.username} size={32} />
              <div className="hidden text-right sm:block">
                <p className="text-sm font-semibold leading-tight">{user?.username}</p>
                <p className="font-display text-[10px] uppercase text-[var(--color-ink-subtle)]">
                  {user?.is_platform_admin ? "Admin" : "Perfil"}
                </p>
              </div>
            </NavLink>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Sair"
              onClick={async () => {
                await logout();
                navigate("/login");
              }}
            >
              <LogOut className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </header>

      <main id="main-content" className="mx-auto max-w-7xl px-4 py-6 pb-[calc(5rem+env(safe-area-inset-bottom))] md:pb-6">
        <Suspense fallback={<div className="rd-fade-in h-[60vh] w-full animate-pulse rounded-[var(--radius-card)] bg-[var(--color-surface-2)]" />}>
          <Outlet />
        </Suspense>
      </main>

      {/* Mobile bottom nav */}
      <nav className="fixed inset-x-0 bottom-0 z-40 flex items-center justify-around border-t-2 border-[var(--color-border)] bg-[var(--color-canvas)]/95 px-2 pb-[calc(0.375rem+env(safe-area-inset-bottom))] pt-1.5 backdrop-blur md:hidden">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex flex-1 flex-col items-center gap-0.5 rounded-lg py-1 text-[10px] font-medium",
                isActive ? "text-[var(--color-accent)]" : "text-[var(--color-ink-subtle)]",
              )
            }
          >
            <Icon className="h-5 w-5" /> {label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
