import { useEffect, useState } from 'react'
import axios from 'axios'

interface PaymentsProps {
  apiKey: string
}

interface Payment {
  id: number
  user_id: number
  amount: number
  method: string
  status: string
  created_at: string | null
}

export default function Payments({ apiKey }: PaymentsProps) {
  const [payments, setPayments] = useState<Payment[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    axios.get('/api/admin/payments', {
      headers: { 'X-API-Key': apiKey },
      params: { page, per_page: 20 },
    })
      .then(res => {
        setPayments(res.data.payments)
        setTotal(res.data.total)
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }, [page, apiKey])

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        پرداخت‌ها
      </h2>
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-right">#</th>
              <th className="px-4 py-3 text-right">کاربر</th>
              <th className="px-4 py-3 text-right">مبلغ</th>
              <th className="px-4 py-3 text-right">روش</th>
              <th className="px-4 py-3 text-right">وضعیت</th>
              <th className="px-4 py-3 text-right">تاریخ</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-gray-500">
                  در حال بارگذاری...
                </td>
              </tr>
            ) : payments.map(p => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">{p.id}</td>
                <td className="px-4 py-3">{p.user_id}</td>
                <td className="px-4 py-3">
                  {p.amount.toLocaleString()} تومان
                </td>
                <td className="px-4 py-3">{p.method}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs ${
                    p.status === 'completed'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {p.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs">
                  {p.created_at || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex justify-between items-center mt-4">
        <span className="text-sm text-gray-500">
          مجموع: {total.toLocaleString()} پرداخت
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
            disabled={payments.length < 20}
            className="px-4 py-2 border rounded-lg disabled:opacity-50"
          >
            بعدی
          </button>
        </div>
      </div>
    </div>
  )
}
