import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ClaimBadge } from "./claim-badge";
import type { ScriptScene } from "@/types/api";
import { formatDuration } from "@/lib/utils";

interface ScriptSceneCardProps {
  scene: ScriptScene;
}

export function ScriptSceneCard({ scene }: ScriptSceneCardProps) {
  return (
    <Card>
      <CardContent className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <span className="font-semibold">
            씬 {scene.scene_id}: {scene.section}
          </span>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {scene.asset_plan.length > 0 && (
              <Badge variant="outline" className="text-xs">
                {scene.asset_plan[0]?.asset_type}
              </Badge>
            )}
            <span>{formatDuration(scene.duration_target_sec)}</span>
          </div>
        </div>

        {/* Purpose */}
        <p className="text-xs text-muted-foreground">{scene.purpose}</p>

        {/* Narration */}
        <div className="rounded-md bg-muted p-3">
          <p className="text-sm leading-relaxed">{scene.narration}</p>
        </div>

        {/* Claims */}
        {scene.claims.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {scene.claims.map((claim, i) => (
              <ClaimBadge key={i} claim={claim} />
            ))}
          </div>
        )}

        {/* Policy flags */}
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

        {/* Keywords */}
        {scene.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {scene.keywords.map((kw) => (
              <Badge key={kw} variant="secondary" className="text-xs">
                {kw}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
