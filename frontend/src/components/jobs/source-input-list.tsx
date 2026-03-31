import { useFieldArray, useFormContext } from "react-hook-form";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";

const SOURCE_TYPES = [
  { value: "blog", label: "블로그" },
  { value: "news", label: "뉴스" },
  { value: "youtube", label: "유튜브" },
  { value: "custom_text", label: "직접 입력" },
] as const;

export function SourceInputList() {
  const { control, watch } = useFormContext();
  const { fields, append, remove } = useFieldArray({
    control,
    name: "sources",
  });

  return (
    <div className="space-y-3">
      {fields.map((field, index) => {
        const sourceType = watch(`sources.${index}.source_type`);
        return (
          <div key={field.id} className="flex gap-2">
            <FormField
              control={control}
              name={`sources.${index}.source_type`}
              render={({ field: f }) => (
                <FormItem className="w-28 shrink-0">
                  <Select
                    onValueChange={f.onChange}
                    defaultValue={f.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {SOURCE_TYPES.map((t) => (
                        <SelectItem key={t.value} value={t.value}>
                          {t.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </FormItem>
              )}
            />

            <div className="flex-1">
              {sourceType === "custom_text" ? (
                <FormField
                  control={control}
                  name={`sources.${index}.custom_text`}
                  render={({ field: f }) => (
                    <FormItem>
                      <FormControl>
                        <Textarea
                          placeholder="텍스트를 직접 입력하세요..."
                          rows={2}
                          {...f}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ) : (
                <FormField
                  control={control}
                  name={`sources.${index}.url`}
                  render={({ field: f }) => (
                    <FormItem>
                      <FormControl>
                        <Input placeholder="https://..." {...f} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}
            </div>

            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => remove(index)}
              disabled={fields.length <= 1}
              className="shrink-0"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        );
      })}

      {fields.length < 10 && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() =>
            append({ source_type: "blog", url: "", custom_text: "" })
          }
        >
          <Plus className="mr-1 h-4 w-4" />
          소스 추가
        </Button>
      )}
    </div>
  );
}
