import { useEffect, useState } from 'react'
import axios from 'axios'

interface ServersProps {
  apiKey: string
}

interface Server {
  id: number
  name: string
  host: string
  is_active: boolean
  panel_type: string
  max_users: number
  current_users: number
}

export default function Servers({ apiKey }: ServersProps) {
  const [servers, setServers] = useState<Server[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/admin/servers', {
      headers: { 'X-API-Key': apiKey },
    })
      .then(res => setServers(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }, [apiKey])

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        وضعیت سرورها
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading ? (
          <p className="text-gray-500 col-span-2 text-center py-8">
            در حال بارگذاری...
          </p>
        ) : servers.map(server => (
          <div key={server.id} className="bg-white rounded-xl p-6 shadow">
            <div className="flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full ${
                server.is_active ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <h3 className="font-bold text-lg">{server.name}</h3>
            </div>
            <div className="mt-4 space-y-2 text-sm text-gray-600">
              <p>🌐 آدرس: <code className="bg-gray-100 px-2 py-0.5 rounded">
                {server.host}
              </code></p>
              <p>📡 پنل: {server.panel_type}</p>
              <p>👥 کاربران: {server.current_users}/{server.max_users}</p>
              <p>وضعیت: {server.is_active ? '🟢 آنلاین' : '🔴 آفلاین'}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
