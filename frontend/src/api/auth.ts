import { api } from "@/lib/api";
import type { TokenPair, User } from "./types";

export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
  password_confirm: string;
  referral_code?: string;
}

export const authApi = {
  async register(payload: RegisterPayload): Promise<User> {
    const { data } = await api.post<User>("/auth/register/", payload);
    return data;
  },
  async login(email: string, password: string): Promise<TokenPair> {
    const { data } = await api.post<TokenPair>("/auth/login/", { email, password });
    return data;
  },
  async logout(refresh: string): Promise<void> {
    await api.post("/auth/logout/", { refresh });
  },
  async me(): Promise<User> {
    const { data } = await api.get<User>("/me/");
    return data;
  },
};
