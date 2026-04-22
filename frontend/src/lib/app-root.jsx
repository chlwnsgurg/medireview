import { createContext, useContext } from "react";

const AppRootContext = createContext("");

function normalize(basename) {
  if (!basename) return "";
  const trimmed = basename.endsWith("/") ? basename.slice(0, -1) : basename;
  return trimmed.startsWith("/") ? trimmed : "/" + trimmed;
}

export function AppRootProvider({ basename = "", children }) {
  return (
    <AppRootContext.Provider value={normalize(basename)}>
      {children}
    </AppRootContext.Provider>
  );
}

export function useAppRoot() {
  return useContext(AppRootContext);
}

export function useAppPath() {
  const root = useAppRoot();
  return (path = "") => {
    if (path === "" || path === "/") return root || "/";
    const p = path.startsWith("/") ? path : "/" + path;
    return root + p;
  };
}
