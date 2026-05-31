import { useEffect, useState } from 'react'
import axios from 'axios'

interface DashboardProps {
  apiKey: string
}

interface Stats {
  total_users: number
  new_users_today: number
  active_subscriptions: number
  total_revenue: number
  revenue_today: number
  total_plans: number
  total_servers: number
  online_servers: number
}

export default function Dashboard({ apiKey }: DashboardProps) {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/admin/dashboard', {
      headers: { 'X-API-Key': apiKey }
    })
      .then(res => setStats(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }, [apiKey])

  if (loading) {
    return <div className="text-center py-20 text-gray-500">در حال بارگذاری...</div>
  }

  if (!stats) {
    return <div className="text-center py-20 text-red-500">خطا در دریافت اطلاعات</div>
  }

  const cards = [
    { label: 'کل کاربران', value: stats.total_users.toLocaleString(), icon: '👥', color: 'bg-blue-50 text-blue-700' },
    { label: 'کاربران جدید امروز', value: stats.new_users_today.toLocaleString(), icon: '🆕', color: 'bg-green-50 text-green-700' },
    { label: 'اشتراک فعال', value: stats.active_subscriptions.toLocaleString(), icon: '✅', color: 'bg-purple-50 text-purple-700' },
    { label: 'درآمد کل', value: `${stats.total_revenue.toLocaleString()} تومان`, icon: '💰', color: 'bg-yellow-50 text-yellow-700' },
    { label: 'درآمد امروز', value: `${stats.revenue_today.toLocaleString()} تومان`, icon: '📈', color: 'bg-emerald-50 text-emerald-700' },
    { label: 'سرورها', value: `${stats.online_servers}/${stats.total_servers} آنلاین`, icon: '🖥️', color: 'bg-indigo-50 text-indigo-700' },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">داشبورد</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map((card, i) => (
          <div key={i} className={`rounded-xl p-6 ${card.color}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm opacity-75">{card.label}</p>
                <p className="text-2xl font-bold mt-1">{card.value}</p>
              </div>
              <span className="text-3xl">{card.icon}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
