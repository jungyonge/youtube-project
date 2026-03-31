import { useAuthStore } from "@/stores/auth-store";
import { Badge } from "@/components/ui/badge";

export function Header() {
  const user = useAuthStore((s) => s.user);

  if (!user) return null;

  const remaining = user.daily_quota - user.today_usage;

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-6">
      <div />
      <div className="flex items-center gap-4">
        <Badge variant={remaining > 0 ? "secondary" : "destructive"}>
          오늘 {user.today_usage}/{user.daily_quota}
        </Badge>
        <span className="text-sm text-muted-foreground">{user.email}</span>
      </div>
    </header>
  );
}
