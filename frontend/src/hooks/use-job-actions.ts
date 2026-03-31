import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/axios";
import type { JobStatusResponse } from "@/types/api";

export function useCancelJob(jobId: string) {
  const queryClient = useQueryClient();

  return {
    ...useMutation({
      mutationFn: () => api.jobs.cancel(jobId),
      onMutate: async () => {
        await queryClient.cancelQueries({ queryKey: ["jobs", jobId] });
        const previous = queryClient.getQueryData<JobStatusResponse>(["jobs", jobId]);
        queryClient.setQueryData<JobStatusResponse>(["jobs", jobId], (old) =>
          old ? { ...old, phase: "cancelled", is_cancelled: true } : old,
        );
        return { previous };
      },
      onError: (_err, _vars, context) => {
        if (context?.previous) {
          queryClient.setQueryData(["jobs", jobId], context.previous);
        }
        toast.error("취소에 실패했습니다.");
      },
      onSuccess: () => {
        toast.success("작업이 취소되었습니다.");
      },
      onSettled: () => {
        queryClient.invalidateQueries({ queryKey: ["jobs"] });
        queryClient.invalidateQueries({ queryKey: ["jobs", jobId] });
        queryClient.invalidateQueries({ queryKey: ["jobs", jobId, "steps"] });
      },
    }),
    cancel() {
      this.mutate();
    },
  };
}

export function useApproveJob(jobId: string) {
  const queryClient = useQueryClient();

  return {
    ...useMutation({
      mutationFn: () => api.jobs.approve(jobId),
      onMutate: async () => {
        await queryClient.cancelQueries({ queryKey: ["jobs", jobId] });
        const previous = queryClient.getQueryData<JobStatusResponse>(["jobs", jobId]);
        queryClient.setQueryData<JobStatusResponse>(["jobs", jobId], (old) =>
          old ? { ...old, phase: "generating_assets", human_approved: true } : old,
        );
        return { previous };
      },
      onError: (_err, _vars, context) => {
        if (context?.previous) {
          queryClient.setQueryData(["jobs", jobId], context.previous);
        }
        toast.error("승인에 실패했습니다.");
      },
      onSuccess: () => {
        toast.success("대본이 승인되었습니다.");
      },
      onSettled: () => {
        queryClient.invalidateQueries({ queryKey: ["jobs"] });
        queryClient.invalidateQueries({ queryKey: ["jobs", jobId] });
        queryClient.invalidateQueries({ queryKey: ["jobs", jobId, "steps"] });
      },
    }),
    approve() {
      this.mutate();
    },
  };
}

export function useRejectJob(jobId: string) {
  const queryClient = useQueryClient();

  return {
    ...useMutation({
      mutationFn: (reason?: string) => api.jobs.reject(jobId, reason),
      onMutate: async () => {
        await queryClient.cancelQueries({ queryKey: ["jobs", jobId] });
        const previous = queryClient.getQueryData<JobStatusResponse>(["jobs", jobId]);
        queryClient.setQueryData<JobStatusResponse>(["jobs", jobId], (old) =>
          old ? { ...old, phase: "rejected" } : old,
        );
        return { previous };
      },
      onError: (_err, _vars, context) => {
        if (context?.previous) {
          queryClient.setQueryData(["jobs", jobId], context.previous);
        }
        toast.error("거부에 실패했습니다.");
      },
      onSuccess: () => {
        toast.success("대본이 거부되었습니다.");
      },
      onSettled: () => {
        queryClient.invalidateQueries({ queryKey: ["jobs"] });
        queryClient.invalidateQueries({ queryKey: ["jobs", jobId] });
        queryClient.invalidateQueries({ queryKey: ["jobs", jobId, "steps"] });
      },
    }),
    reject(reason?: string) {
      this.mutate(reason);
    },
  };
}

export function useRetryJob(jobId: string) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (opts?: { from_step?: string; cost_budget_usd?: number }) =>
      api.jobs.retry(jobId, opts),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      toast.success("재시도 작업이 생성되었습니다.");
      navigate(`/jobs/${data.job_id}`);
    },
    onError: () => {
      toast.error("재시도에 실패했습니다.");
    },
  });
}
