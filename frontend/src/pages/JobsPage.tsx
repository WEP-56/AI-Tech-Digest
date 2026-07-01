import { useState, useEffect, useCallback } from 'react'
import client from '../api/client'
import { useToast } from '../components/Toast'
import Loading from '../components/Loading'
import Modal from '../components/Modal'

interface Job {
  id: number
  job_date: string
  job_type: string
  status: string
  raw_count: number
  filtered_count: number
  processed_count: number
  email_sent_count: number
  started_at?: string
  finished_at?: string
  error_message?: string
  created_at: string
}

const statusColors: Record<string, string> = {
  success: 'bg-green-100 text-green-700',
  partial_success: 'bg-yellow-100 text-yellow-700',
  failed: 'bg-red-100 text-red-700',
  error: 'bg-red-100 text-red-700',
  running: 'bg-blue-100 text-blue-700',
  pending: 'bg-yellow-100 text-yellow-700',
}

const jobTypeLabels: Record<string, string> = {
  manual: '手动',
  daily: '定时',
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [detailJob, setDetailJob] = useState<Job | null>(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const { showToast } = useToast()

  const fetchJobs = useCallback(async () => {
    setLoading(true)
    try {
      const res = await client.get('/jobs', { params: { page, page_size: 20 } })
      const data = res.data
      if (Array.isArray(data)) {
        setJobs(data)
        setTotalPages(1)
      } else {
        setJobs(data.items || [])
        setTotalPages(data.total_pages || Math.ceil((data.total || 0) / 20) || 1)
      }
    } catch (err) {
      showToast(err instanceof Error ? err.message : '获取任务列表失败', 'error')
    } finally {
      setLoading(false)
    }
  }, [showToast, page])

  useEffect(() => {
    fetchJobs()
  }, [fetchJobs])

  const handleViewDetail = async (job: Job) => {
    setDetailJob(job)
  }

  const handleAction = async (action: string, endpoint: string, successMsg: string) => {
    setActionLoading(action)
    try {
      await client.post(endpoint)
      showToast(successMsg, 'success')
      fetchJobs()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '操作失败', 'error')
    } finally {
      setActionLoading(null)
    }
  }

  const quickActions = [
    { label: '采集', action: 'fetch', endpoint: '/jobs/fetch-now', msg: '采集任务已触发', icon: 'M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745' },
    { label: '生成', action: 'generate', endpoint: '/jobs/generate-digest', msg: '日报生成任务已触发', icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
    { label: '发送', action: 'send', endpoint: '/jobs/send-now', msg: '日报发送任务已触发', icon: 'M12 19l9 2-9-18-9 18 9-2zm0 0v-8' },
  ]

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return dateStr.replace('T', ' ').substring(0, 19)
  }

  if (loading) {
    return <Loading size="lg" text="正在加载任务日志..." />
  }

  return (
    <div className="space-y-6">
      {/* Header & Quick Actions */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h3 className="text-xl font-semibold text-gray-800">任务日志</h3>
          <p className="text-sm text-gray-500 mt-1">查看任务历史记录与手动触发任务</p>
        </div>
        <div className="flex gap-2">
          {quickActions.map((qa) => (
            <button
              key={qa.action}
              onClick={() => handleAction(qa.action, qa.endpoint, qa.msg)}
              disabled={actionLoading === qa.action}
              className="btn-primary btn-sm"
            >
              {actionLoading === qa.action ? `${qa.label}中...` : qa.label}
            </button>
          ))}
        </div>
      </div>

      {/* Jobs Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">ID</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">任务日期</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">类型</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">状态</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">创建时间</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">完成时间</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">数据统计</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-gray-400">
                    暂无任务记录
                  </td>
                </tr>
              ) : (
                jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-600">#{job.id}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{job.job_date}</td>
                    <td className="px-4 py-3 text-sm text-gray-800">
                      {jobTypeLabels[job.job_type] || job.job_type}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`badge ${statusColors[job.status] || 'bg-gray-100 text-gray-600'}`}>
                        {job.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{formatDate(job.created_at)}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{formatDate(job.finished_at)}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      <div className="flex gap-2 flex-wrap">
                        <span className="badge bg-blue-50 text-blue-600">原始 {job.raw_count}</span>
                        <span className="badge bg-cyan-50 text-cyan-600">过滤 {job.filtered_count}</span>
                        <span className="badge bg-green-50 text-green-600">处理 {job.processed_count}</span>
                        <span className="badge bg-purple-50 text-purple-600">发送 {job.email_sent_count}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleViewDetail(job)}
                        className="text-purple-600 hover:text-purple-800 text-sm font-medium"
                      >
                        详情
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              第 {page} / {totalPages} 页
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="btn-secondary btn-sm"
              >
                上一页
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="btn-secondary btn-sm"
              >
                下一页
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      <Modal
        isOpen={!!detailJob}
        onClose={() => setDetailJob(null)}
        title={`任务详情 #${detailJob?.id || ''}`}
        size="xl"
      >
        {detailJob && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400">任务日期</p>
                <p className="text-sm font-medium text-gray-800 mt-1">{detailJob.job_date}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400">任务类型</p>
                <p className="text-sm font-medium text-gray-800 mt-1">{jobTypeLabels[detailJob.job_type] || detailJob.job_type}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400">状态</p>
                <span className={`badge ${statusColors[detailJob.status] || 'bg-gray-100'} mt-1`}>{detailJob.status}</span>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400">创建时间</p>
                <p className="text-sm text-gray-800 mt-1">{formatDate(detailJob.created_at)}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400">开始时间</p>
                <p className="text-sm text-gray-800 mt-1">{formatDate(detailJob.started_at)}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400">完成时间</p>
                <p className="text-sm text-gray-800 mt-1">{formatDate(detailJob.finished_at)}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-blue-50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-blue-600">{detailJob.raw_count}</p>
                <p className="text-xs text-gray-500 mt-1">原始数</p>
              </div>
              <div className="bg-cyan-50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-cyan-600">{detailJob.filtered_count}</p>
                <p className="text-xs text-gray-500 mt-1">过滤数</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-green-600">{detailJob.processed_count}</p>
                <p className="text-xs text-gray-500 mt-1">处理数</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-purple-600">{detailJob.email_sent_count}</p>
                <p className="text-xs text-gray-500 mt-1">发送数</p>
              </div>
            </div>

            {detailJob.error_message && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm font-medium text-red-700 mb-1">错误信息</p>
                <p className="text-sm text-red-600">{detailJob.error_message}</p>
              </div>
            )}

            <div className="flex justify-end pt-4 border-t border-gray-100">
              <button onClick={() => setDetailJob(null)} className="btn-primary">
                关闭
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
