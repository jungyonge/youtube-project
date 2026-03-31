import { Badge } from "@/components/ui/badge";
import { formatCost } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface JobCostBadgeProps {
  current: number;
  budget: number;
}

export function JobCostBadge({ current, budget }: JobCostBadgeProps) {
  const ratio = budget > 0 ? current / budget : 0;

  const colorClass =
    ratio >= 1
      ? "bg-red-100 text-red-700"
      : ratio >= 0.8
        ? "bg-yellow-100 text-yellow-700"
        : "bg-secondary text-secondary-foreground";

  return (
    <Badge className={cn(colorClass)}>
      {formatCost(current)} / {formatCost(budget)}
    </Badge>
  );
}
