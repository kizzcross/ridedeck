import { StrictMode, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import "./styles/index.css";
import { router } from "./app/router";
import { QueryProvider } from "./app/query";
import { ThemeProvider } from "./app/theme";
import { ToastProvider } from "./components/ui";
import { useAuth } from "./hooks/useAuth";

function Root() {
  const bootstrap = useAuth((s) => s.bootstrap);
  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  return (
    <ThemeProvider>
      <QueryProvider>
        <ToastProvider>
          <RouterProvider router={router} />
        </ToastProvider>
      </QueryProvider>
    </ThemeProvider>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
