import { useState } from "react";
import { Ban, RotateCcw, Download, CheckCircle, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { TERMINAL_STATES } from "@/types/api";
import type { JobPhase } from "@/types/api";
import {
  useCancelJob,
  useApproveJob,
  useRejectJob,
  useRetryJob,
} from "@/hooks/use-job-actions";
import { env } from "@/config/env";

interface JobActionsProps {
  jobId: string;
  phase: JobPhase;
}

export function JobActions({ jobId, phase }: JobActionsProps) {
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  const cancelJob = useCancelJob(jobId);
  const approveJob = useApproveJob(jobId);
  const rejectJob = useRejectJob(jobId);
  const retryJob = useRetryJob(jobId);

  const canCancel = !TERMINAL_STATES.includes(phase);
  const canApprove = phase === "awaiting_approval";
  const canReject = phase === "awaiting_approval";
  const canRetry = TERMINAL_STATES.includes(phase);
  const canDownload = phase === "completed";

  return (
    <div className="flex flex-wrap gap-2">
      {canApprove && (
        <Button
          size="sm"
          onClick={() => approveJob.approve()}
          disabled={approveJob.isPending}
        >
          <CheckCircle className="mr-1 h-4 w-4" />
          {approveJob.isPending ? "승인 중..." : "승인"}
        </Button>
      )}

      {canReject && (
        <>
          <Button
            size="sm"
            variant="destructive"
            onClick={() => setRejectOpen(true)}
            disabled={rejectJob.isPending}
          >
            <XCircle className="mr-1 h-4 w-4" />
            거부
          </Button>
          <Dialog open={rejectOpen} onOpenChange={setRejectOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>대본 거부</DialogTitle>
                <DialogDescription>
                  거부 사유를 입력하세요 (선택).
                </DialogDescription>
              </DialogHeader>
              <Textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="거부 사유..."
                rows={3}
              />
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setRejectOpen(false)}
                >
                  취소
                </Button>
                <Button
                  variant="destructive"
                  disabled={rejectJob.isPending}
                  onClick={() => {
                    rejectJob.reject(rejectReason || undefined);
                    setRejectOpen(false);
                    setRejectReason("");
                  }}
                >
                  거부 확인
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </>
      )}

      {canCancel && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => cancelJob.cancel()}
          disabled={cancelJob.isPending}
        >
          <Ban className="mr-1 h-4 w-4" />
          {cancelJob.isPending ? "취소 중..." : "취소"}
        </Button>
      )}

      {canRetry && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => retryJob.mutate(undefined)}
          disabled={retryJob.isPending}
        >
          <RotateCcw className="mr-1 h-4 w-4" />
          {retryJob.isPending ? "재시도 중..." : "재시도"}
        </Button>
      )}

      {canDownload && (
        <Button size="sm" variant="outline" asChild>
          <a
            href={`${env.API_BASE_URL}/api/v1/videos/${jobId}/download`}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Download className="mr-1 h-4 w-4" />
            다운로드
          </a>
        </Button>
      )}
    </div>
  );
}
