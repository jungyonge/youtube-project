import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow } from "date-fns";
import { ko } from "date-fns/locale";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** 초 → "5분 30초" 형태 */
export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  if (mins === 0) return `${secs}초`;
  if (secs === 0) return `${mins}분`;
  return `${mins}분 ${secs}초`;
}

/** USD 비용 포맷 → "$1.23" */
export function formatCost(usd: number): string {
  return `$${usd.toFixed(2)}`;
}

/** ISO 날짜 → "2026-03-31 14:30" 또는 상대 시간 */
export function formatDate(
  dateStr: string,
  mode: "absolute" | "relative" = "absolute",
): string {
  const date = new Date(dateStr);
  if (mode === "relative") {
    return formatDistanceToNow(date, { addSuffix: true, locale: ko });
  }
  return format(date, "yyyy-MM-dd HH:mm");
}
