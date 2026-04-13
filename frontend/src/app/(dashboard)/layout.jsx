"use client";

import Sidebar from "@/components/layout/Sidebar";
import { SidebarProvider, useSidebar } from "@/lib/sidebar-context";

function DashboardInner({ children }) {
  const { collapsed } = useSidebar();

  return (
    <div className="flex min-h-[100dvh]">
      <Sidebar />
      <main
        id="dashboard-content"
        className={`
          flex-1 overflow-y-auto transition-all duration-300 ease-in-out
          ${collapsed ? "ml-[var(--width-sidebar-collapsed)]" : "ml-[var(--width-sidebar)]"}
        `}
      >
        <div className="p-8 flex flex-col flex-1">
          {children}
        </div>
      </main>
    </div>
  );
}

export default function DashboardLayout({ children }) {
  return (
    <SidebarProvider>
      <DashboardInner>{children}</DashboardInner>
    </SidebarProvider>
  );
}
