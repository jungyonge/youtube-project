import { useEffect, useRef, useState, useCallback } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { createJobSSE, type SSEConnection } from "@/lib/sse";
import { useAuthStore } from "@/stores/auth-store";
import { api } from "@/lib/axios";
import type { JobPhase, JobStatusResponse } from "@/types/api";
import { TERMINAL_STATES } from "@/types/api";

interface StreamState {
  phase: JobPhase;
  progress_percent: number;
  current_step_detail: string;
  cost_usd: number;
  isConnected: boolean;
  isFallbackPolling: boolean;
}

export function useJobStream(jobId: string | undefined, initialJob?: JobStatusResponse) {
  const token = useAuthStore((s) => s.token);
  const queryClient = useQueryClient();
  const sseRef = useRef<SSEConnection | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [state, setState] = useState<StreamState>({
    phase: initialJob?.phase ?? "queued",
    progress_percent: initialJob?.progress_percent ?? 0,
    current_step_detail: initialJob?.current_step_detail ?? "",
    cost_usd: initialJob?.total_cost_usd ?? 0,
    isConnected: false,
    isFallbackPolling: false,
  });

  const invalidateJob = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["jobs", jobId] });
    queryClient.invalidateQueries({ queryKey: ["jobs", jobId, "steps"] });
    queryClient.invalidateQueries({ queryKey: ["jobs"] });
  }, [queryClient, jobId]);

  // Start fallback polling
  const startPolling = useCallback(() => {
    if (!jobId || pollingRef.current) return;
    setState((s) => ({ ...s, isFallbackPolling: true }));
    pollingRef.current = setInterval(async () => {
      try {
        const status = await api.jobs.getStatus(jobId);
        setState((s) => ({
          ...s,
          phase: status.phase,
          progress_percent: status.progress_percent,
          current_step_detail: status.current_step_detail,
          cost_usd: status.total_cost_usd,
        }));
        if (TERMINAL_STATES.includes(status.phase) && pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          invalidateJob();
        }
      } catch {
        // ignore polling errors
      }
    }, 5_000);
  }, [jobId, invalidateJob]);

  useEffect(() => {
    if (!jobId || !token) return;

    // Don't connect for terminal states
    if (initialJob && TERMINAL_STATES.includes(initialJob.phase)) return;

    sseRef.current = createJobSSE(jobId, token, {
      onProgress: (event) => {
        setState((s) => ({
          ...s,
          phase: event.phase,
          progress_percent: event.progress_percent,
          current_step_detail: event.current_step_detail,
          cost_usd: event.cost_usd,
        }));
      },
      onApprovalRequired: (event) => {
        setState((s) => ({ ...s, phase: "awaiting_approval" }));
        toast.info(`대본 승인이 필요합니다 (민감도: ${event.sensitivity_level})`);
        invalidateJob();
      },
      onCostWarning: (event) => {
        toast.warning(
          `비용 경고: $${event.current_cost.toFixed(2)} / $${event.budget.toFixed(2)}`,
        );
      },
      onCompleted: () => {
        setState((s) => ({
          ...s,
          phase: "completed",
          progress_percent: 100,
          current_step_detail: "완료",
        }));
        toast.success("영상 생성이 완료되었습니다!");
        invalidateJob();
      },
      onFailed: (event) => {
        setState((s) => ({
          ...s,
          phase: "failed",
          current_step_detail: event.error_message,
        }));
        toast.error(`생성 실패: ${event.error_message}`);
        invalidateJob();
      },
      onCancelled: () => {
        setState((s) => ({
          ...s,
          phase: "cancelled",
          current_step_detail: "취소됨",
        }));
        invalidateJob();
      },
      onConnectionChange: (connected) => {
        setState((s) => ({ ...s, isConnected: connected }));
        if (!connected) {
          // SSE failed → start polling fallback
          startPolling();
        }
      },
    });

    return () => {
      sseRef.current?.close();
      sseRef.current = null;
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [jobId, token, initialJob, invalidateJob, startPolling]);

  // Sync from initialJob when it updates (from TanStack Query)
  useEffect(() => {
    if (initialJob) {
      setState((s) => ({
        ...s,
        phase: initialJob.phase,
        progress_percent: initialJob.progress_percent,
        current_step_detail: initialJob.current_step_detail,
        cost_usd: initialJob.total_cost_usd,
      }));
    }
  }, [initialJob]);

  return state;
}
