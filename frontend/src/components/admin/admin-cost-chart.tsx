import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DailyStatsItem } from "@/types/api";

interface AdminCostChartProps {
  data: DailyStatsItem[];
}

export function AdminCostChart({ data }: AdminCostChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">일별 비용 추이 (최근 30일)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis
                dataKey="date"
                tickFormatter={(v: string) => v.slice(5)} // MM-DD
                className="text-xs"
              />
              <YAxis
                tickFormatter={(v: number) => `$${v}`}
                className="text-xs"
              />
              <Tooltip
                formatter={(value: number) => [`$${value.toFixed(2)}`, "비용"]}
                labelFormatter={(label: string) => label}
              />
              <Area
                type="monotone"
                dataKey="cost_usd"
                stroke="hsl(var(--primary))"
                fill="url(#colorCost)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
