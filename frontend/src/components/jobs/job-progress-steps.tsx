import { CheckCircle, Circle, Loader2, XCircle, SkipForward } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { JobStepDetail } from "@/types/api";
import { formatDuration, formatCost } from "@/lib/utils";

interface JobProgressStepsProps {
  steps: JobStepDetail[];
}

const STATUS_ICON = {
  pending: <Circle className="h-4 w-4 text-muted-foreground" />,
  running: <Loader2 className="h-4 w-4 animate-spin text-blue-500" />,
  completed: <CheckCircle className="h-4 w-4 text-green-500" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
  skipped: <SkipForward className="h-4 w-4 text-muted-foreground" />,
};

export function JobProgressSteps({ steps }: JobProgressStepsProps) {
  if (steps.length === 0) {
    return (
      <p className="py-8 text-center text-muted-foreground">
        실행 기록이 없습니다.
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-10" />
          <TableHead>단계</TableHead>
          <TableHead>상태</TableHead>
          <TableHead className="text-right">소요 시간</TableHead>
          <TableHead className="text-right">비용</TableHead>
          <TableHead>오류</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {steps.map((step) => (
          <TableRow key={step.step_name}>
            <TableCell>{STATUS_ICON[step.status]}</TableCell>
            <TableCell className="font-medium">{step.step_name}</TableCell>
            <TableCell>{step.status}</TableCell>
            <TableCell className="text-right">
              {step.duration_sec != null
                ? formatDuration(step.duration_sec)
                : "-"}
            </TableCell>
            <TableCell className="text-right">
              {formatCost(step.cost_usd)}
            </TableCell>
            <TableCell className="max-w-[200px] truncate text-red-600">
              {step.error_message ?? "-"}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
