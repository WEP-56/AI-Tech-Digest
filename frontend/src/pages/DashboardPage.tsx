import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import client from '../api/client'
import { useToast } from '../components/Toast'
import Loading from '../components/Loading'

interface DashboardSummary {
  today_fetched?: number
  today_processed?: number
  today_sent?: number
  total_recipients?: number
  active_sources?: number
  last_job_status?: string
  last_job_date?: string
  digest_sent_today?: boolean
  [key: string]: unknown
}

interface StatCard {
  label: string
  value: string | number
  icon: string
  gradient: string
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const { showToast } = useToast()

  const fetchSummary = useCallback(async () => {
    setLoading(true)
    try {
      const res = await client.get('/dashboard/summary')
      setSummary(res.data)
    } catch (err) {
      showToast(err instanceof Error ? err.message : '获取数据失败', 'error')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    fetchSummary()
  }, [fetchSummary])

  const handleAction = async (action: string, endpoint: string, successMsg: string) => {
    setActionLoading(action)
    try {
      await client.post(endpoint)
      showToast(successMsg, 'success')
      fetchSummary()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '操作失败', 'error')
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) {
    return <Loading size="lg" text="正在加载仪表盘..." />
  }

  const statCards: StatCard[] = [
    {
      label: '今日采集数',
      value: summary?.today_fetched ?? 0,
      icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
      gradient: 'from-blue-500 to-cyan-500',
    },
    {
      label: '今日处理数',
      value: summary?.today_processed ?? 0,
      icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
      gradient: 'from-green-500 to-emerald-500',
    },
    {
      label: '今日发送数',
      value: summary?.today_sent ?? 0,
      icon: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
      gradient: 'from-purple-500 to-pink-500',
    },
    {
      label: '活跃收件人',
      value: summary?.total_recipients ?? 0,
      icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.127-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.127-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z',
      gradient: 'from-orange-500 to-red-500',
    },
  ]

  const quickActions = [
    {
      label: '立即采集',
      desc: '抓取最新资讯',
      action: 'fetch',
      endpoint: '/jobs/fetch-now',
      successMsg: '采集任务已触发',
      icon: 'M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
      gradient: 'from-blue-500 to-indigo-600',
    },
    {
      label: '生成日报',
      desc: 'AI生成今日日报',
      action: 'generate',
      endpoint: '/jobs/generate-digest',
      successMsg: '日报生成任务已触发',
      icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      gradient: 'from-purple-500 to-pink-600',
    },
    {
      label: '发送日报',
      desc: '发送日报邮件',
      action: 'send',
      endpoint: '/jobs/send-now',
      successMsg: '日报发送任务已触发',
      icon: 'M12 19l9 2-9-18-9 18 9-2zm0 0v-8',
      gradient: 'from-green-500 to-teal-600',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-brand-gradient rounded-2xl p-6 lg:p-8 text-white shadow-brand">
        <h2 className="text-2xl font-bold mb-2">欢迎使用 AI Tech Digest Mailer</h2>
        <p className="text-purple-100">
          智能科技资讯采集、AI摘要生成与邮件推送管理平台
        </p>
        {summary?.last_job_date && (
          <div className="mt-4 inline-flex items-center gap-2 bg-white bg-opacity-20 px-4 py-2 rounded-lg text-sm">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            上次任务：{summary.last_job_date}
            {summary.last_job_status && (
              <span className="badge bg-white bg-opacity-25 text-white ml-2">
                {summary.last_job_status}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <div key={card.label} className="card p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-500 mb-1">{card.label}</p>
                <p className="text-3xl font-bold text-gray-800">{card.value}</p>
              </div>
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${card.gradient} flex items-center justify-center flex-shrink-0`}>
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={card.icon} />
                </svg>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">快捷操作</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {quickActions.map((qa) => (
            <button
              key={qa.action}
              onClick={() => handleAction(qa.action, qa.endpoint, qa.successMsg)}
              disabled={actionLoading === qa.action}
              className="group relative overflow-hidden rounded-xl border border-gray-200 p-5 text-left hover:border-transparent hover:shadow-lg transition disabled:opacity-50"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${qa.gradient} opacity-0 group-hover:opacity-100 transition`} />
              <div className="relative">
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${qa.gradient} flex items-center justify-center mb-3 group-hover:bg-white group-hover:bg-opacity-20`}>
                  {actionLoading === qa.action ? (
                    <svg className="w-5 h-5 text-white animate-spin group-hover:text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={qa.icon} />
                    </svg>
                  )}
                </div>
                <p className="font-semibold text-gray-800 group-hover:text-white transition">{qa.label}</p>
                <p className="text-sm text-gray-500 group-hover:text-purple-100 transition mt-1">{qa.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Navigation Shortcuts */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">系统导航</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {[
            { label: '邮箱配置', path: '/mail-account' },
            { label: '收件人管理', path: '/recipients' },
            { label: '模型配置', path: '/models' },
            { label: '信源配置', path: '/sources' },
            { label: '邮件模板', path: '/email-template' },
            { label: '任务调度', path: '/schedule' },
            { label: '任务日志', path: '/jobs' },
            { label: '存储管理', path: '/storage' },
          ].map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className="flex items-center justify-between px-4 py-3 rounded-lg bg-gray-50 hover:bg-purple-50 hover:text-purple-600 text-gray-600 text-sm font-medium transition"
            >
              {item.label}
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
