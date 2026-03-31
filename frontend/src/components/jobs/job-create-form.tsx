import { useState } from "react";
import { useForm, FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  ChevronDown,
  ChevronUp,
  BookOpen,
  Clapperboard,
  GraduationCap,
  MessageSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { SourceInputList } from "./source-input-list";
import { useCreateJob } from "@/hooks/use-jobs";
import { cn } from "@/lib/utils";

const sourceSchema = z.object({
  source_type: z.enum(["blog", "news", "youtube", "custom_text"]),
  url: z.string().optional(),
  custom_text: z.string().optional(),
});

const formSchema = z.object({
  topic: z.string().min(5, "주제는 5자 이상이어야 합니다").max(200, "주제는 200자 이하여야 합니다"),
  sources: z.array(sourceSchema).min(1, "소스를 1개 이상 추가하세요").max(10),
  style: z.enum(["informative", "storytelling", "tutorial", "opinion"]),
  target_duration_minutes: z.number().min(10).max(15),
  language: z.string(),
  tts_voice: z.string(),
  include_subtitles: z.boolean(),
  include_bgm: z.boolean(),
  cost_budget_usd: z.number().min(0.5).max(10),
  auto_approve: z.boolean(),
  additional_instructions: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

const STYLES = [
  { value: "informative" as const, icon: BookOpen, label: "정보 전달", desc: "객관적 사실 중심" },
  { value: "storytelling" as const, icon: Clapperboard, label: "스토리텔링", desc: "이야기 구조" },
  { value: "tutorial" as const, icon: GraduationCap, label: "튜토리얼", desc: "단계별 설명" },
  { value: "opinion" as const, icon: MessageSquare, label: "오피니언", desc: "관점 제시" },
];

const VOICES = [
  { value: "alloy", label: "Alloy (중성)" },
  { value: "echo", label: "Echo (남성)" },
  { value: "fable", label: "Fable (남성)" },
  { value: "onyx", label: "Onyx (남성, 저음)" },
  { value: "nova", label: "Nova (여성)" },
  { value: "shimmer", label: "Shimmer (여성)" },
];

const LANGUAGES = [
  { value: "ko", label: "한국어" },
  { value: "en", label: "English" },
  { value: "ja", label: "日本語" },
];

export function JobCreateForm() {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const createJob = useCreateJob();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      topic: "",
      sources: [{ source_type: "blog", url: "", custom_text: "" }],
      style: "informative",
      target_duration_minutes: 10,
      language: "ko",
      tts_voice: "alloy",
      include_subtitles: true,
      include_bgm: true,
      cost_budget_usd: 2,
      auto_approve: true,
      additional_instructions: "",
    },
  });

  const onSubmit = (values: FormValues) => {
    createJob.mutate({
      ...values,
      idempotency_key: crypto.randomUUID(),
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>영상 생성</CardTitle>
      </CardHeader>
      <CardContent>
        <FormProvider {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Topic */}
            <FormField
              control={form.control}
              name="topic"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>주제</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="영상으로 만들 주제를 입력하세요 (5~200자)"
                      rows={3}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Sources */}
            <div className="space-y-2">
              <Label>소스</Label>
              <SourceInputList />
            </div>

            {/* Style */}
            <FormField
              control={form.control}
              name="style"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>스타일</FormLabel>
                  <div className="grid grid-cols-2 gap-2">
                    {STYLES.map((s) => (
                      <button
                        key={s.value}
                        type="button"
                        onClick={() => field.onChange(s.value)}
                        className={cn(
                          "flex items-center gap-2 rounded-md border p-3 text-left text-sm transition-colors hover:bg-accent",
                          field.value === s.value
                            ? "border-primary bg-primary/5"
                            : "border-border",
                        )}
                      >
                        <s.icon className="h-4 w-4 shrink-0" />
                        <div>
                          <div className="font-medium">{s.label}</div>
                          <div className="text-xs text-muted-foreground">
                            {s.desc}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </FormItem>
              )}
            />

            {/* Advanced Settings Toggle */}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="w-full justify-between"
            >
              고급 설정
              {showAdvanced ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>

            {showAdvanced && (
              <div className="space-y-4 rounded-md border p-4">
                {/* Duration */}
                <FormField
                  control={form.control}
                  name="target_duration_minutes"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>영상 길이: {field.value}분</FormLabel>
                      <FormControl>
                        <Slider
                          min={10}
                          max={15}
                          step={1}
                          value={[field.value]}
                          onValueChange={([v]) => field.onChange(v)}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                {/* Voice */}
                <FormField
                  control={form.control}
                  name="tts_voice"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>음성</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {VOICES.map((v) => (
                            <SelectItem key={v.value} value={v.value}>
                              {v.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormItem>
                  )}
                />

                {/* Language */}
                <FormField
                  control={form.control}
                  name="language"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>언어</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {LANGUAGES.map((l) => (
                            <SelectItem key={l.value} value={l.value}>
                              {l.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormItem>
                  )}
                />

                {/* Subtitles */}
                <FormField
                  control={form.control}
                  name="include_subtitles"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between">
                      <FormLabel>자막 포함</FormLabel>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                {/* BGM */}
                <FormField
                  control={form.control}
                  name="include_bgm"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between">
                      <FormLabel>배경 음악</FormLabel>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                {/* Budget */}
                <FormField
                  control={form.control}
                  name="cost_budget_usd"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>비용 예산 ($)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={0.5}
                          max={10}
                          step={0.5}
                          {...field}
                          onChange={(e) =>
                            field.onChange(parseFloat(e.target.value))
                          }
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Auto Approve */}
                <FormField
                  control={form.control}
                  name="auto_approve"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex items-center justify-between">
                        <FormLabel>자동 승인</FormLabel>
                        <FormControl>
                          <Switch
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                      </div>
                      {!field.value && (
                        <p className="text-xs text-muted-foreground">
                          대본 생성 후 직접 검토하고 승인해야 영상 생성이
                          진행됩니다.
                        </p>
                      )}
                    </FormItem>
                  )}
                />

                {/* Additional Instructions */}
                <FormField
                  control={form.control}
                  name="additional_instructions"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>추가 지시사항</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="특별한 요구사항이 있다면 입력하세요..."
                          rows={2}
                          {...field}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </div>
            )}

            {/* Submit */}
            <Button
              type="submit"
              className="w-full"
              disabled={createJob.isPending}
            >
              {createJob.isPending ? "생성 중..." : "영상 생성 시작"}
            </Button>
          </form>
        </FormProvider>
      </CardContent>
    </Card>
  );
}
