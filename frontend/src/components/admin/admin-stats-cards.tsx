import { Film, CheckCircle, DollarSign, Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AdminStats } from "@/types/api";
import { formatCost } from "@/lib/utils";

interface AdminStatsCardsProps {
  stats: AdminStats;
}

const CARDS = [
  {
    key: "today_jobs" as const,
    label: "오늘 생성",
    icon: Film,
    format: (v: number) => `${v}건`,
  },
  {
    key: "success_rate" as const,
    label: "성공률",
    icon: CheckCircle,
    format: (v: number) => `${(v * 100).toFixed(1)}%`,
  },
  {
    key: "daily_cost_usd" as const,
    label: "일 비용",
    icon: DollarSign,
    format: (v: number) => formatCost(v),
  },
  {
    key: "active_jobs" as const,
    label: "활성 작업",
    icon: Activity,
    format: (v: number) => `${v}건`,
  },
];

export function AdminStatsCards({ stats }: AdminStatsCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {CARDS.map((card) => (
        <Card key={card.key}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {card.label}
            </CardTitle>
            <card.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {card.format(stats[card.key])}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
