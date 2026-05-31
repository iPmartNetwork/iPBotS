import { useEffect, useState } from 'react'
import axios from 'axios'

interface PlansProps {
  apiKey: string
}

interface Plan {
  id: number
  name: string
  price: number
  data_limit_gb: number
  duration_days: number
  is_active: boolean
  sort_order: number
}

export default function Plans({ apiKey }: PlansProps) {
  const [plans, setPlans] = useState<Plan[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/admin/plans', {
      headers: { 'X-API-Key': apiKey },
    })
      .then(res => setPlans(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }, [apiKey])

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        مدیریت پلن‌ها
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <p className="text-gray-500 col-span-3 text-center py-8">
            در حال بارگذاری...
          </p>
        ) : plans.map(plan => (
          <div key={plan.id} className={`bg-white rounded-xl p-6 shadow
            border-r-4 ${plan.is_active
              ? 'border-green-500' : 'border-gray-300'}`}>
            <div className="flex justify-between items-start">
              <h3 className="font-bold text-lg">{plan.name}</h3>
              <span className={`px-2 py-1 rounded text-xs ${
                plan.is_active
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-500'
              }`}>
                {plan.is_active ? 'فعال' : 'غیرفعال'}
              </span>
            </div>
            <div className="mt-4 space-y-2 text-sm text-gray-600">
              <p>💰 قیمت: <span className="font-bold text-gray-800">
                {plan.price.toLocaleString()} تومان
              </span></p>
              <p>📊 حجم: {plan.data_limit_gb} GB</p>
              <p>⏱️ مدت: {plan.duration_days} روز</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
