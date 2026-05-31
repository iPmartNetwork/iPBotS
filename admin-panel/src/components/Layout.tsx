import { Link, useLocation } from 'react-router-dom'
import { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
  onLogout: () => void
}

const navItems = [
  { path: '/', label: 'داشبورد', icon: '📊' },
  { path: '/users', label: 'کاربران', icon: '👥' },
  { path: '/plans', label: 'پلن‌ها', icon: '📋' },
  { path: '/servers', label: 'سرورها', icon: '🖥️' },
  { path: '/payments', label: 'پرداخت‌ها', icon: '💰' },
]

export default function Layout({ children, onLogout }: LayoutProps) {
  const location = useLocation()

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white p-4 fixed h-full right-0 top-0">
        <div className="mb-8">
          <h1 className="text-xl font-bold text-center">🤖 iPBotS Admin</h1>
          <p className="text-gray-400 text-sm text-center mt-1">v2.0.0</p>
        </div>

        <nav className="space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                location.pathname === item.path
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <button
          onClick={onLogout}
          className="absolute bottom-4 left-4 right-4 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-center transition-colors"
        >
          🚪 خروج
        </button>
      </aside>

      {/* Main content */}
      <main className="flex-1 mr-64 p-8">
        {children}
      </main>
    </div>
  )
}
