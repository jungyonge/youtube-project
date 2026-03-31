import { useState } from "react";
import { Film } from "lucide-react";
import { Button } from "@/components/ui/button";
import { JobCard } from "./job-card";
import { JobListSkeleton } from "./job-list-skeleton";
import { useJobList } from "@/hooks/use-jobs";

export function JobList() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useJobList({ page, size: 20 });

  if (isLoading) {
    return <JobListSkeleton />;
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <Film className="mb-2 h-10 w-10" />
        <p>아직 생성된 영상이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {data.items.map((job) => (
        <JobCard key={job.job_id} job={job} />
      ))}

      {/* Pagination */}
      {(data.has_next || page > 1) && (
        <div className="flex justify-center gap-2 pt-2">
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
    </div>
  );
}
