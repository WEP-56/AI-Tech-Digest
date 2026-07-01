import { useState, useEffect, useCallback } from 'react'
import client from '../api/client'
import { useToast } from '../components/Toast'
import Loading from '../components/Loading'

interface StorageItem {
  [key: string]: unknown
}

interface TabConfig {
  key: string
  label: string
  endpoint: string
  columns: { key: string; label: string; format?: (val: unknown) => string }[]
}

const tabs: TabConfig[] = [
  {
    key: 'raw',
    label: '原始资讯',
    endpoint: '/raw-items',
    columns: [
      { key: 'id', label: 'ID' },
      { key: 'title', label: '标题' },
      { key: 'source_id', label: '来源ID' },
      { key: 'url', label: 'URL' },
      { key: 'author', label: '作者' },
      { key: 'summary', label: '摘要' },
      { key: 'published_at', label: '发布时间', format: (v) => String(v || '').replace('T', ' ').substring(0, 19) },
      { key: 'fetched_at', label: '采集时间', format: (v) => String(v || '').replace('T', ' ').substring(0, 19) },
      { key: 'status', label: '状态' },
      { key: 'created_at', label: '创建时间', format: (v) => String(v || '').replace('T', ' ').substring(0, 19) },
    ],
  },
  {
    key: 'processed',
    label: '处理后资讯',
    endpoint: '/processed-items',
    columns: [
      { key: 'id', label: 'ID' },
      { key: 'title', label: '标题' },
      { key: 'summary', label: '摘要' },
      { key: 'why_it_matters', label: '为何重要' },
      { key: 'category', label: '分类' },
      { key: 'tags', label: '标签' },
      { key: 'importance', label: '重要度' },
      { key: 'source_name', label: '来源名称' },
      { key: 'source_url', label: '来源URL' },
      { key: 'created_at', label: '创建时间', format: (v) => String(v || '').replace('T', ' ').substring(0, 19) },
    ],
  },
  {
    key: 'emails',
    label: '邮件日志',
    endpoint: '/email-logs',
    columns: [
      { key: 'id', label: 'ID' },
      { key: 'digest_job_id', label: '任务ID' },
      { key: 'recipient_email', label: '收件人' },
      { key: 'subject', label: '主题' },
      { key: 'status', label: '状态' },
      { key: 'sent_at', label: '发送时间', format: (v) => String(v || '').replace('T', ' ').substring(0, 19) },
      { key: 'error_message', label: '错误信息' },
      { key: 'created_at', label: '创建时间', format: (v) => String(v || '').replace('T', ' ').substring(0, 19) },
    ],
  },
  {
    key: 'llm',
    label: 'LLM日志',
    endpoint: '/llm-logs',
    columns: [
      { key: 'id', label: 'ID' },
      { key: 'digest_job_id', label: '任务ID' },
      { key: 'provider_type', label: '提供商' },
      { key: 'model_name', label: '模型' },
      { key: 'status', label: '状态' },
      { key: 'input_tokens', label: '输入Tokens' },
      { key: 'output_tokens', label: '输出Tokens' },
      { key: 'latency_ms', label: '延迟(ms)' },
      { key: 'error_message', label: '错误信息' },
      { key: 'created_at', label: '时间', format: (v) => String(v || '').replace('T', ' ').substring(0, 19) },
    ],
  },
  {
    key: 'fetch-logs',
    label: '信源抓取日志',
    endpoint: '/source-fetch-logs',
    columns: [
      { key: 'id', label: 'ID' },
      { key: 'source_id', label: '信源ID' },
      { key: 'status', label: '状态' },
      { key: 'fetched_count', label: '抓取数' },
      { key: 'new_count', label: '新增数' },
      { key: 'http_status_code', label: 'HTTP状态码' },
      { key: 'started_at', label: '开始时间', format: (v) => String(v || '').replace('T', ' ').substring(0, 19) },
      { key: 'finished_at', label: '完成时间', format: (v) => String(v || '').replace('T', ' ').substring(0, 19) },
      { key: 'error_message', label: '错误信息' },
      { key: 'created_at', label: '创建时间', format: (v) => String(v || '').replace('T', ' ').substring(0, 19) },
    ],
  },
]

