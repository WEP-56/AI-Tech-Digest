import { useState, useEffect, useCallback } from 'react'
import client from '../api/client'
import { useToast } from '../components/Toast'
import Loading from '../components/Loading'
import Modal from '../components/Modal'

interface Recipient {
  id: number
  email: string
  name: string
  recipient_type: string
  topics: string | null
  frequency: string
  enabled: boolean
  remark: string | null
  created_at?: string
}

interface RecipientForm {
  email: string
  name: string
  recipient_type: string
  topics: string
  frequency: string
  enabled: boolean
  remark: string
}

const emptyForm: RecipientForm = {
  email: '',
  name: '',
  recipient_type: 'to',
  topics: '',
  frequency: 'daily',
  enabled: true,
  remark: '',
}

const availableTopics = [
  'AI', '机器学习', '深度学习', '大模型', 'NLP', '计算机视觉',
  'Robotics', '云计算', '前端开发', '后端开发', 'DevOps', '安全',
]

export default function RecipientsPage() {
  const [recipients, setRecipients] = useState<Recipient[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<RecipientForm>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [testingId, setTestingId] = useState<number | null>(null)
  const { showToast } = useToast()

  const fetchRecipients = useCallback(async () => {
    setLoading(true)
    try {
      const res = await client.get('/recipients')
      setRecipients(Array.isArray(res.data) ? res.data : [])
    } catch (err) {
      showToast(err instanceof Error ? err.message : '获取收件人列表失败', 'error')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    fetchRecipients()
  }, [fetchRecipients])

  const handleAdd = () => {
    setForm(emptyForm)
    setEditingId(null)
    setModalOpen(true)
  }

  const handleEdit = (recipient: Recipient) => {
    setForm({
      email: recipient.email,
      name: recipient.name,
      recipient_type: recipient.recipient_type,
      topics: recipient.topics || '',
      frequency: recipient.frequency,
      enabled: recipient.enabled,
      remark: recipient.remark || '',
    })
    setEditingId(recipient.id)
    setModalOpen(true)
  }

  const handleSave = async () => {
    if (!form.email) {
      showToast('请输入邮箱地址', 'warning')
      return
    }
    setSaving(true)
    try {
      if (editingId) {
        await client.put(`/recipients/${editingId}`, form)
        showToast('更新成功', 'success')
      } else {
        await client.post('/recipients', form)
        showToast('添加成功', 'success')
      }
      setModalOpen(false)
      fetchRecipients()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除此收件人吗？')) return
    try {
      await client.delete(`/recipients/${id}`)
      showToast('删除成功', 'success')
      fetchRecipients()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '删除失败', 'error')
    }
  }

  const handleToggleEnabled = async (recipient: Recipient) => {
    try {
      await client.put(`/recipients/${recipient.id}`, { enabled: !recipient.enabled })
      showToast(recipient.enabled ? '已禁用' : '已启用', 'success')
      fetchRecipients()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '操作失败', 'error')
    }
  }

  const handleSendTest = async (id: number) => {
    setTestingId(id)
    try {
      const res = await client.post(`/recipients/${id}/send-test`)
      showToast(res.data?.message || '测试邮件已发送', res.data?.success ? 'success' : 'error')
    } catch (err) {
      showToast(err instanceof Error ? err.message : '发送失败', 'error')
    } finally {
      setTestingId(null)
    }
  }

  const toggleTopic = (topic: string) => {
    const current = form.topics ? form.topics.split(',').map((t) => t.trim()) : []
    const newTopics = current.includes(topic)
      ? current.filter((t) => t !== topic)
      : [...current, topic]
    setForm((prev) => ({ ...prev, topics: newTopics.join(', ') }))
  }

  const getTopicList = (topics: string | null): string[] => {
    if (!topics) return []
    return topics.split(',').map((t) => t.trim()).filter(Boolean)
  }

  const typeColors: Record<string, string> = {
    to: 'bg-blue-100 text-blue-700',
    cc: 'bg-yellow-100 text-yellow-700',
    bcc: 'bg-gray-100 text-gray-700',
  }

  const freqColors: Record<string, string> = {
    daily: 'bg-green-100 text-green-700',
    weekly: 'bg-purple-100 text-purple-700',
    manual: 'bg-orange-100 text-orange-700',
  }

  const freqLabels: Record<string, string> = {
    daily: '每日',
    weekly: '每周',
    manual: '手动',
  }

  if (loading) {
    return <Loading size="lg" text="正在加载收件人列表..." />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h3 className="text-xl font-semibold text-gray-800">收件人管理</h3>
          <p className="text-sm text-gray-500 mt-1">共 {recipients.length} 位收件人</p>
        </div>
        <button onClick={handleAdd} className="btn-primary">
          <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          新增收件人
        </button>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">邮箱</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">名称</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">类型</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">频率</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">订阅主题</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">状态</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {recipients.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-gray-400">
                    暂无收件人，点击右上角"新增收件人"添加
                  </td>
                </tr>
              ) : (
                recipients.map((r) => {
                  const topicList = getTopicList(r.topics)
                  return (
                    <tr key={r.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-800">{r.email}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{r.name || '-'}</td>
                      <td className="px-4 py-3">
                        <span className={`badge ${typeColors[r.recipient_type] || 'bg-gray-100'}`}>
                          {r.recipient_type?.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`badge ${freqColors[r.frequency] || 'bg-gray-100'}`}>
                          {freqLabels[r.frequency] || r.frequency}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {topicList.slice(0, 3).map((t) => (
                            <span key={t} className="badge bg-purple-50 text-purple-600">{t}</span>
                          ))}
                          {topicList.length > 3 && (
                            <span className="text-xs text-gray-400">+{topicList.length - 3}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleToggleEnabled(r)}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
                            r.enabled ? 'bg-green-500' : 'bg-gray-300'
                          }`}
                        >
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                              r.enabled ? 'translate-x-6' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => handleSendTest(r.id)}
                            disabled={testingId === r.id}
                            className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition disabled:opacity-50"
                            title="发送测试邮件"
                          >
                            {testingId === r.id ? (
                              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                              </svg>
                            ) : (
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                              </svg>
                            )}
                          </button>
                          <button
                            onClick={() => handleEdit(r)}
                            className="p-1.5 text-gray-600 hover:bg-gray-100 rounded-lg transition"
                            title="编辑"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                          <button
                            onClick={() => handleDelete(r.id)}
                            className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition"
                            title="删除"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingId ? '编辑收件人' : '新增收件人'}
        size="lg"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">邮箱地址 *</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="user@example.com"
                className="input"
              />
            </div>
            <div>
              <label className="label">名称</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="收件人名称"
                className="input"
              />
            </div>
            <div>
              <label className="label">收件类型</label>
              <select
                value={form.recipient_type}
                onChange={(e) => setForm({ ...form, recipient_type: e.target.value })}
                className="input"
              >
                <option value="to">收件人 (To)</option>
                <option value="cc">抄送 (CC)</option>
                <option value="bcc">密送 (BCC)</option>
              </select>
            </div>
            <div>
              <label className="label">发送频率</label>
              <select
                value={form.frequency}
                onChange={(e) => setForm({ ...form, frequency: e.target.value })}
                className="input"
              >
                <option value="daily">每日</option>
                <option value="weekly">每周</option>
                <option value="manual">手动发送</option>
              </select>
            </div>
          </div>

          <div>
            <label className="label">订阅主题（点击选择/取消）</label>
            <div className="flex flex-wrap gap-2">
              {availableTopics.map((topic) => {
                const selected = form.topics.split(',').map((t) => t.trim()).includes(topic)
                return (
                  <button
                    key={topic}
                    type="button"
                    onClick={() => toggleTopic(topic)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                      selected ? 'bg-brand-gradient text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {topic}
                  </button>
                )
              })}
            </div>
          </div>

          <div>
            <label className="label">备注</label>
            <input
              type="text"
              value={form.remark}
              onChange={(e) => setForm({ ...form, remark: e.target.value })}
              placeholder="可选备注"
              className="input"
            />
          </div>

          <div className="flex items-center gap-3 pt-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.enabled}
                onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
                className="w-4 h-4 rounded text-purple-600 focus:ring-purple-400"
              />
              <span className="text-sm text-gray-700">启用此收件人</span>
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button onClick={() => setModalOpen(false)} className="btn-secondary">取消</button>
            <button onClick={handleSave} disabled={saving} className="btn-primary">
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
