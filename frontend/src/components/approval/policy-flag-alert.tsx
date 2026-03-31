import { AlertTriangle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

interface PolicyFlagAlertProps {
  sensitivity: "low" | "medium" | "high";
  warnings: string[];
}

const SENSITIVITY_MAP = {
  low: { label: "낮음", color: "bg-green-100 text-green-700" },
  medium: { label: "보통", color: "bg-yellow-100 text-yellow-700" },
  high: { label: "높음", color: "bg-red-100 text-red-700" },
};

export function PolicyFlagAlert({
  sensitivity,
  warnings,
}: PolicyFlagAlertProps) {
  if (warnings.length === 0) return null;

  const s = SENSITIVITY_MAP[sensitivity];

  return (
    <Alert variant="destructive">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle className="flex items-center gap-2">
        민감 주제 - 승인 필요
        <Badge className={s.color}>{s.label}</Badge>
      </AlertTitle>
      <AlertDescription>
        <div className="mt-2 flex flex-wrap gap-1">
          {warnings.map((w) => (
            <Badge key={w} variant="outline" className="text-xs">
              {w}
            </Badge>
          ))}
        </div>
      </AlertDescription>
    </Alert>
  );
}
