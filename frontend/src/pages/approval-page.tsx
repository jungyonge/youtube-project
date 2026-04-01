import { useParams, Link, Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScriptPreview } from "@/components/approval/script-preview";
import { ApprovalActions } from "@/components/approval/approval-actions";
import { useJobDetail } from "@/hooks/use-jobs";
import { api } from "@/lib/axios";

export default function ApprovalPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const { data: job, isLoading: jobLoading } = useJobDetail(jobId);

  const { data: script, isLoading: scriptLoading } = useQuery({
    queryKey: ["jobs", jobId, "script"],
    queryFn: () => api.jobs.getScript(jobId!),
    enabled: !!jobId,
  });

  // If not awaiting approval, redirect to detail page (check before script load)
  if (job && job.phase !== "awaiting_approval") {
    return <Navigate to={`/jobs/${job.job_id}`} replace />;
  }

  if (jobLoading || scriptLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!job || !script) {
    return (
      <div className="py-20 text-center text-muted-foreground">
        데이터를 불러올 수 없습니다.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Back */}
      <Button variant="ghost" size="sm" asChild>
        <Link to={`/jobs/${job.job_id}`}>
          <ArrowLeft className="mr-1 h-4 w-4" /> 상세로 돌아가기
        </Link>
      </Button>

      {/* Script Preview */}
      <ScriptPreview script={script} />

      <Separator />

      {/* Actions */}
      <div className="sticky bottom-0 bg-background py-4">
        <ApprovalActions jobId={job.job_id} />
      </div>
    </div>
  );
}
