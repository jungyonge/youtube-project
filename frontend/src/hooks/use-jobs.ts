import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import { api } from "@/lib/axios";
import type { JobPhase, VideoGenerationRequest } from "@/types/api";

export function useJobList(params?: {
  page?: number;
  size?: number;
  status?: string;
}) {
  return useQuery({
    queryKey: ["jobs", params],
    queryFn: () => api.jobs.list(params),
    refetchInterval: 10_000, // 10초마다 갱신
  });
}

export function useJobDetail(jobId: string | undefined) {
  return useQuery({
    queryKey: ["jobs", jobId],
    queryFn: () => api.jobs.getStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const phase = query.state.data?.phase;
      if (!phase) return false;
      const terminal: JobPhase[] = ["completed", "failed", "cancelled", "rejected"];
      return terminal.includes(phase) ? false : 5_000;
    },
  });
}

export function useJobSteps(jobId: string | undefined) {
  return useQuery({
    queryKey: ["jobs", jobId, "steps"],
    queryFn: () => api.jobs.getSteps(jobId!),
    enabled: !!jobId,
    refetchInterval: 10_000,
  });
}

export function usePlaybackUrl(jobId: string | undefined, phase?: JobPhase) {
  return useQuery({
    queryKey: ["jobs", jobId, "playback"],
    queryFn: () => api.jobs.getPlaybackUrl(jobId!),
    enabled: !!jobId && phase === "completed",
    staleTime: 30 * 60 * 1000, // 30분
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (req: VideoGenerationRequest) => api.jobs.create(req),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      toast.success("영상 생성이 시작되었습니다.");
      navigate(`/jobs/${data.job_id}`);
    },
    onError: (error) => {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        const existingJobId = error.response.data?.job_id;
        if (existingJobId) {
          toast.info("이미 동일한 요청이 있습니다.");
          navigate(`/jobs/${existingJobId}`);
          return;
        }
      }
      toast.error("영상 생성에 실패했습니다.");
    },
  });
}
