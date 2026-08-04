import { create } from "zustand";
import { authApi, type RegisterPayload } from "@/api/auth";
import type { User } from "@/api/types";
import { tokenStore } from "@/lib/tokens";

interface AuthState {
  user: User | null;
  status: "idle" | "loading" | "authenticated" | "anonymous";
  bootstrap: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  status: "idle",

  async bootstrap() {
    if (!tokenStore.access) {
      set({ status: "anonymous" });
      return;
    }
    set({ status: "loading" });
    try {
      const user = await authApi.me();
      set({ user, status: "authenticated" });
    } catch {
      tokenStore.clear();
      set({ user: null, status: "anonymous" });
    }
  },

  async login(email, password) {
    const tokens = await authApi.login(email, password);
    tokenStore.set(tokens.access, tokens.refresh);
    const user = await authApi.me();
    set({ user, status: "authenticated" });
  },

  async register(payload) {
    await authApi.register(payload);
    await useAuth.getState().login(payload.email, payload.password);
  },

  async logout() {
    const refresh = tokenStore.refresh;
    if (refresh) {
      try {
        await authApi.logout(refresh);
      } catch {
        /* best effort */
      }
    }
    tokenStore.clear();
    set({ user: null, status: "anonymous" });
  },

  async refreshUser() {
    try {
      const user = await authApi.me();
      set({ user, status: "authenticated" });
    } catch {
      /* ignore */
    }
  },
}));

// React to forced logout from the axios refresh interceptor.
if (typeof window !== "undefined") {
  window.addEventListener("rd:logout", () => {
    tokenStore.clear();
    useAuth.setState({ user: null, status: "anonymous" });
  });
}
