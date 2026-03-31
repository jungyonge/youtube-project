import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScriptSceneCard } from "./script-scene-card";
import { PolicyFlagAlert } from "./policy-flag-alert";
import type { FullScript } from "@/types/api";
import { formatDuration } from "@/lib/utils";

interface ScriptPreviewProps {
  script: FullScript;
}

export function ScriptPreview({ script }: ScriptPreviewProps) {
  return (
    <div className="space-y-4">
      {/* Policy alert */}
      <PolicyFlagAlert
        sensitivity={script.overall_sensitivity}
        warnings={script.policy_warnings}
      />

      {/* Meta */}
      <div className="space-y-1">
        <h2 className="text-xl font-bold">{script.title}</h2>
        <p className="text-sm text-muted-foreground">{script.subtitle}</p>
        <div className="flex flex-wrap gap-2 pt-2">
          <Badge variant="outline">
            {formatDuration(script.total_duration_sec)}
          </Badge>
          <Badge variant="outline">{script.scenes.length}개 씬</Badge>
          {script.tags.map((tag) => (
            <Badge key={tag} variant="secondary">
              {tag}
            </Badge>
          ))}
        </div>
      </div>

      {/* Description */}
      {script.description && (
        <p className="text-sm text-muted-foreground">{script.description}</p>
      )}

      <Separator />

      {/* Scenes */}
      <div className="space-y-3">
        {script.scenes.map((scene) => (
          <ScriptSceneCard key={scene.scene_id} scene={scene} />
        ))}
      </div>
    </div>
  );
}
