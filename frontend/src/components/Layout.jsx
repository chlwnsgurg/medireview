import { NavLink, Outlet } from 'react-router-dom';
import AlertBadge from './AlertBadge';

const navItems = [
  { to: '/', label: '대시보드', icon: '📊' },
  { to: '/alerts', label: '알림', icon: '🔔', showBadge: true },
  { to: '/automation', label: '자동화', icon: '🤖' },
  { to: '/settings', label: '설정', icon: '⚙️' },
];

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-60 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <span className="text-xl font-bold text-blue-600">🏥 MediReview</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-6 py-3 text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 font-medium border-r-2 border-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
              {item.showBadge && <AlertBadge />}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 text-xs text-gray-400">
          © 2026 MediReview
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8">
          <h1 className="text-lg font-semibold text-gray-800">병·의원 통합 리뷰 관리</h1>
          <div className="flex items-center gap-4">
            <AlertBadge />
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-8 flex flex-col">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
