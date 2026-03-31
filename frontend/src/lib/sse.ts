import { api } from "@/lib/axios";
import type {
  SSEApprovalEvent,
  SSECancelledEvent,
  SSECompletedEvent,
  SSECostWarningEvent,
  SSEFailedEvent,
  SSEProgressEvent,
} from "@/types/api";
import { env } from "@/config/env";

export interface SSEHandlers {
  onProgress?: (event: SSEProgressEvent) => void;
  onApprovalRequired?: (event: SSEApprovalEvent) => void;
  onCostWarning?: (event: SSECostWarningEvent) => void;
  onCompleted?: (event: SSECompletedEvent) => void;
  onFailed?: (event: SSEFailedEvent) => void;
  onCancelled?: (event: SSECancelledEvent) => void;
  onConnectionChange?: (connected: boolean) => void;
}

export interface SSEConnection {
  close: () => void;
}

const MAX_RETRIES = 5;
const RETRY_DELAY_MS = 3_000;

export function createJobSSE(
  jobId: string,
  token: string,
  handlers: SSEHandlers,
): SSEConnection {
  let eventSource: EventSource | null = null;
  let retryCount = 0;
  let closed = false;
  let retryTimeout: ReturnType<typeof setTimeout> | null = null;

  function connect() {
    if (closed) return;

    const url = `${env.API_BASE_URL}/api/v1/videos/${jobId}/stream?token=${encodeURIComponent(token)}`;
    eventSource = new EventSource(url);

    eventSource.onopen = () => {
      retryCount = 0;
      handlers.onConnectionChange?.(true);

      // 재연결 시 상태 동기화 — 누락된 이벤트 보정
      api.jobs.getStatus(jobId).then((status) => {
        handlers.onProgress?.({
          type: "progress",
          phase: status.phase,
          progress_percent: status.progress_percent,
          current_step_detail: status.current_step_detail,
          cost_usd: status.total_cost_usd,
        });
      });
    };

    eventSource.addEventListener("progress", (e) => {
      const data = JSON.parse((e as MessageEvent).data) as SSEProgressEvent;
      handlers.onProgress?.(data);
    });

    eventSource.addEventListener("approval_required", (e) => {
      const data = JSON.parse((e as MessageEvent).data) as SSEApprovalEvent;
      handlers.onApprovalRequired?.(data);
    });

    eventSource.addEventListener("cost_warning", (e) => {
      const data = JSON.parse((e as MessageEvent).data) as SSECostWarningEvent;
      handlers.onCostWarning?.(data);
    });

    eventSource.addEventListener("completed", (e) => {
      const data = JSON.parse((e as MessageEvent).data) as SSECompletedEvent;
      handlers.onCompleted?.(data);
      cleanup();
    });

    eventSource.addEventListener("failed", (e) => {
      const data = JSON.parse((e as MessageEvent).data) as SSEFailedEvent;
      handlers.onFailed?.(data);
      cleanup();
    });

    eventSource.addEventListener("cancelled", (e) => {
      const data = JSON.parse((e as MessageEvent).data) as SSECancelledEvent;
      handlers.onCancelled?.(data);
      cleanup();
    });

    eventSource.onerror = () => {
      eventSource?.close();
      eventSource = null;

      if (closed) return;

      retryCount++;
      if (retryCount <= MAX_RETRIES) {
        handlers.onConnectionChange?.(false);
        retryTimeout = setTimeout(connect, RETRY_DELAY_MS);
      } else {
        // 5회 실패 → 연결 포기
        handlers.onConnectionChange?.(false);
      }
    };
  }

  function cleanup() {
    closed = true;
    if (retryTimeout) {
      clearTimeout(retryTimeout);
      retryTimeout = null;
    }
    eventSource?.close();
    eventSource = null;
  }

  connect();

  return { close: cleanup };
}
