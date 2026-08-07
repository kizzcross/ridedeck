import { lazy, Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "./AppShell";
import { ProtectedRoute } from "./ProtectedRoute";
import { LandingPage } from "@/pages/LandingPage";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { DashboardPage } from "@/pages/DashboardPage";

// Heavy routes are code-split so the main bundle stays lean (framer-motion,
// dnd-kit and the championship UI load only when their page is visited).
const named = <T extends string>(p: Promise<Record<T, React.ComponentType>>, k: T) =>
  p.then((m) => ({ default: m[k] }));
const CatalogPage = lazy(() => named(import("@/pages/CatalogPage"), "CatalogPage"));
const MyDecksPage = lazy(() => named(import("@/pages/MyDecksPage"), "MyDecksPage"));
const DeckBuilderPage = lazy(() => named(import("@/pages/DeckBuilderPage"), "DeckBuilderPage"));
const CollectionPage = lazy(() => named(import("@/pages/CollectionPage"), "CollectionPage"));
const BanlistsPage = lazy(() => named(import("@/pages/BanlistsPage"), "BanlistsPage"));
const BanlistDetailPage = lazy(() => named(import("@/pages/BanlistDetailPage"), "BanlistDetailPage"));
const TournamentsPage = lazy(() => named(import("@/pages/TournamentsPage"), "TournamentsPage"));
const TournamentCreateWizardPage = lazy(() => named(import("@/pages/TournamentCreateWizardPage"), "TournamentCreateWizardPage"));
const TournamentDetailPage = lazy(() => named(import("@/pages/TournamentDetailPage"), "TournamentDetailPage"));
const RosterBuilderPage = lazy(() => named(import("@/pages/RosterBuilderPage"), "RosterBuilderPage"));
const RoundBoardPage = lazy(() => named(import("@/pages/RoundBoardPage"), "RoundBoardPage"));
const OwnerControlPanelPage = lazy(() => named(import("@/pages/OwnerControlPanelPage"), "OwnerControlPanelPage"));
const OverlayPage = lazy(() => named(import("@/pages/OverlayPage"), "OverlayPage"));
const ProfilePage = lazy(() => named(import("@/pages/ProfilePage"), "ProfilePage"));
const PublicProfilePage = lazy(() => named(import("@/pages/PublicProfilePage"), "PublicProfilePage"));
import { NotFoundPage } from "@/pages/NotFoundPage";

export const router = createBrowserRouter([
  { path: "/", element: <LandingPage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  { path: "/overlay/:uuid", element: <Suspense fallback={null}><OverlayPage /></Suspense> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: "/app",
        element: <AppShell />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: "cards", element: <CatalogPage /> },
          { path: "profile", element: <ProfilePage /> },
          { path: "u/:username", element: <PublicProfilePage /> },
          { path: "decks", element: <MyDecksPage /> },
          { path: "decks/:uuid", element: <DeckBuilderPage /> },
          { path: "collection", element: <CollectionPage /> },
          { path: "banlists", element: <BanlistsPage /> },
          { path: "banlists/:uuid", element: <BanlistDetailPage /> },
          { path: "tournaments", element: <TournamentsPage /> },
          { path: "tournaments/new", element: <TournamentCreateWizardPage /> },
          { path: "tournaments/:uuid", element: <TournamentDetailPage /> },
          { path: "tournaments/:uuid/roster", element: <RosterBuilderPage /> },
          { path: "tournaments/:uuid/round", element: <RoundBoardPage /> },
          { path: "tournaments/:uuid/manage", element: <OwnerControlPanelPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
