import { Link, useLocation } from "react-router";
import { useSidebar } from "@medireview/lib/sidebar-context";
import { useAppPath, useAppRoot } from "@medireview/lib/app-root.jsx";

/* ─── 네비게이션 아이콘 ─── */
function NavIcon({ icon, size = 18 }) {
  const props = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.5,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": true,
  };

  switch (icon) {
    case "chart":
      return (
        <svg {...props}>
          <line x1="18" y1="20" x2="18" y2="10" />
          <line x1="12" y1="20" x2="12" y2="4" />
          <line x1="6" y1="20" x2="6" y2="14" />
        </svg>
      );
    case "bell":
      return (
        <svg {...props}>
          <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 01-3.46 0" />
        </svg>
      );
    case "gear":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
        </svg>
      );
    default:
      return null;
  }
}

/* ─── 사이드바 네비게이션 구성 ─── */
const NAV_GROUPS = [
  {
    label: "OVERVIEW",
    items: [
      { id: "dashboard", path: "", label: "대시보드", icon: "chart" },
    ],
  },
  {
    label: "MANAGEMENT",
    items: [
      { id: "alerts", path: "alerts", label: "알림", icon: "bell" },
      { id: "settings", path: "settings", label: "설정", icon: "gear" },
    ],
  },
];

/* ─── 메인 사이드바 컴포넌트 ─── */
export default function Sidebar({ collapsed: collapsedProp, onToggle, style }) {
  const location = useLocation();
  const ctx = useSidebar();
  const appPath = useAppPath();
  const appRoot = useAppRoot();
  const collapsed = collapsedProp ?? ctx?.collapsed ?? false;
  const toggle = onToggle ?? ctx?.toggle;

  const pathname = location.pathname;
  const rootHref = appPath("");
  const mergedStyle = appRoot ? { left: "var(--width-app-rail)", ...style } : style;

  const isActive = (href) => {
    if (href === rootHref) return pathname === rootHref;
    return pathname === href || pathname.startsWith(href + "/");
  };

  return (
    <aside
      className={`
        fixed inset-y-0 left-0 z-30 flex flex-col
        bg-[var(--color-sidebar-bg)]
        transition-all duration-300 ease-in-out
        ${collapsed ? "w-[var(--width-sidebar-collapsed)]" : "w-[var(--width-sidebar)]"}
      `}
      style={mergedStyle}
    >
      {/* 앱 로고 */}
      <div className="flex h-14 items-center px-4 border-b border-[var(--color-sidebar-border)]">
        <Link to={rootHref} className="flex items-center gap-2.5 group">
          <span className="text-lg">🏥</span>
          {!collapsed && (
            <span className="font-semibold text-[var(--color-sidebar-text-active)] tracking-tight text-[15px] group-hover:text-[var(--color-accent)] transition-colors">
              MediReview
            </span>
          )}
        </Link>
      </div>

      {/* 네비게이션 */}
      <nav className="flex-1 overflow-y-auto py-3" aria-label="MediReview navigation">
        {NAV_GROUPS.map((group, groupIdx) => (
          <div key={group.label}>
            {groupIdx > 0 && (
              <hr className="my-2 mx-3 border-[var(--color-sidebar-border)]" />
            )}

            {!collapsed && (
              <p className="px-4 py-1.5 text-[10px] font-semibold tracking-widest text-[var(--color-sidebar-category)] uppercase">
                {group.label}
              </p>
            )}

            <ul className="space-y-0.5 px-2">
              {group.items.map((item) => {
                const href = appPath(item.path);
                const active = isActive(href);
                return (
                  <li key={item.id}>
                    <Link
                      to={href}
                      aria-current={active ? "page" : undefined}
                      className={`
                        flex items-center gap-3 rounded-lg px-3 py-2 text-sm
                        transition-all duration-200
                        ${collapsed ? "justify-center" : ""}
                        ${
                          active
                            ? "border-l-[3px] border-[var(--color-accent)] bg-[var(--color-sidebar-active)] font-medium text-[var(--color-sidebar-text-active)]"
                            : "border-l-[3px] border-transparent text-[var(--color-sidebar-text)] hover:bg-[var(--color-sidebar-hover)] hover:text-[var(--color-sidebar-text-active)]"
                        }
                      `}
                      title={collapsed ? item.label : undefined}
                    >
                      <NavIcon icon={item.icon} />
                      {!collapsed && <span>{item.label}</span>}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* 하단: 접기 토글 */}
      <div className="border-t border-[var(--color-sidebar-border)] p-3">
        <button
          type="button"
          onClick={toggle}
          className="flex w-full items-center justify-center rounded-lg py-1.5 text-sm
                     text-[var(--color-sidebar-text)] transition-colors duration-200
                     hover:bg-[var(--color-sidebar-hover)] hover:text-[var(--color-sidebar-text-active)]"
          aria-label={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
        >
          <svg
            aria-hidden="true"
            width="16" height="16" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="1.5"
            strokeLinecap="round" strokeLinejoin="round"
            className={`transition-transform duration-300 ${collapsed ? "rotate-180" : ""}`}
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      </div>
    </aside>
  );
}
