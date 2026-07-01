import { useState, useEffect } from 'react'
import client from '../api/client'
import { useToast } from '../components/Toast'
import Loading from '../components/Loading'
import Modal from '../components/Modal'

interface ModelConfig {
  id?: number
  name: string
  provider_type: string
  base_url: string
  api_key: string
  model_name: string
  temperature: number
  max_output_tokens: number
  timeout_seconds: number
  retry_count: number
  anthropic_version: string
  enabled: boolean
  is_default: boolean
  has_api_key?: boolean
  api_key_masked?: string
  created_at?: string
}

interface TestResult {
  success: boolean
  message: string
  response_text?: string
  latency_ms?: number
}

const providerLabels: Record<string, string> = {
  openai_completion: 'OpenAI Chat Completions',
  openai_responses: 'OpenAI Responses',
  anthropic_messages: 'Anthropic Messages',
}

const emptyForm: ModelConfig = {
  name: '',
  provider_type: 'openai_completion',
  base_url: 'https://api.openai.com',
  api_key: '',
  model_name: '',
  temperature: 0.3,
  max_output_tokens: 4000,
  timeout_seconds: 60,
  retry_count: 2,
  anthropic_version: '2023-06-01',
  enabled: true,
  is_default: false,
}

export default function ModelConfigsPage() {
  const [models, setModels] = useState<ModelConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editModel, setEditModel] = useState<ModelConfig | null>(null)
  const [form, setForm] = useState<ModelConfig>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [testingId, setTestingId] = useState<number | null>(null)
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [resultModalOpen, setResultModalOpen] = useState(false)
  const { showToast } = useToast()

  useEffect(() => {
    fetchModels()
  }, [])

  const fetchModels = async () => {
    setLoading(true)
    try {
      const res = await client.get('/models')
      setModels(Array.isArray(res.data) ? res.data : [])
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const handleOpenAdd = () => {
    setEditModel(null)
    setForm(emptyForm)
    setModalOpen(true)
  }

  const handleOpenEdit = (model: ModelConfig) => {
    setEditModel(model)
    setForm({ ...emptyForm, ...model, api_key: '' })
    setModalOpen(true)
  }

  const handleSave = async () => {
    if (!form.name || !form.base_url || !form.model_name) {
      showToast('请填写名称、Base URL 和模型名称', 'warning')
      return
    }
    if (!form.api_key && !form.has_api_key) {
      showToast('请填写 API Key', 'warning')
      return
    }
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        name: form.name,
        provider_type: form.provider_type,
        base_url: form.base_url,
        model_name: form.model_name,
        temperature: form.temperature,
        max_output_tokens: form.max_output_tokens,
        timeout_seconds: form.timeout_seconds,
        retry_count: form.retry_count,
        anthropic_version: form.anthropic_version,
        enabled: form.enabled,
        is_default: form.is_default,
      }
      if (form.api_key) {
        payload.api_key = form.api_key
      }

      if (editModel?.id) {
        await client.put(`/models/${editModel.id}`, payload)
      } else {
        await client.post('/models', payload)
      }
      showToast(editModel ? '更新成功' : '添加成功', 'success')
      setModalOpen(false)
      fetchModels()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定删除此模型配置？')) return
    try {
      await client.delete(`/models/${id}`)
      showToast('已删除', 'success')
      fetchModels()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '删除失败', 'error')
    }
  }

  const handleSetDefault = async (id: number) => {
    try {
      await client.post(`/models/${id}/set-default`)
      showToast('已设为默认模型', 'success')
      fetchModels()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '操作失败', 'error')
    }
  }

  const handleToggleEnabled = async (model: ModelConfig) => {
    if (!model.id) return
    try {
      await client.put(`/models/${model.id}`, { enabled: !model.enabled })
      showToast(model.enabled ? '已禁用' : '已启用', 'success')
      fetchModels()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '操作失败', 'error')
    }
  }

  const handleTest = async (model: ModelConfig) => {
    if (!model.id) return
    setTestingId(model.id)
    try {
      const res = await client.post(`/models/${model.id}/test`)
      setTestResult(res.data)
      setResultModalOpen(true)
    } catch (err) {
      showToast(err instanceof Error ? err.message : '测试失败', 'error')
    } finally {
      setTestingId(null)
    }
  }

  const handleFieldChange = (field: keyof ModelConfig, value: string | number | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  if (loading) {
    return <Loading size="lg" text="正在加载模型配置..." />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">模型配置</h2>
          <p className="text-sm text-gray-500 mt-1">配置 LLM 接口，支持 OpenAI 和 Anthropic 兼容接口</p>
        </div>
        <button onClick={handleOpenAdd} className="btn-primary">+ 添加模型</button>
      </div>

      {/* Model Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        {models.map((model) => (
          <div key={model.id} className="card p-5 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-lg font-semibold text-gray-800">{model.name}</h3>
                  {model.is_default && (
                    <span className="px-2 py-0.5 rounded text-xs bg-amber-100 text-amber-700 font-medium">⭐ 默认</span>
                  )}
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${model.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {model.enabled ? '已启用' : '已禁用'}
                  </span>
                </div>
                <div className="mt-2 space-y-1 text-sm">
                  <p className="text-gray-600">
                    <span className="text-gray-400">接口类型：</span>
                    {providerLabels[model.provider_type] || model.provider_type}
                  </p>
                  <p className="text-gray-600">
                    <span className="text-gray-400">Base URL：</span>
                    <span className="break-all">{model.base_url}</span>
                  </p>
                  <p className="text-gray-600">
                    <span className="text-gray-400">模型：</span>
                    {model.model_name}
                  </p>
                  <p className="text-gray-600">
                    <span className="text-gray-400">API Key：</span>
                    {model.has_api_key ? (
                      <span className="text-green-600">{model.api_key_masked || '已加密保存'}</span>
                    ) : (
                      <span className="text-red-400">未设置</span>
                    )}
                  </p>
                  <div className="flex gap-3 text-xs text-gray-400">
                    <span>温度: {model.temperature}</span>
                    <span>超时: {model.timeout_seconds}s</span>
                    <span>重试: {model.retry_count}</span>
                  </div>
                </div>
              </div>
              {/* 启用开关 */}
              <button
                onClick={() => handleToggleEnabled(model)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition flex-shrink-0 ${model.enabled ? 'bg-green-500' : 'bg-gray-300'}`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${model.enabled ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
            </div>

            <div className="flex flex-wrap gap-2 pt-3 border-t border-gray-100">
              <button
                onClick={() => handleTest(model)}
                disabled={testingId === model.id}
                className="px-3 py-1.5 text-sm text-purple-600 hover:bg-purple-50 rounded-lg transition disabled:opacity-50"
              >
                {testingId === model.id ? '测试中...' : '🔗 测试连通性'}
              </button>
              {!model.is_default && model.enabled && (
                <button
                  onClick={() => handleSetDefault(model.id!)}
                  className="px-3 py-1.5 text-sm text-amber-600 hover:bg-amber-50 rounded-lg transition"
                >
                  设为默认
                </button>
              )}
              <button
                onClick={() => handleOpenEdit(model)}
                className="px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition"
              >
                编辑
              </button>
              <button
                onClick={() => handleDelete(model.id!)}
                className="px-3 py-1.5 text-sm text-red-500 hover:bg-red-50 rounded-lg transition ml-auto"
              >
                删除
              </button>
            </div>
          </div>
        ))}
      </div>

      {models.length === 0 && (
        <div className="card p-12 text-center">
          <p className="text-gray-400 mb-4">还没有模型配置，点击上方按钮添加</p>
        </div>
      )}

      {/* Add/Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editModel ? '编辑模型配置' : '添加模型配置'}
        size="lg"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">配置名称 *</label>
              <input
                value={form.name}
                onChange={(e) => handleFieldChange('name', e.target.value)}
                className="input"
                placeholder="如：OpenAI GPT-4o"
              />
            </div>
            <div>
              <label className="label">接口类型 *</label>
              <select
                value={form.provider_type}
                onChange={(e) => handleFieldChange('provider_type', e.target.value)}
                className="input"
              >
                <option value="openai_completion">OpenAI Chat Completions</option>
                <option value="openai_responses">OpenAI Responses API</option>
                <option value="anthropic_messages">Anthropic Messages</option>
              </select>
            </div>
          </div>

          <div>
            <label className="label">Base URL *</label>
            <input
              value={form.base_url}
              onChange={(e) => handleFieldChange('base_url', e.target.value)}
              className="input"
              placeholder="https://api.openai.com"
            />
            <p className="text-xs text-gray-400 mt-1">不含 /v1 后缀，系统会自动拼接接口路径</p>
          </div>

          <div>
            <label className="label">API Key *</label>
            <input
              type="password"
              value={form.api_key}
              onChange={(e) => handleFieldChange('api_key', e.target.value)}
              className="input"
              placeholder={form.has_api_key ? `已保存（${form.api_key_masked || '********'}），留空不修改` : 'sk-...'}
            />
            {form.has_api_key && (
              <p className="text-xs text-green-600 mt-1">✓ API Key 已加密保存，当前显示：{form.api_key_masked}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">模型名称 *</label>
              <input
                value={form.model_name}
                onChange={(e) => handleFieldChange('model_name', e.target.value)}
                className="input"
                placeholder="如：gpt-4o / claude-3-5-sonnet-20241022"
              />
            </div>
            <div>
              <label className="label">Temperature</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={form.temperature}
                onChange={(e) => handleFieldChange('temperature', parseFloat(e.target.value) || 0)}
                className="input"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="label">最大输出 Tokens</label>
              <input
                type="number"
                value={form.max_output_tokens}
                onChange={(e) => handleFieldChange('max_output_tokens', parseInt(e.target.value) || 4000)}
                className="input"
              />
            </div>
            <div>
              <label className="label">超时（秒）</label>
              <input
                type="number"
                value={form.timeout_seconds}
                onChange={(e) => handleFieldChange('timeout_seconds', parseInt(e.target.value) || 60)}
                className="input"
              />
            </div>
            <div>
              <label className="label">重试次数</label>
              <input
                type="number"
                value={form.retry_count}
                onChange={(e) => handleFieldChange('retry_count', parseInt(e.target.value) || 2)}
                className="input"
              />
            </div>
          </div>

          {form.provider_type === 'anthropic_messages' && (
            <div>
              <label className="label">Anthropic API 版本</label>
              <input
                value={form.anthropic_version}
                onChange={(e) => handleFieldChange('anthropic_version', e.target.value)}
                className="input"
                placeholder="2023-06-01"
              />
            </div>
          )}

          <div className="flex items-center gap-6 pt-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.enabled}
                onChange={(e) => handleFieldChange('enabled', e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-sm">启用</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.is_default}
                onChange={(e) => handleFieldChange('is_default', e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-sm">设为默认模型</span>
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <button onClick={() => setModalOpen(false)} className="btn-secondary">取消</button>
            <button onClick={handleSave} disabled={saving} className="btn-primary">
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Test Result Modal */}
      <Modal
        isOpen={resultModalOpen}
        onClose={() => setResultModalOpen(false)}
        title="模型连通性测试结果"
        size="md"
      >
        {testResult && (
          <div className="space-y-4">
            {/* Status Banner */}
            <div className={`p-4 rounded-lg ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <div className="flex items-center gap-3">
                <span className={`text-3xl ${testResult.success ? 'text-green-500' : 'text-red-500'}`}>
                  {testResult.success ? '✅' : '❌'}
                </span>
                <div>
                  <p className={`font-bold ${testResult.success ? 'text-green-700' : 'text-red-700'}`}>
                    {testResult.success ? '连接成功' : '连接失败'}
                  </p>
                  <p className={`text-sm mt-0.5 ${testResult.success ? 'text-green-600' : 'text-red-600'}`}>
                    {testResult.message}
                  </p>
                </div>
              </div>
            </div>

            {/* Latency */}
            {testResult.latency_ms != null && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-400">响应延迟：</span>
                <span className={`font-mono font-semibold ${testResult.latency_ms < 2000 ? 'text-green-600' : testResult.latency_ms < 5000 ? 'text-amber-600' : 'text-red-500'}`}>
                  {testResult.latency_ms} ms
                </span>
                {testResult.latency_ms < 2000 && <span className="text-xs text-green-500">（响应迅速）</span>}
                {testResult.latency_ms >= 2000 && testResult.latency_ms < 5000 && <span className="text-xs text-amber-500">（响应正常）</span>}
                {testResult.latency_ms >= 5000 && <span className="text-xs text-red-400">（响应较慢，建议增加超时时间）</span>}
              </div>
            )}

            {/* Response Text */}
            {testResult.response_text && (
              <div>
                <p className="text-sm text-gray-500 mb-2">模型回复：</p>
                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-700 font-mono whitespace-pre-wrap">{testResult.response_text}</p>
                </div>
              </div>
            )}

            {/* Error Detail */}
            {!testResult.success && testResult.message && (
              <div>
                <p className="text-sm text-gray-500 mb-2">错误详情：</p>
                <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                  <p className="text-sm text-red-600 font-mono whitespace-pre-wrap break-all">{testResult.message}</p>
                </div>
                <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-700">💡 常见原因：</p>
                  <ul className="text-xs text-blue-600 mt-1 space-y-0.5">
                    <li>• API Key 错误或已过期</li>
                    <li>• Base URL 不正确（不需要加 /v1 后缀）</li>
                    <li>• 模型名称拼写错误</li>
                    <li>• 网络无法访问该 API 地址</li>
                    <li>• 账户余额不足或达到调用限制</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
