import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/axios";
import { useAuthStore } from "@/stores/auth-store";

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      api.auth.login(email, password),
    onSuccess: (data) => {
      setAuth(data.access_token, data.user);
      toast.success("로그인 성공");
      navigate("/dashboard", { replace: true });
    },
    onError: () => {
      toast.error("이메일 또는 비밀번호가 올바르지 않습니다.");
    },
  });
}

export function useRegister() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      api.auth.register(email, password),
    onSuccess: (data) => {
      setAuth(data.access_token, data.user);
      toast.success("회원가입 완료");
      navigate("/dashboard", { replace: true });
    },
    onError: () => {
      toast.error("회원가입에 실패했습니다. 이미 존재하는 이메일일 수 있습니다.");
    },
  });
}

export function useMe() {
  const token = useAuthStore((s) => s.token);
  const setUser = useAuthStore((s) => s.setUser);

  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const user = await api.auth.me();
      setUser(user);
      return user;
    },
    enabled: !!token,
    staleTime: 5 * 60 * 1000, // 5분
  });
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return () => {
    logout();
    queryClient.clear();
    navigate("/login", { replace: true });
  };
}
