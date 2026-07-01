import { useState, useEffect } from 'react'
import client from '../api/client'
import { useToast } from '../components/Toast'
import Loading from '../components/Loading'

interface ScheduleConfig {
  enabled: boolean
  fetch_time: string
  generate_time: string
  send_time: string
  timezone: string
  weekdays_only: boolean
}

const defaultConfig: ScheduleConfig = {
  enabled: false,
  fetch_time: '06:00',
  generate_time: '07:00',
  send_time: '08:00',
  timezone: 'Asia/Shanghai',
  weekdays_only: true,
}

const timezones = [
  'Asia/Shanghai',
  'Asia/Tokyo',
  'Asia/Hong_Kong',
  'Asia/Singapore',
  'UTC',
  'Europe/London',
  'Europe/Berlin',
  'America/New_York',
  'America/Los_Angeles',
  'Australia/Sydney',
]

export default function SchedulePage() {
  const [config, setConfig] = useState<ScheduleConfig>(defaultConfig)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [triggering, setTriggering] = useState<string | null>(null)
  const { showToast } = useToast()

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    setLoading(true)
    try {
      const res = await client.get('/schedule')
      if (res.data && Object.keys(res.data).length > 0) {
        setConfig({ ...defaultConfig, ...res.data })
      }
    } catch (err) {
      if (!(err instanceof Error && err.message.includes('404'))) {
        showToast(err instanceof Error ? err.message : '获取调度配置失败', 'error')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await client.put('/schedule', config)
      showToast('调度配置已保存', 'success')
      fetchConfig()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (field: keyof ScheduleConfig, value: string | boolean) => {
    setConfig((prev) => ({ ...prev, [field]: value }))
  }

  const handleTrigger = async (action: string, endpoint: string, label: string) => {
    setTriggering(action)
    try {
      const res = await client.post(endpoint)
      showToast(res.data?.message || `${label}已触发`, res.data?.success ? 'success' : 'error')
    } catch (err) {
      showToast(err instanceof Error ? err.message : `${label}失败`, 'error')
    } finally {
      setTriggering(null)
    }
  }

  if (loading) {
    return <Loading size="lg" text="正在加载调度配置..." />
  }

  const scheduleSteps = [
    {
      key: 'fetch_time' as const,
      label: '采集时间',
      desc: '系统自动从各信源抓取最新资讯',
      icon: 'M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
      gradient: 'from-blue-500 to-indigo-600',
    },
    {
      key: 'generate_time' as const,
      label: '生成时间',
      desc: 'AI处理资讯并生成日报内容',
      icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      gradient: 'from-purple-500 to-pink-600',
    },
    {
      key: 'send_time' as const,
      label: '发送时间',
      desc: '将日报邮件发送给所有收件人',
      icon: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
      gradient: 'from-green-500 to-teal-600',
    },
  ]

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Enable/Disable */}
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-800">调度总开关</h3>
            <p className="text-sm text-gray-500 mt-1">开启后系统将按计划自动执行任务</p>
          </div>
          <button
            onClick={() => handleChange('enabled', !config.enabled)}
            className={`relative inline-flex h-8 w-14 items-center rounded-full transition ${
              config.enabled ? 'bg-green-500' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-md transition ${
                config.enabled ? 'translate-x-7' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        {config.enabled && (
          <div className="mt-4 p-3 bg-green-50 rounded-lg flex items-center gap-2">
            <svg className="w-5 h-5 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-green-700">调度已启用，系统将按计划自动运行</p>
          </div>
        )}
      </div>

      {/* Schedule Steps */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-1">任务执行计划</h3>
        <p className="text-sm text-gray-500 mb-6">设置各阶段任务的执行时间</p>

        <div className="space-y-4">
          {scheduleSteps.map((step, index) => (
            <div
              key={step.key}
              className="flex items-center gap-4 p-4 rounded-xl border border-gray-100 hover:border-purple-200 hover:bg-purple-50 transition"
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${step.gradient} flex items-center justify-center flex-shrink-0`}>
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={step.icon} />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="badge bg-gray-100 text-gray-500">步骤 {index + 1}</span>
                  <h4 className="font-semibold text-gray-800">{step.label}</h4>
                </div>
                <p className="text-sm text-gray-500 mt-0.5">{step.desc}</p>
              </div>
              <div className="flex-shrink-0">
                <input
                  type="time"
                  value={config[step.key]}
                  onChange={(e) => handleChange(step.key, e.target.value)}
                  className="input w-32 text-center font-mono"
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Advanced Settings */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">高级设置</h3>
        <div className="space-y-4">
          <div>
            <label className="label">时区</label>
            <select
              value={config.timezone}
              onChange={(e) => handleChange('timezone', e.target.value)}
              className="input"
            >
              {timezones.map((tz) => (
                <option key={tz} value={tz}>{tz}</option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">请选择您所在地区的时区</p>
          </div>

          <div className="flex items-center justify-between p-4 rounded-xl border border-gray-100">
            <div>
              <p className="font-medium text-gray-800">仅工作日发送</p>
              <p className="text-sm text-gray-500 mt-0.5">关闭后周末也会发送日报</p>
            </div>
            <button
              onClick={() => handleChange('weekdays_only', !config.weekdays_only)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
                config.weekdays_only ? 'bg-purple-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                  config.weekdays_only ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Manual Triggers */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-1">手动操作</h3>
        <p className="text-sm text-gray-500 mb-4">无需等待定时计划，立即执行任务（操作记录可在任务日志查看）</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <button
            onClick={() => handleTrigger('fetch', '/schedule/trigger-fetch', '采集')}
            disabled={triggering !== null}
            className="group relative overflow-hidden rounded-xl border border-gray-200 p-5 text-left hover:border-transparent hover:shadow-lg transition disabled:opacity-50"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-indigo-600 opacity-0 group-hover:opacity-100 transition" />
            <div className="relative">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mb-3 group-hover:bg-white group-hover:bg-opacity-20">
                {triggering === 'fetch' ? (
                  <svg className="w-5 h-5 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                )}
              </div>
              <p className="font-semibold text-gray-800 group-hover:text-white transition">立即采集</p>
              <p className="text-sm text-gray-500 group-hover:text-blue-100 transition mt-1">抓取最新资讯</p>
            </div>
          </button>

          <button
            onClick={() => handleTrigger('generate', '/schedule/trigger-generate', '生成日报')}
            disabled={triggering !== null}
            className="group relative overflow-hidden rounded-xl border border-gray-200 p-5 text-left hover:border-transparent hover:shadow-lg transition disabled:opacity-50"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500 to-pink-600 opacity-0 group-hover:opacity-100 transition" />
            <div className="relative">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center mb-3 group-hover:bg-white group-hover:bg-opacity-20">
                {triggering === 'generate' ? (
                  <svg className="w-5 h-5 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                )}
              </div>
              <p className="font-semibold text-gray-800 group-hover:text-white transition">生成日报</p>
              <p className="text-sm text-gray-500 group-hover:text-purple-100 transition mt-1">AI生成日报内容</p>
            </div>
          </button>

          <button
            onClick={() => handleTrigger('send', '/schedule/trigger-send', '发送日报')}
            disabled={triggering !== null}
            className="group relative overflow-hidden rounded-xl border border-gray-200 p-5 text-left hover:border-transparent hover:shadow-lg transition disabled:opacity-50"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-green-500 to-teal-600 opacity-0 group-hover:opacity-100 transition" />
            <div className="relative">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-green-500 to-teal-600 flex items-center justify-center mb-3 group-hover:bg-white group-hover:bg-opacity-20">
                {triggering === 'send' ? (
                  <svg className="w-5 h-5 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                )}
              </div>
              <p className="font-semibold text-gray-800 group-hover:text-white transition">发送日报</p>
              <p className="text-sm text-gray-500 group-hover:text-green-100 transition mt-1">发送邮件给收件人</p>
            </div>
          </button>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn-primary px-8"
        >
          {saving ? '保存中...' : '保存配置'}
        </button>
      </div>
    </div>
  )
}
