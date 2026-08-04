import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "./AppShell";
import { ProtectedRoute } from "./ProtectedRoute";
import { LandingPage } from "@/pages/LandingPage";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { CatalogPage } from "@/pages/CatalogPage";
import { MyDecksPage } from "@/pages/MyDecksPage";
import { DeckBuilderPage } from "@/pages/DeckBuilderPage";
import { DeckViewPage } from "@/pages/DeckViewPage";
import { CollectionPage } from "@/pages/CollectionPage";
import { BanlistsPage } from "@/pages/BanlistsPage";
import { BanlistDetailPage } from "@/pages/BanlistDetailPage";
import { TournamentsPage } from "@/pages/TournamentsPage";
import { TournamentDetailPage } from "@/pages/TournamentDetailPage";
import { PowerLevelAdminPage } from "@/pages/admin/PowerLevelAdminPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { PublicProfilePage } from "@/pages/PublicProfilePage";
import { NotFoundPage } from "@/pages/NotFoundPage";

export const router = createBrowserRouter([
  { path: "/", element: <LandingPage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
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
          { path: "decks/:uuid/view", element: <DeckViewPage /> },
          { path: "collection", element: <CollectionPage /> },
          { path: "banlists", element: <BanlistsPage /> },
          { path: "banlists/:uuid", element: <BanlistDetailPage /> },
          { path: "tournaments", element: <TournamentsPage /> },
          { path: "tournaments/:uuid", element: <TournamentDetailPage /> },
        ],
      },
    ],
  },
  {
    element: <ProtectedRoute adminOnly />,
    children: [
      {
        path: "/admin",
        element: <AppShell />,
        children: [
          { index: true, element: <Navigate to="/admin/power-levels" replace /> },
          { path: "power-levels", element: <PowerLevelAdminPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