export default function StoragePage() {
  const [activeTab, setActiveTab] = useState(0)
  const [data, setData] = useState<StorageItem[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [cleaning, setCleaning] = useState(false)
  const [showCleanupConfirm, setShowCleanupConfirm] = useState(false)
  const [cleanupDays, setCleanupDays] = useState(30)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [deleting, setDeleting] = useState(false)
  const { showToast } = useToast()

  const currentTab = tabs[activeTab]

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await client.get(currentTab.endpoint, { params: { page, page_size: 20 } })
      const d = res.data
      if (Array.isArray(d)) {
        setData(d)
        setTotalPages(1)
      } else {
        setData(d.items || [])
        setTotalPages(d.total_pages || Math.ceil((d.total || 0) / 20) || 1)
      }
      setSelectedIds([])
    } catch (err) {
      showToast(err instanceof Error ? err.message : '获取数据失败', 'error')
      setData([])
    } finally {
      setLoading(false)
    }
  }, [currentTab, page, showToast])

  useEffect(() => {
    setPage(1)
    setSelectedIds([])
  }, [activeTab])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleCleanup = async () => {
    setCleaning(true)
    try {
      await client.delete('/storage/cleanup', { params: { days: cleanupDays } })
      showToast(`已清理 ${cleanupDays} 天前的历史数据`, 'success')
      setShowCleanupConfirm(false)
      fetchData()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '清理失败', 'error')
    } finally {
      setCleaning(false)
    }
  }

  const visibleIds = data
    .map((item) => item.id)
    .filter((id): id is number => typeof id === 'number')
  const allVisibleSelected = visibleIds.length > 0 && visibleIds.every((id) => selectedIds.includes(id))

  const toggleSelectAll = () => {
    setSelectedIds(allVisibleSelected ? [] : visibleIds)
  }

  const toggleSelectOne = (id: number) => {
    setSelectedIds((prev) => prev.includes(id) ? prev.filter((itemId) => itemId !== id) : [...prev, id])
  }

  const handleDeleteOne = async (id: number) => {
    if (!window.confirm(`确定删除 ID ${id} 吗？此操作不可恢复。`)) return
    setDeleting(true)
    try {
      const res = await client.delete(`/storage/${currentTab.key}/${id}`)
      showToast(res.data?.message || '已删除', 'success')
      fetchData()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '删除失败', 'error')
    } finally {
      setDeleting(false)
    }
  }

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) {
      showToast('请先勾选要删除的数据', 'error')
      return
    }
    if (!window.confirm(`确定删除已勾选的 ${selectedIds.length} 条数据吗？此操作不可恢复。`)) return
    setDeleting(true)
    try {
      const res = await client.post(`/storage/${currentTab.key}/bulk-delete`, { ids: selectedIds })
      showToast(res.data?.message || '已删除', 'success')
      fetchData()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '批量删除失败', 'error')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h3 className="text-xl font-semibold text-gray-800">存储管理</h3>
          <p className="text-sm text-gray-500 mt-1">查看和管理系统存储的数据</p>
        </div>
        <button
          onClick={handleBulkDelete}
          disabled={selectedIds.length === 0 || deleting}
          className="btn-danger disabled:opacity-50"
        >
          删除已选 {selectedIds.length > 0 ? `(${selectedIds.length})` : ''}
        </button>
        <button
          onClick={() => setShowCleanupConfirm(true)}
          className="btn-danger"
        >
          <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          清理历史数据
        </button>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-gray-200">
        {tabs.map((tab, index) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(index)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition ${
              activeTab === index
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Data Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <Loading text="正在加载数据..." />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="px-4 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={allVisibleSelected}
                        onChange={toggleSelectAll}
                        className="h-4 w-4 rounded border-gray-300 text-purple-600"
                      />
                    </th>
                    {currentTab.columns.map((col) => (
                      <th key={col.key} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase whitespace-nowrap">
                        {col.label}
                      </th>
                    ))}
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase whitespace-nowrap">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.length === 0 ? (
                    <tr>
                      <td colSpan={currentTab.columns.length + 2} className="px-4 py-12 text-center text-gray-400">
                        暂无数据
                      </td>
                    </tr>
                  ) : (
                    data.map((item, idx) => (
                      <tr key={(item.id as number) || idx} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          {typeof item.id === 'number' && (
                            <input
                              type="checkbox"
                              checked={selectedIds.includes(item.id)}
                              onChange={() => toggleSelectOne(item.id as number)}
                              className="h-4 w-4 rounded border-gray-300 text-purple-600"
                            />
                          )}
                        </td>
                        {currentTab.columns.map((col) => {
                          const val = item[col.key]
                          const display = col.format ? col.format(val) : String(val ?? '-')
                          return (
                            <td key={col.key} className="px-4 py-3 text-sm text-gray-700 max-w-xs truncate" title={display}>
                              {display}
                            </td>
                          )
                        })}
                        <td className="px-4 py-3">
                          {typeof item.id === 'number' && (
                            <button
                              onClick={() => handleDeleteOne(item.id as number)}
                              disabled={deleting}
                              className="text-sm font-medium text-red-600 hover:text-red-700 disabled:opacity-50"
                            >
                              删除
                            </button>
                          )}
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
          </>
        )}
      </div>

      {/* Cleanup Confirmation Modal */}
      {showCleanupConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={() => setShowCleanupConfirm(false)} />
          <div className="relative bg-white rounded-2xl shadow-2xl p-6 max-w-md w-full animate-slide-up">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-800">清理历史数据</h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              此操作将删除指定天数之前的历史数据，不可恢复。请选择保留天数：
            </p>
            <div className="mb-4">
              <label className="label">保留最近天数</label>
              <input
                type="number"
                value={cleanupDays}
                onChange={(e) => setCleanupDays(Math.max(1, parseInt(e.target.value) || 30))}
                min={1}
                className="input"
              />
            </div>
            <div className="flex justify-end gap-3">
              <button onClick={() => setShowCleanupConfirm(false)} className="btn-secondary">
                取消
              </button>
              <button onClick={handleCleanup} disabled={cleaning} className="btn-danger">
                {cleaning ? '清理中...' : `清理 ${cleanupDays} 天前数据`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
