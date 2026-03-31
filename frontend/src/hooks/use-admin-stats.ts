import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/axios";

export function useAdminStats() {
  return useQuery({
    queryKey: ["admin", "stats"],
    queryFn: () => api.admin.getStats(),
    refetchInterval: 30_000,
  });
}

export function useAdminDailyStats(days: number = 30) {
  return useQuery({
    queryKey: ["admin", "daily-stats", days],
    queryFn: () => api.admin.getDailyStats(days),
  });
}

export function useAdminJobs(filters?: {
  page?: number;
  size?: number;
  status?: string;
  user_email?: string;
}) {
  return useQuery({
    queryKey: ["admin", "jobs", filters],
    queryFn: () => api.admin.getJobs(filters),
    refetchInterval: 15_000,
  });
}

export function useForceCancel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: string) => api.admin.forceCancel(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "jobs"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "stats"] });
      toast.success("강제 취소되었습니다.");
    },
    onError: () => {
      toast.error("강제 취소에 실패했습니다.");
    },
  });
}
