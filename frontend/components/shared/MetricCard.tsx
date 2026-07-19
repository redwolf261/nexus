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
    <div className="bg-card border border-border rounded-lg p-6 flex flex-col gap-4">
      <div className="flex items-center justify-between text-muted-foreground">
        <span className="text-sm font-medium uppercase tracking-wider">{title}</span>
        <Icon className="w-5 h-5 text-primary" />
      </div>
      <div className="flex items-end justify-between">
        <span className="text-4xl font-bold text-foreground font-mono">{value}</span>
        {trend && (
          <span className={`text-sm font-medium ${trendUp ? 'text-chart-5' : 'text-destructive'}`}>
            {trend}
          </span>
        )}
      </div>
    </div>
  );
}
