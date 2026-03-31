import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { JobProgress } from "@/components/jobs/job-progress";
import { JobActions } from "@/components/jobs/job-actions";
import { JobDetailPanel } from "@/components/jobs/job-detail-panel";
import { useJobDetail } from "@/hooks/use-jobs";
import { useJobStream } from "@/hooks/use-job-stream";
import { PHASE_COLORS, PHASE_LABELS } from "@/types/job";
import { formatDate } from "@/lib/utils";

export default function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const { data: job, isLoading } = useJobDetail(jobId);

  const stream = useJobStream(jobId, job);

  if (isLoading || !job) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Back */}
      <Button variant="ghost" size="sm" asChild>
        <Link to="/dashboard">
          <ArrowLeft className="mr-1 h-4 w-4" /> 대시보드
        </Link>
      </Button>

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Badge className={PHASE_COLORS[stream.phase]}>
            {PHASE_LABELS[stream.phase]}
          </Badge>
          <span className="text-sm text-muted-foreground">
            {formatDate(job.created_at)}
          </span>
        </div>
        <JobActions jobId={job.job_id} phase={stream.phase} />
      </div>

      {/* Parent job link */}
      {job.parent_job_id && (
        <p className="text-sm text-muted-foreground">
          원본 작업:{" "}
          <Link
            to={`/jobs/${job.parent_job_id}`}
            className="text-primary hover:underline"
          >
            {job.parent_job_id.slice(0, 8)}...
          </Link>
        </p>
      )}

      {/* Progress */}
      <JobProgress
        phase={stream.phase}
        progressPercent={stream.progress_percent}
        currentStepDetail={stream.current_step_detail}
        costUsd={stream.cost_usd}
        costBudget={job.cost_budget_usd}
        isConnected={stream.isConnected}
        isFallbackPolling={stream.isFallbackPolling}
      />

      <Separator />

      {/* Detail tabs */}
      <JobDetailPanel job={{ ...job, phase: stream.phase }} />
    </div>
  );
}
