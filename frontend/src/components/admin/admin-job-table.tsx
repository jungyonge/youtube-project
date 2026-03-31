import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Ban, Eye, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdminJobs, useForceCancel } from "@/hooks/use-admin-stats";
import { PHASE_COLORS, PHASE_LABELS } from "@/types/job";
import { TERMINAL_STATES } from "@/types/api";
import { formatCost, formatDate } from "@/lib/utils";

const STATUS_OPTIONS = [
  { value: "all", label: "전체" },
  { value: "queued", label: "대기" },
  { value: "extracting", label: "추출 중" },
  { value: "generating_script", label: "대본 생성" },
  { value: "awaiting_approval", label: "승인 대기" },
  { value: "generating_assets", label: "에셋 생성" },
  { value: "assembling_video", label: "영상 조립" },
  { value: "completed", label: "완료" },
  { value: "failed", label: "실패" },
  { value: "cancelled", label: "취소" },
];

export function AdminJobTable() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("all");
  const [emailFilter, setEmailFilter] = useState("");

  const { data, isLoading } = useAdminJobs({
    page,
    size: 20,
    status: statusFilter === "all" ? undefined : statusFilter,
    user_email: emailFilter || undefined,
  });

  const forceCancel = useForceCancel();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">전체 작업</CardTitle>
        <div className="flex flex-wrap gap-2 pt-2">
          <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {STATUS_OPTIONS.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            placeholder="이메일 검색..."
            value={emailFilter}
            onChange={(e) => { setEmailFilter(e.target.value); setPage(1); }}
            className="w-48"
          />
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : !data || data.items.length === 0 ? (
          <p className="py-8 text-center text-muted-foreground">
            작업이 없습니다.
          </p>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>사용자</TableHead>
                  <TableHead>주제</TableHead>
                  <TableHead>상태</TableHead>
                  <TableHead className="text-right">비용</TableHead>
                  <TableHead>생성일</TableHead>
                  <TableHead className="w-24" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((job) => (
                  <TableRow key={job.job_id}>
                    <TableCell className="text-xs">{job.user_email}</TableCell>
                    <TableCell className="max-w-[200px] truncate">
                      {job.topic}
                    </TableCell>
                    <TableCell>
                      <Badge className={PHASE_COLORS[job.phase]}>
                        {PHASE_LABELS[job.phase]}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCost(job.total_cost_usd)}
                    </TableCell>
                    <TableCell className="text-xs">
                      {formatDate(job.created_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => navigate(`/jobs/${job.job_id}`)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {!TERMINAL_STATES.includes(job.phase) && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => forceCancel.mutate(job.job_id)}
                            disabled={forceCancel.isPending}
                          >
                            <Ban className="h-4 w-4 text-destructive" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {/* Pagination */}
            {(data.has_next || page > 1) && (
              <div className="flex justify-center gap-2 pt-4">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  이전
                </Button>
                <span className="flex items-center text-sm text-muted-foreground">
                  {page} / {Math.ceil(data.total / 20)}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!data.has_next}
                  onClick={() => setPage((p) => p + 1)}
                >
                  다음
                </Button>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
