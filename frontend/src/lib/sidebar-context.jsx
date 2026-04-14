"use client";

import { createContext, useContext, useState, useCallback } from "react";

const SidebarContext = createContext(undefined);

export function SidebarProvider({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const toggle = useCallback(() => setCollapsed((c) => !c), []);

  return (
    <SidebarContext.Provider value={{ collapsed, toggle }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const ctx = useContext(SidebarContext);
  if (!ctx) throw new Error("useSidebar must be used within SidebarProvider");
  return ctx;
}
