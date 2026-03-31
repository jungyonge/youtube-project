import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { SceneClaim } from "@/types/api";
import { CLAIM_BADGES } from "@/types/job";

interface ClaimBadgeProps {
  claim: SceneClaim;
}

export function ClaimBadge({ claim }: ClaimBadgeProps) {
  const style = CLAIM_BADGES[claim.claim_type] ?? {
    color: "bg-muted text-muted-foreground",
    label: claim.claim_type,
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge className={style.color}>
            {style.label}: {claim.claim_text}
            <span className="ml-1 opacity-60">
              ({(claim.confidence * 100).toFixed(0)}%)
            </span>
          </Badge>
        </TooltipTrigger>
        {claim.evidence_quote && (
          <TooltipContent className="max-w-xs">
            <p className="text-xs">근거: {claim.evidence_quote}</p>
          </TooltipContent>
        )}
      </Tooltip>
    </TooltipProvider>
  );
}
