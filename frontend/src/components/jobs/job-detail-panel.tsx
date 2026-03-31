import { useQuery } from "@tanstack/react-query";
import { Loader2, AlertTriangle } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { JobProgressSteps } from "./job-progress-steps";
import { api } from "@/lib/axios";
import type { JobStatusResponse } from "@/types/api";
import { CLAIM_BADGES } from "@/types/job";
import { useJobSteps, usePlaybackUrl } from "@/hooks/use-jobs";
import { env } from "@/config/env";

interface JobDetailPanelProps {
  job: JobStatusResponse;
}

export function JobDetailPanel({ job }: JobDetailPanelProps) {
  const { data: steps, isLoading: stepsLoading } = useJobSteps(job.job_id);
  const { data: playback } = usePlaybackUrl(job.job_id, job.phase);

  const { data: script, isLoading: scriptLoading } = useQuery({
    queryKey: ["jobs", job.job_id, "script"],
    queryFn: () => api.jobs.getScript(job.job_id),
    enabled:
      job.phase === "awaiting_approval" ||
      job.phase === "generating_assets" ||
      job.phase === "assembling_video" ||
      job.phase === "completed" ||
      job.phase === "rejected",
  });

  return (
    <Tabs defaultValue="progress">
      <TabsList>
        <TabsTrigger value="progress">진행 상세</TabsTrigger>
        <TabsTrigger value="script">대본</TabsTrigger>
        <TabsTrigger value="result">결과</TabsTrigger>
      </TabsList>

      {/* Progress Tab */}
      <TabsContent value="progress">
        {stepsLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <JobProgressSteps steps={steps ?? []} />
        )}
      </TabsContent>

      {/* Script Tab */}
      <TabsContent value="script">
        {scriptLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : script ? (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold">{script.title}</h3>
              <p className="text-sm text-muted-foreground">
                {script.subtitle}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {script.tags.map((tag) => (
                  <Badge key={tag} variant="outline">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>

            {script.policy_warnings.length > 0 && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>정책 경고</AlertTitle>
                <AlertDescription>
                  {script.policy_warnings.join(", ")}
                </AlertDescription>
              </Alert>
            )}

            {/* Scenes */}
            <div className="space-y-3">
              {script.scenes.map((scene) => (
                <Card key={scene.scene_id}>
                  <CardContent className="p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">
                        씬 {scene.scene_id}: {scene.section}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {scene.duration_target_sec}초
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {scene.narration}
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {scene.claims.map((claim, i) => {
                        const badge = CLAIM_BADGES[claim.claim_type];
                        return (
                          <Badge
                            key={i}
                            className={badge?.color ?? ""}
                          >
                            {badge?.label ?? claim.claim_type}:{" "}
                            {claim.claim_text}
                          </Badge>
                        );
                      })}
                    </div>
                    {scene.policy_flags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {scene.policy_flags.map((flag) => (
                          <Badge
                            key={flag}
                            variant="destructive"
                            className="text-xs"
                          >
                            {flag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ) : (
          <p className="py-8 text-center text-muted-foreground">
            대본이 아직 생성되지 않았습니다.
          </p>
        )}
      </TabsContent>

      {/* Result Tab */}
      <TabsContent value="result">
        {job.phase === "completed" ? (
          <div className="space-y-4">
            {/* Video Player */}
            {playback?.url ? (
              <video
                src={playback.url}
                controls
                preload="metadata"
                playsInline
                controlsList="nodownload"
                className="w-full rounded-lg"
              />
            ) : (
              <div className="flex h-64 items-center justify-center rounded-lg bg-muted">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            )}

            {/* Download link */}
            <a
              href={`${env.API_BASE_URL}/api/v1/videos/${job.job_id}/download`}
              className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              MP4 파일 다운로드
            </a>
          </div>
        ) : job.phase === "failed" ? (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>생성 실패</AlertTitle>
            <AlertDescription>
              {job.current_step_detail || "알 수 없는 오류가 발생했습니다."}
            </AlertDescription>
          </Alert>
        ) : (
          <p className="py-8 text-center text-muted-foreground">
            영상이 아직 생성되지 않았습니다.
          </p>
        )}
      </TabsContent>
    </Tabs>
  );
}
