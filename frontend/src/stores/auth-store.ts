import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types/user";

interface AuthState {
  token: string | null;
  refreshToken: string | null; // MVP에서는 null, 추후 확장
  user: User | null;
  setAuth: (token: string, user: User, refreshToken?: string) => void;
  setToken: (token: string) => void; // Silent Refresh용
  setUser: (user: User) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
  isAdmin: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      user: null,

      setAuth: (token, user, refreshToken) =>
        set({ token, user, refreshToken: refreshToken ?? null }),

      setToken: (token) => set({ token }),

      setUser: (user) => set({ user }),

      logout: () => set({ token: null, refreshToken: null, user: null }),

      isAuthenticated: () => get().token !== null,

      isAdmin: () => get().user?.role === "admin",
    }),
    {
      name: "auth-storage",
      // TODO: PRODUCTION_SECURITY — 프로덕션에서는 localStorage 저장 금지,
      // 메모리만 사용하고 refreshToken은 HttpOnly 쿠키로 전환
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    },
  ),
);
