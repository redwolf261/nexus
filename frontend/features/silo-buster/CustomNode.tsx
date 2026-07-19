import { Handle, Position } from "@xyflow/react";
import { FileText, Smartphone, Car, User } from "lucide-react";

const iconMap = {
  FIR: FileText,
  Phone: Smartphone,
  Vehicle: Car,
  Person: User,
};

export function EntityNode({ data }: any) {
  const Icon = iconMap[data.type as keyof typeof iconMap] || User;
  
  return (
    <div className={`bg-card border-2 rounded-md px-4 py-3 shadow-lg min-w-[150px] flex items-center gap-3 transition-all duration-300 ${data.isHighlighted ? 'border-[#00e5ff] shadow-[0_0_20px_rgba(0,229,255,0.4)] scale-110 z-50' : 'border-border'}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3 bg-primary" />
      
      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
        data.type === 'FIR' ? 'bg-chart-3/20 text-chart-3' :
        data.type === 'Person' ? 'bg-chart-1/20 text-chart-1' :
        data.type === 'Vehicle' ? 'bg-chart-2/20 text-chart-2' :
        'bg-chart-4/20 text-chart-4'
      }`}>
        <Icon className="w-4 h-4" />
      </div>
      
      <div className="flex flex-col">
        <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">{data.type}</span>
        <span className="text-sm font-medium text-foreground font-mono">{data.id}</span>
      </div>

      <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-primary" />
    </div>
  );
}
