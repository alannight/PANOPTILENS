"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Eye,
  LayoutDashboard,
  Image,
  FileText,
  Fingerprint,
  Lightbulb,
  Search,
  Network,
  Clock,
  Shield,
  FileBarChart,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Images", href: "/images", icon: Image },
  { name: "Metadata", href: "/metadata", icon: FileText },
  { name: "Forensics", href: "/forensics", icon: Fingerprint },
  { name: "Clues", href: "/clues", icon: Lightbulb },
  { name: "Recon", href: "/recon", icon: Search },
  { name: "Graph", href: "/graph", icon: Network },
  { name: "Timeline", href: "/timeline", icon: Clock },
  { name: "Evidence", href: "/evidence", icon: Shield },
  { name: "Reports", href: "/reports", icon: FileBarChart },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col border-r border-border bg-card">
      {/* Logo & Brand */}
      <div className="flex h-16 items-center gap-3 border-b border-border px-6">
        <div className="relative flex h-9 w-9 items-center justify-center">
          {/* Panoptes Eye Symbol */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-8 w-8 rounded-full border-2 border-accent" />
            <div className="absolute h-3 w-3 rounded-full bg-accent" />
          </div>
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-bold tracking-wider text-foreground">
            PANOPTILENS
          </span>
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
            See Beyond
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-secondary text-foreground"
                  : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-4">
        <div className="rounded-md bg-secondary p-3">
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <Eye className="h-3 w-3" />
            INVESTIGATION
          </div>
          <div className="text-sm font-medium text-foreground">Image workspace</div>
          <p className="mt-1 text-xs text-muted-foreground">Investigation case workspace</p>
        </div>
      </div>
    </div>
  );
}
