import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { JobStatusResponse } from "@/types/api";
import { PHASE_COLORS, PHASE_LABELS } from "@/types/job";
import { formatCost, formatDate } from "@/lib/utils";

interface JobCardProps {
  job: JobStatusResponse;
}

export function JobCard({ job }: JobCardProps) {
  const navigate = useNavigate();

  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={() => navigate(`/jobs/${job.job_id}`)}
    >
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <Badge className={PHASE_COLORS[job.phase]}>
            {PHASE_LABELS[job.phase]}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {formatDate(job.created_at, "relative")}
          </span>
        </div>

        {/* Progress bar */}
        <div className="space-y-1">
          <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full rounded-full bg-primary transition-all duration-300"
              style={{ width: `${job.progress_percent}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{job.current_step_detail || `${job.progress_percent}%`}</span>
            <span>{formatCost(job.total_cost_usd)} / {formatCost(job.cost_budget_usd)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
