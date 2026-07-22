import Link from "next/link";
import { LayoutDashboard, Network, Map, ListTree, Users, Bell } from "lucide-react";

export function Sidebar() {
  const links = [
    { name: "Executive", href: "/", icon: LayoutDashboard },
    { name: "Investigations", href: "/investigations", icon: Users },
    { name: "Silo Buster", href: "/silo-buster", icon: Network },
    { name: "Knowledge Graph", href: "/graph", icon: ListTree },
    { name: "Predictive", href: "/map", icon: Map },
  ];

  return (
    <aside className="w-64 bg-sidebar border-r border-sidebar-border h-full flex flex-col">
      <div className="h-16 flex items-center px-6 border-b border-sidebar-border">
        <span className="font-mono text-xl text-primary tracking-widest font-bold">NEXUS</span>
      </div>
      <nav className="flex-1 px-4 py-6 space-y-2">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <Link 
              key={link.name} 
              href={link.href}
              className="flex items-center gap-3 px-3 py-2 rounded-md text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm font-medium">{link.name}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-sidebar-border">
        <div className="flex items-center gap-3 px-3 py-2 text-muted-foreground">
          <Bell className="w-5 h-5" />
          <span className="text-xs uppercase tracking-wider">Alerts Active</span>
        </div>
      </div>
      
      <div className="p-4 border-t border-border/50 shrink-0 space-y-3">
        <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2 border-b border-border/50 pb-1">System Status</div>
        
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-muted-foreground">GIS Core</span>
          <span className="text-primary flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-primary" /> OK</span>
        </div>
        
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-muted-foreground">Neo4j Graph</span>
          <span className="text-primary flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-primary" /> OK</span>
        </div>
        
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-muted-foreground">Prediction AI</span>
          <span className="text-chart-2 flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-chart-2 animate-pulse" /> 14ms</span>
        </div>
      </div>
    </aside>
  );
}
