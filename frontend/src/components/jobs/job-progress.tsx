import { Wifi, WifiOff, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { JobCostBadge } from "./job-cost-badge";
import { PHASE_LABELS } from "@/types/job";
import type { JobPhase } from "@/types/api";
import { cn } from "@/lib/utils";

const PIPELINE_STEPS: { phase: JobPhase; label: string }[] = [
  { phase: "extracting", label: "추출" },
  { phase: "normalizing", label: "정규화" },
  { phase: "building_evidence", label: "근거" },
  { phase: "generating_script", label: "대본" },
  { phase: "reviewing_script", label: "검수" },
  { phase: "policy_review", label: "정책" },
  { phase: "awaiting_approval", label: "승인" },
  { phase: "generating_assets", label: "에셋" },
  { phase: "assembling_video", label: "조립" },
];

const PHASE_ORDER: Record<string, number> = {};
PIPELINE_STEPS.forEach((s, i) => {
  PHASE_ORDER[s.phase] = i;
});

function getStepStatus(
  stepPhase: JobPhase,
  currentPhase: JobPhase,
): "completed" | "active" | "pending" | "failed" | "approval" {
  if (currentPhase === "failed") {
    const currentIdx = PHASE_ORDER[currentPhase] ?? -1;
    const stepIdx = PHASE_ORDER[stepPhase] ?? -1;
    if (stepIdx < currentIdx) return "completed";
    if (stepIdx === currentIdx) return "failed";
    return "pending";
  }
  if (currentPhase === "completed") return "completed";
  if (currentPhase === "cancelled" || currentPhase === "rejected") {
    const currentIdx = PHASE_ORDER[currentPhase] ?? -1;
    const stepIdx = PHASE_ORDER[stepPhase] ?? -1;
    return stepIdx <= currentIdx ? "completed" : "pending";
  }

  const currentIdx = PHASE_ORDER[currentPhase] ?? -1;
  const stepIdx = PHASE_ORDER[stepPhase] ?? -1;

  if (stepIdx < currentIdx) return "completed";
  if (stepIdx === currentIdx) {
    if (stepPhase === "awaiting_approval") return "approval";
    return "active";
  }
  return "pending";
}

interface JobProgressProps {
  phase: JobPhase;
  progressPercent: number;
  currentStepDetail: string;
  costUsd: number;
  costBudget: number;
  isConnected: boolean;
  isFallbackPolling: boolean;
}

export function JobProgress({
  phase,
  progressPercent,
  currentStepDetail,
  costUsd,
  costBudget,
  isConnected,
  isFallbackPolling,
}: JobProgressProps) {
  return (
    <div className="space-y-4">
      {/* Step indicators */}
      <div className="flex items-center justify-between gap-1 overflow-x-auto pb-2">
        {PIPELINE_STEPS.map((step) => {
          const status = getStepStatus(step.phase, phase);
          return (
            <div
              key={step.phase}
              className="flex flex-col items-center gap-1 min-w-0"
            >
              <div
                className={cn(
                  "h-3 w-3 rounded-full shrink-0",
                  status === "completed" && "bg-green-500",
                  status === "active" && "bg-blue-500 animate-pulse",
                  status === "pending" && "bg-muted-foreground/30",
                  status === "failed" && "bg-red-500",
                  status === "approval" && "bg-yellow-500 animate-pulse",
                )}
              />
              <span className="text-[10px] text-muted-foreground truncate max-w-[3.5rem] text-center">
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="h-3 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-500",
              phase === "failed"
                ? "bg-red-500"
                : phase === "completed"
                  ? "bg-green-500"
                  : "bg-primary animate-shimmer bg-[length:200%_100%] bg-gradient-to-r from-primary via-primary/70 to-primary",
            )}
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground truncate mr-4">
            {currentStepDetail || PHASE_LABELS[phase] || `${progressPercent}%`}
          </span>
          <div className="flex items-center gap-2 shrink-0">
            <JobCostBadge current={costUsd} budget={costBudget} />
            {/* Connection status */}
            {isConnected ? (
              <Badge variant="outline" className="gap-1 text-green-600">
                <Wifi className="h-3 w-3" /> 실시간
              </Badge>
            ) : isFallbackPolling ? (
              <Badge variant="outline" className="gap-1 text-yellow-600">
                <RefreshCw className="h-3 w-3" /> 폴링
              </Badge>
            ) : (
              <Badge variant="outline" className="gap-1 text-red-600">
                <WifiOff className="h-3 w-3" /> 끊김
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
