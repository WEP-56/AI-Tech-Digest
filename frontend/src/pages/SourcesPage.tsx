import { useState, useEffect } from 'react'
import client from '../api/client'
import { useToast } from '../components/Toast'
import Loading from '../components/Loading'
import Modal from '../components/Modal'

interface Source {
  id?: number
  name: string
  source_type: string
  url: string
  category?: string
  language: string
  include_keywords?: string
  exclude_keywords?: string
  max_items: number
  need_full_text: boolean
  send_to_llm: boolean
  weight: number
  enabled: boolean
  github_language?: string
  github_since: string
  min_stars: number
  created_at?: string
}

interface FetchResult {
  success: boolean
  message: string
  fetched_count: number
  sample_items: Array<{ title: string; url: string; summary: string }>
}

const sourceTypeLabels: Record<string, string> = {
  rss: 'RSS 订阅',
  github_trending: 'GitHub Trending',
  hackernews_rss: 'Hacker News',
  arxiv_rss: 'Arxiv 论文',
}

const emptyForm: Source = {
  name: '',
  source_type: 'rss',
  url: '',
  category: '',
  language: 'zh',
  include_keywords: '',
  exclude_keywords: '',
  max_items: 20,
  need_full_text: false,
  send_to_llm: true,
  weight: 1.0,
  enabled: true,
  github_language: '',
  github_since: 'daily',
  min_stars: 0,
}

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editSource, setEditSource] = useState<Source | null>(null)
  const [form, setForm] = useState<Source>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [testingId, setTestingId] = useState<number | null>(null)
  const [fetchResult, setFetchResult] = useState<FetchResult | null>(null)
  const [resultModalOpen, setResultModalOpen] = useState(false)
  const { showToast } = useToast()

  useEffect(() => {
    fetchSources()
  }, [])

  const fetchSources = async () => {
    setLoading(true)
    try {
      const res = await client.get('/sources')
      setSources(Array.isArray(res.data) ? res.data : [])
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const handleOpenAdd = () => {
    setEditSource(null)
    setForm(emptyForm)
    setModalOpen(true)
  }

  const handleOpenEdit = (source: Source) => {
    setEditSource(source)
    setForm({ ...emptyForm, ...source })
    setModalOpen(true)
  }

  const handleSave = async () => {
    if (!form.name || !form.url) {
      showToast('请填写信源名称和URL', 'warning')
      return
    }
    setSaving(true)
    try {
      if (editSource?.id) {
        await client.put(`/sources/${editSource.id}`, form)
      } else {
        await client.post('/sources', form)
      }
      showToast(editSource ? '更新成功' : '添加成功', 'success')
      setModalOpen(false)
      fetchSources()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定删除此信源？')) return
    try {
      await client.delete(`/sources/${id}`)
      showToast('已删除', 'success')
      fetchSources()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '删除失败', 'error')
    }
  }

  const handleToggleEnabled = async (source: Source) => {
    if (!source.id) return
    try {
      await client.put(`/sources/${source.id}`, { enabled: !source.enabled })
      showToast(source.enabled ? '已禁用' : '已启用', 'success')
      fetchSources()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '操作失败', 'error')
    }
  }

  const handleTestFetch = async (source: Source) => {
    if (!source.id) return
    setTestingId(source.id)
    try {
      const res = await client.post(`/sources/${source.id}/test-fetch`)
      setFetchResult(res.data)
      setResultModalOpen(true)
    } catch (err) {
      showToast(err instanceof Error ? err.message : '测试失败', 'error')
    } finally {
      setTestingId(null)
    }
  }

  const handleFieldChange = (field: keyof Source, value: string | number | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  if (loading) {
    return <Loading size="lg" text="正在加载信源列表..." />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">信源配置</h2>
          <p className="text-sm text-gray-500 mt-1">管理信息采集来源，支持 RSS 和 GitHub Trending</p>
        </div>
        <button onClick={handleOpenAdd} className="btn-primary">+ 添加信源</button>
      </div>

      {/* Source Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        {sources.map((source) => (
          <div key={source.id} className="card p-5 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-lg font-semibold text-gray-800">{source.name}</h3>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${source.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {source.enabled ? '已启用' : '已禁用'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs bg-purple-100 text-purple-700">
                    {sourceTypeLabels[source.source_type] || source.source_type}
                  </span>
                  {source.category && (
                    <span className="px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-600">{source.category}</span>
                  )}
                </div>
                <p className="text-sm text-gray-500 mt-1 break-all">{source.url}</p>
                <div className="flex gap-3 mt-2 text-xs text-gray-400">
                  <span>最多 {source.max_items} 条</span>
                  <span>权重 {source.weight}</span>
                  {source.language && <span>语言: {source.language}</span>}
                </div>
              </div>
              {/* 启用开关 */}
              <button
                onClick={() => handleToggleEnabled(source)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition flex-shrink-0 ${source.enabled ? 'bg-green-500' : 'bg-gray-300'}`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${source.enabled ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
            </div>

            {source.include_keywords && (
              <div className="flex flex-wrap gap-1 mb-2">
                {source.include_keywords.split(',').map((kw, i) => (
                  kw.trim() && <span key={i} className="px-1.5 py-0.5 rounded text-xs bg-green-50 text-green-600">{kw.trim()}</span>
                ))}
              </div>
            )}

            <div className="flex gap-2 pt-3 border-t border-gray-100">
              <button
                onClick={() => handleOpenEdit(source)}
                className="px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition"
              >
                编辑
              </button>
              <button
                onClick={() => handleTestFetch(source)}
                disabled={testingId === source.id}
                className="px-3 py-1.5 text-sm text-purple-600 hover:bg-purple-50 rounded-lg transition disabled:opacity-50"
              >
                {testingId === source.id ? '抓取中...' : '🔍 测试抓取'}
              </button>
              <button
                onClick={() => handleDelete(source.id!)}
                className="px-3 py-1.5 text-sm text-red-500 hover:bg-red-50 rounded-lg transition ml-auto"
              >
                删除
              </button>
            </div>
          </div>
        ))}
      </div>

      {sources.length === 0 && (
        <div className="card p-12 text-center">
          <p className="text-gray-400 mb-4">还没有信源，点击上方按钮添加</p>
        </div>
      )}

      {/* Add/Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editSource ? '编辑信源' : '添加信源'}
        size="lg"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">信源名称 *</label>
              <input
                value={form.name}
                onChange={(e) => handleFieldChange('name', e.target.value)}
                className="input"
                placeholder="如：Hacker News"
              />
            </div>
            <div>
              <label className="label">信源类型 *</label>
              <select
                value={form.source_type}
                onChange={(e) => handleFieldChange('source_type', e.target.value)}
                className="input"
              >
                <option value="rss">RSS 订阅</option>
                <option value="github_trending">GitHub Trending</option>
                <option value="hackernews_rss">Hacker News (RSS)</option>
                <option value="arxiv_rss">Arxiv 论文 (RSS)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="label">URL *</label>
            <input
              value={form.url}
              onChange={(e) => handleFieldChange('url', e.target.value)}
              className="input"
              placeholder="https://..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">分类</label>
              <input
                value={form.category || ''}
                onChange={(e) => handleFieldChange('category', e.target.value)}
                className="input"
                placeholder="如：AI厂商动态"
              />
            </div>
            <div>
              <label className="label">语言</label>
              <select
                value={form.language}
                onChange={(e) => handleFieldChange('language', e.target.value)}
                className="input"
              >
                <option value="zh">中文</option>
                <option value="en">英文</option>
              </select>
            </div>
          </div>

          <div>
            <label className="label">包含关键词（逗号分隔，留空则不过滤）</label>
            <input
              value={form.include_keywords || ''}
              onChange={(e) => handleFieldChange('include_keywords', e.target.value)}
              className="input"
              placeholder="如：AI,LLM,agent,GPT"
            />
          </div>

          <div>
            <label className="label">排除关键词（逗号分隔）</label>
            <input
              value={form.exclude_keywords || ''}
              onChange={(e) => handleFieldChange('exclude_keywords', e.target.value)}
              className="input"
              placeholder="如：广告,招聘"
            />
          </div>

          {form.source_type === 'github_trending' && (
            <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="label">编程语言</label>
                <input
                  value={form.github_language || ''}
                  onChange={(e) => handleFieldChange('github_language', e.target.value)}
                  className="input"
                  placeholder="留空=全部"
                />
              </div>
              <div>
                <label className="label">时间范围</label>
                <select
                  value={form.github_since}
                  onChange={(e) => handleFieldChange('github_since', e.target.value)}
                  className="input"
                >
                  <option value="daily">今日</option>
                  <option value="weekly">本周</option>
                  <option value="monthly">本月</option>
                </select>
              </div>
              <div>
                <label className="label">最低 Stars</label>
                <input
                  type="number"
                  value={form.min_stars}
                  onChange={(e) => handleFieldChange('min_stars', parseInt(e.target.value) || 0)}
                  className="input"
                />
              </div>
            </div>
          )}

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="label">最大条数</label>
              <input
                type="number"
                value={form.max_items}
                onChange={(e) => handleFieldChange('max_items', parseInt(e.target.value) || 20)}
                className="input"
              />
            </div>
            <div>
              <label className="label">权重</label>
              <input
                type="number"
                step="0.1"
                value={form.weight}
                onChange={(e) => handleFieldChange('weight', parseFloat(e.target.value) || 1)}
                className="input"
              />
            </div>
            <div className="flex items-end gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.send_to_llm}
                  onChange={(e) => handleFieldChange('send_to_llm', e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">发送给LLM</span>
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <button onClick={() => setModalOpen(false)} className="btn-secondary">取消</button>
            <button onClick={handleSave} disabled={saving} className="btn-primary">
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Test Fetch Result Modal */}
      <Modal
        isOpen={resultModalOpen}
        onClose={() => setResultModalOpen(false)}
        title="抓取预览结果"
        size="lg"
      >
        {fetchResult && (
          <div className="space-y-4">
            {/* Result Summary */}
            <div className={`p-4 rounded-lg ${fetchResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <div className="flex items-center gap-2">
                <span className={`text-2xl ${fetchResult.success ? 'text-green-500' : 'text-red-500'}`}>
                  {fetchResult.success ? '✅' : '❌'}
                </span>
                <div>
                  <p className={`font-semibold ${fetchResult.success ? 'text-green-700' : 'text-red-700'}`}>
                    {fetchResult.message}
                  </p>
                  {fetchResult.success && fetchResult.fetched_count > 0 && (
                    <p className="text-sm text-green-600 mt-0.5">
                      共抓取到 <strong>{fetchResult.fetched_count}</strong> 条内容，以下是前 {fetchResult.sample_items.length} 条预览：
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Sample Items */}
            {fetchResult.sample_items.length > 0 && (
              <div className="space-y-3">
                {fetchResult.sample_items.map((item, i) => (
                  <div key={i} className="card p-4 bg-gray-50">
                    <div className="flex items-start gap-3">
                      <span className="w-7 h-7 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-sm font-bold flex-shrink-0">
                        {i + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-800 text-sm">{item.title}</h4>
                        {item.summary && (
                          <p className="text-xs text-gray-500 mt-1 line-clamp-2">{item.summary}</p>
                        )}
                        {item.url && (
                          <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:underline mt-1 inline-block">
                            {item.url}
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Empty State */}
            {fetchResult.success && fetchResult.fetched_count === 0 && (
              <div className="text-center py-8 text-gray-400">
                抓取成功，但未获取到内容。请检查信源URL是否正确。
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
