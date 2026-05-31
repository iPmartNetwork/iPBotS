import { useEffect, useState } from 'react'
import axios from 'axios'

interface UsersProps {
  apiKey: string
}

interface User {
  id: number
  telegram_id: number
  username: string | null
  full_name: string
  total_purchases: number
  total_spent: number
  is_banned: boolean
  is_active: boolean
  created_at: string | null
}

export default function Users({ apiKey }: UsersProps) {
  const [users, setUsers] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  const fetchUsers = () => {
    setLoading(true)
    const params: Record<string, string | number> = { page, per_page: 20 }
    if (search) params.search = search

    axios.get('/api/admin/users', {
      headers: { 'X-API-Key': apiKey },
      params,
    })
      .then(res => {
        setUsers(res.data.users)
        setTotal(res.data.total)
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchUsers() }, [page, apiKey])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    fetchUsers()
  }

  const toggleBan = async (userId: number) => {
    await axios.post(`/api/admin/users/${userId}/ban`, null, {
      headers: { 'X-API-Key': apiKey },
    })
    fetchUsers()
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">مدیریت کاربران</h2>

      {/* Search */}
      <form onSubmit={handleSearch} className="mb-6 flex gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="جستجو (نام، یوزرنیم، آیدی تلگرام)..."
          className="flex-1 px-4 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-primary-500"
          dir="ltr"
        />
        <button type="submit" className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
          جستجو
        </button>
      </form>

      {/* Table */}
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-right">نام</th>
              <th className="px-4 py-3 text-right">یوزرنیم</th>
              <th className="px-4 py-3 text-right">آیدی تلگرام</th>
              <th className="px-4 py-3 text-right">خریدها</th>
              <th className="px-4 py-3 text-right">مبلغ کل</th>
              <th className="px-4 py-3 text-right">وضعیت</th>
              <th className="px-4 py-3 text-right">عملیات</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-500">در حال بارگذاری...</td></tr>
            ) : users.map(user => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">{user.full_name}</td>
                <td className="px-4 py-3 text-left font-mono text-xs">{user.username || '—'}</td>
                <td className="px-4 py-3 text-left font-mono text-xs">{user.telegram_id}</td>
                <td className="px-4 py-3">{user.total_purchases}</td>
                <td className="px-4 py-3">{user.total_spent.toLocaleString()}</td>
                <td className="px-4 py-3">
                  {user.is_banned ? (
                    <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">بن شده</span>
                  ) : (
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">فعال</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => toggleBan(user.id)}
                    className={`px-3 py-1 rounded text-xs ${
                      user.is_banned
                        ? 'bg-green-100 text-green-700 hover:bg-green-200'
                        : 'bg-red-100 text-red-700 hover:bg-red-200'
                    }`}
                  >
                    {user.is_banned ? 'آنبن' : 'بن'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center mt-4">
        <span className="text-sm text-gray-500">
          مجموع: {total.toLocaleString()} کاربر
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 border rounded-lg disabled:opacity-50"
          >
            قبلی
          </button>
          <span className="px-4 py-2">صفحه {page}</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={users.length < 20}
            className="px-4 py-2 border rounded-lg disabled:opacity-50"
          >
            بعدی
          </button>
        </div>
      </div>
    </div>
  )
}
