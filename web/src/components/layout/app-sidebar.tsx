"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Activity,
  Calendar,
  ChevronRight,
  Music,
  Settings,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";
import type { LucideIcon } from "lucide-react";

interface NavChild {
  title: string;
  href: string;
  exact?: boolean;
}

interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  children?: NavChild[];
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    label: "Overview",
    items: [{ title: "Dashboard", href: "/", icon: LayoutDashboard }],
  },
  {
    label: "Data",
    items: [
      { title: "Health", href: "/dash/health", icon: Activity },
      { title: "Music", href: "/dash/music", icon: Music },
      { title: "Calendar", href: "/dash/calendar", icon: Calendar },
    ],
  },
  {
    label: "System",
    items: [
      { title: "Settings", href: "/dash/settings", icon: Settings },
    ],
  },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <Sidebar>
      <SidebarHeader className="border-b px-4 py-3">
        <Link href="/" className="text-lg font-semibold">
          Personal Hub
        </Link>
      </SidebarHeader>
      <SidebarContent>
        {navGroups.map((group) => (
          <SidebarGroup key={group.label}>
            <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) =>
                  item.children ? (
                    <CollapsibleNavItem
                      key={item.href}
                      item={item}
                      pathname={pathname}
                    />
                  ) : (
                    <SidebarMenuItem key={item.href}>
                      <SidebarMenuButton
                        asChild
                        isActive={
                          pathname === item.href ||
                          pathname.startsWith(item.href + "/")
                        }
                      >
                        <Link href={item.href}>
                          <item.icon />
                          <span>{item.title}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  )
                )}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
    </Sidebar>
  );
}

function CollapsibleNavItem({
  item,
  pathname,
}: {
  item: NavItem;
  pathname: string;
}) {
  const isChildActive = item.children?.some((child) =>
    child.exact
      ? pathname === child.href
      : pathname === child.href || pathname.startsWith(child.href + "/"),
  );
  const [open, setOpen] = useState(isChildActive ?? false);

  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        onClick={() => setOpen((prev) => !prev)}
        isActive={isChildActive}
      >
        <item.icon />
        <span>{item.title}</span>
        <ChevronRight
          className={`ml-auto size-4 transition-transform ${open ? "rotate-90" : ""}`}
        />
      </SidebarMenuButton>
      {open && (
        <SidebarMenuSub>
          {item.children!.map((child) => (
            <SidebarMenuSubItem key={child.href}>
              <SidebarMenuSubButton
                asChild
                isActive={
                  child.exact
                    ? pathname === child.href
                    : pathname === child.href ||
                      pathname.startsWith(child.href + "/")
                }
              >
                <Link href={child.href}>{child.title}</Link>
              </SidebarMenuSubButton>
            </SidebarMenuSubItem>
          ))}
        </SidebarMenuSub>
      )}
    </SidebarMenuItem>
  );
}
