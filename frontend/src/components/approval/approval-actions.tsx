import { useState } from "react";
import { CheckCircle, XCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  useApproveJob,
  useRejectJob,
  useRetryJob,
} from "@/hooks/use-job-actions";

interface ApprovalActionsProps {
  jobId: string;
}

export function ApprovalActions({ jobId }: ApprovalActionsProps) {
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [modifyOpen, setModifyOpen] = useState(false);
  const [modifyInstructions, setModifyInstructions] = useState("");

  const approveJob = useApproveJob(jobId);
  const rejectJob = useRejectJob(jobId);
  const retryJob = useRetryJob(jobId);

  return (
    <div className="flex flex-wrap gap-3">
      {/* Reject */}
      <Button
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
            <Button variant="outline" onClick={() => setRejectOpen(false)}>
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

      {/* Modify (retry from review) */}
      <Button
        variant="outline"
        onClick={() => setModifyOpen(true)}
        disabled={retryJob.isPending}
      >
        <RefreshCw className="mr-1 h-4 w-4" />
        수정 요청
      </Button>
      <Dialog open={modifyOpen} onOpenChange={setModifyOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>수정 요청</DialogTitle>
            <DialogDescription>
              수정할 내용을 지시하세요. 대본 재생성부터 새로 시작됩니다.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label>추가 지시사항</Label>
            <Textarea
              value={modifyInstructions}
              onChange={(e) => setModifyInstructions(e.target.value)}
              placeholder="예: 3번 씬의 투자 예측 표현을 완화해주세요"
              rows={4}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setModifyOpen(false)}>
              취소
            </Button>
            <Button
              disabled={retryJob.isPending || !modifyInstructions.trim()}
              onClick={() => {
                retryJob.mutate({
                  from_step: "review",
                  // additional_instructions는 retry body에 포함되지 않으므로
                  // cost_budget_usd만 전달. 추후 백엔드 확장 시 instructions 추가 가능.
                });
                setModifyOpen(false);
                setModifyInstructions("");
              }}
            >
              수정 요청 확인
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Approve */}
      <Button
        onClick={() => approveJob.approve()}
        disabled={approveJob.isPending}
      >
        <CheckCircle className="mr-1 h-4 w-4" />
        {approveJob.isPending ? "승인 중..." : "승인하고 생성 시작"}
      </Button>
    </div>
  );
}
