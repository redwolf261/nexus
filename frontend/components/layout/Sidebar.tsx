"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard, Network, Map, ListTree, Users, Bell,
  CheckCircle, AlertTriangle, Shield, ClipboardList,
  Terminal, LogOut, Wifi
} from "lucide-react";

const NAV_GROUPS = [
  {
    label: "Intelligence",
    links: [
      { name: "Executive", href: "/", icon: LayoutDashboard },
      { name: "Investigations", href: "/investigations", icon: Users },
      { name: "Silo Buster", href: "/silo-buster", icon: Network },
      { name: "Knowledge Graph", href: "/graph", icon: ListTree },
      { name: "Predictive Map", href: "/map", icon: Map },
    ],
  },
  {
    label: "Operations",
    links: [
      { name: "Command Center", href: "/command-center", icon: Terminal },
      { name: "Approvals", href: "/approvals", icon: CheckCircle },
      { name: "Escalations", href: "/escalations", icon: AlertTriangle },
      { name: "Notifications", href: "/notifications", icon: Bell },
    ],
  },
  {
    label: "Governance",
    links: [
      { name: "Audit Ledger", href: "/audit", icon: Shield },
      { name: "Compliance", href: "/compliance", icon: ClipboardList },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  function handleLogout() {
    localStorage.removeItem("nexus_token");
    localStorage.removeItem("dev_token");
    router.push("/login");
  }

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <aside className="w-60 bg-slate-950 border-r border-slate-800/60 h-full flex flex-col shrink-0">
      {/* Logo */}
      <div className="h-14 flex items-center px-5 border-b border-slate-800/60 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-mono text-lg text-emerald-400 tracking-widest font-bold">NEXUS</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <p className="text-[9px] font-bold text-slate-600 uppercase tracking-[0.2em] px-2 mb-2">
              {group.label}
            </p>
            <div className="space-y-0.5">
              {group.links.map((link) => {
                const Icon = link.icon;
                const active = isActive(link.href);
                return (
                  <Link
                    key={link.name}
                    href={link.href}
                    className={`flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm transition-all group ${
                      active
                        ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800/40"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                    }`}
                  >
                    <Icon className={`w-4 h-4 shrink-0 ${active ? "text-emerald-400" : "text-slate-500 group-hover:text-slate-300"}`} />
                    <span className="font-medium text-[13px]">{link.name}</span>
                    {active && <div className="ml-auto w-1 h-1 rounded-full bg-emerald-400" />}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-800/60 p-3 space-y-2 shrink-0">
        <div className="flex items-center justify-between px-2 py-1">
          <div className="flex items-center gap-1.5">
            <Wifi className="w-3 h-3 text-emerald-500" />
            <span className="text-[10px] font-mono text-emerald-500">SYSTEMS NOMINAL</span>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-slate-500 hover:text-rose-400 hover:bg-rose-950/20 transition-all text-[13px]"
        >
          <LogOut className="w-4 h-4" />
          <span className="font-medium">Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
