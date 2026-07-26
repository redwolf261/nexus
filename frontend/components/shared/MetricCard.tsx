import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  trendUp?: boolean;
}

export function MetricCard({ title, value, icon: Icon, trend, trendUp }: MetricCardProps) {
  return (
    <div className="glass-card rounded-xl p-5 flex flex-col gap-3 group hover:border-primary/30 transition-all duration-300 relative overflow-hidden">
      {/* Subtle top accent line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent" />

      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.15em]">
          {title}
        </span>
        <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
          <Icon className="w-4 h-4 text-primary" />
        </div>
      </div>

      <div className="flex items-end justify-between gap-2">
        <span className="text-3xl font-bold text-foreground font-mono tracking-tight">
          {value}
        </span>
        {trend && (
          <span
            className={`text-xs font-mono font-bold px-2 py-0.5 rounded-full border ${
              trendUp
                ? "text-chart-1 bg-chart-1/10 border-chart-1/20"
                : "text-destructive bg-destructive/10 border-destructive/20"
            }`}
          >
            {trend}
          </span>
        )}
      </div>
    </div>
  );
}
