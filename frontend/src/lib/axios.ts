import axios from "axios";
import { toast } from "sonner";
import { env } from "@/config/env";
import { useAuthStore } from "@/stores/auth-store";
import type { AuthResponse, User } from "@/types/user";
import type {
  AdminJobItem,
  AdminStats,
  DailyStatsItem,
  FullScript,
  JobStatusResponse,
  JobStepDetail,
  PaginatedResponse,
  VideoGenerationRequest,
} from "@/types/api";

const client = axios.create({
  baseURL: env.API_BASE_URL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// ── Request Interceptor ──────────────────────────────────────────
client.interceptors.request.use((config) => {
  const { token } = useAuthStore.getState();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response Interceptor ─────────────────────────────────────────
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!axios.isAxiosError(error) || !error.response) {
      toast.error("네트워크 오류가 발생했습니다.");
      return Promise.reject(error);
    }

    const { status } = error.response;

    if (status === 401) {
      const url = error.config?.url || "";
      if (!url.startsWith("/auth/")) {
        useAuthStore.getState().logout();
        window.location.href = "/login";
      }
      return Promise.reject(error);
    }

    if (status === 409) {
      // 멱등성 중복 — 기존 job_id 반환
      return Promise.reject(error);
    }

    if (status === 429) {
      toast.error("요청 제한을 초과했습니다. 잠시 후 다시 시도해주세요.");
      return Promise.reject(error);
    }

    if (status >= 500) {
      toast.error("서버 오류가 발생했습니다.");
      return Promise.reject(error);
    }

    return Promise.reject(error);
  },
);

// ── Type-safe API functions ──────────────────────────────────────

export const api = {
  auth: {
    login: (email: string, password: string) =>
      client
        .post<AuthResponse>("/auth/login", { email, password })
        .then((r) => r.data),

    register: (email: string, password: string) =>
      client
        .post<AuthResponse>("/auth/register", { email, password })
        .then((r) => r.data),

    me: () => client.get<User>("/auth/me").then((r) => r.data),
  },

  jobs: {
    create: (req: VideoGenerationRequest) =>
      client
        .post<{ job_id: string }>("/api/v1/videos", req)
        .then((r) => r.data),

    list: (params?: { page?: number; size?: number; status?: string }) =>
      client
        .get<PaginatedResponse<JobStatusResponse>>("/api/v1/videos", { params })
        .then((r) => r.data),

    getStatus: (jobId: string) =>
      client
        .get<JobStatusResponse>(`/api/v1/videos/${jobId}`)
        .then((r) => r.data),

    getSteps: (jobId: string) =>
      client
        .get<JobStepDetail[]>(`/api/v1/videos/${jobId}/steps`)
        .then((r) => r.data),

    getScript: (jobId: string) =>
      client
        .get<FullScript>(`/api/v1/videos/${jobId}/script`)
        .then((r) => r.data),

    getPlaybackUrl: (jobId: string) =>
      client
        .get<{ url: string }>(`/api/v1/videos/${jobId}/playback`)
        .then((r) => r.data),

    cancel: (jobId: string) =>
      client
        .post<{ status: string }>(`/api/v1/videos/${jobId}/cancel`)
        .then((r) => r.data),

    approve: (jobId: string) =>
      client
        .post<{ status: string }>(`/api/v1/videos/${jobId}/approve`)
        .then((r) => r.data),

    reject: (jobId: string, reason?: string) =>
      client
        .post<{ status: string }>(`/api/v1/videos/${jobId}/reject`, { reason })
        .then((r) => r.data),

    retry: (
      jobId: string,
      opts?: { from_step?: string; cost_budget_usd?: number },
    ) =>
      client
        .post<{ job_id: string; parent_job_id: string }>(
          `/api/v1/videos/${jobId}/retry`,
          opts,
        )
        .then((r) => r.data),
  },

  admin: {
    getStats: () =>
      client.get("/admin/stats").then((r) => {
        const d = r.data;
        // Map nested BE response to flat FE AdminStats
        if (d.jobs !== undefined) {
          const created = d.jobs?.created ?? 0;
          const completed = d.jobs?.completed ?? 0;
          const failed = d.jobs?.failed ?? 0;
          return {
            today_jobs: created,
            success_rate: created > 0 ? completed / created : 0,
            daily_cost_usd: d.cost?.total_usd ?? 0,
            active_jobs: d.jobs?.active ?? 0,
          } as AdminStats;
        }
        return d as AdminStats;
      }),

    getDailyStats: (days: number = 30) =>
      client
        .get<DailyStatsItem[]>("/admin/stats/daily", { params: { days } })
        .then((r) => r.data),

    getJobs: (filters?: {
      page?: number;
      size?: number;
      status?: string;
      user_email?: string;
    }) =>
      client
        .get<PaginatedResponse<AdminJobItem>>("/admin/jobs", {
          params: filters,
        })
        .then((r) => r.data),

    forceCancel: (jobId: string) =>
      client.post(`/admin/jobs/${jobId}/force-cancel`).then(() => undefined),
  },
} as const;

export default client;
