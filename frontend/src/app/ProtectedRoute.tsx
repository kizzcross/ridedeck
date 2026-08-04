import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Skeleton } from "@/components/ui";

export function ProtectedRoute({ adminOnly = false }: { adminOnly?: boolean }) {
  const { status, user } = useAuth();
  const location = useLocation();

  if (status === "idle" || status === "loading") {
    return (
      <div className="mx-auto max-w-5xl space-y-4 p-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (status === "anonymous" || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (adminOnly && !user.is_platform_admin) {
    return <Navigate to="/app" replace />;
  }

  return <Outlet />;
}
