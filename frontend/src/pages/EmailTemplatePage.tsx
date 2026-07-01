import { useState, useEffect } from 'react'
import client from '../api/client'
import { useToast } from '../components/Toast'
import Loading from '../components/Loading'

interface EmailTemplate {
  id: number
  name: string
  subject_template: string
  html_template: string | null
  is_active: boolean
  created_at?: string
  updated_at?: string
}

const defaultTemplate: EmailTemplate = {
  id: 0,
  name: 'default',
  subject_template: '{{date}} AI 前沿日报',
  html_template: '',
  is_active: true,
}

export default function EmailTemplatePage() {
  const [template, setTemplate] = useState<EmailTemplate>(defaultTemplate)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [previewing, setPreviewing] = useState(false)
  const [previewHtml, setPreviewHtml] = useState('')
  const [previewSubject, setPreviewSubject] = useState('')
  const [showPreview, setShowPreview] = useState(false)
  const { showToast } = useToast()

  useEffect(() => {
    fetchTemplate()
  }, [])

  const fetchTemplate = async () => {
    setLoading(true)
    try {
      const res = await client.get('/email-template')
      if (res.data) {
        setTemplate({ ...defaultTemplate, ...res.data })
      }
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await client.put('/email-template', {
        subject_template: template.subject_template,
        html_template: template.html_template,
        is_active: template.is_active,
      })
      showToast('保存成功', 'success')
      fetchTemplate()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handlePreview = async () => {
    setPreviewing(true)
    try {
      const res = await client.post('/email-template/preview')
      if (res.data) {
        setPreviewSubject(res.data.subject || '')
        setPreviewHtml(res.data.html || '')
        setShowPreview(true)
      }
    } catch (err) {
      showToast(err instanceof Error ? err.message : '预览失败', 'error')
    } finally {
      setPreviewing(false)
    }
  }

  if (loading) {
    return <Loading size="lg" text="正在加载邮件模板..." />
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-gray-800">邮件模板配置</h3>
        <p className="text-sm text-gray-500 mt-1">配置日报邮件的标题模板和内容样式</p>
      </div>

      <div className="card p-6 space-y-6">
        {/* 标题模板 */}
        <div>
          <label className="label">邮件标题模板</label>
          <input
            type="text"
            value={template.subject_template}
            onChange={(e) => setTemplate({ ...template, subject_template: e.target.value })}
            className="input"
            placeholder="{{date}} AI 前沿日报"
          />
          <div className="mt-2 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-700 font-medium mb-1">可用变量：</p>
            <div className="flex flex-wrap gap-2">
              <code className="px-2 py-0.5 bg-white rounded text-blue-600 text-xs">{'{{date}}'}</code>
              <span className="text-xs text-blue-500">→ 当前日期（如 2026-07-01）</span>
            </div>
            <div className="flex flex-wrap gap-2 mt-1">
              <code className="px-2 py-0.5 bg-white rounded text-blue-600 text-xs">{'{{digest_title}}'}</code>
              <span className="text-xs text-blue-500">→ 日报标题</span>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1">示例：{'{{date}} AI 前沿日报'} → 2026-07-01 AI 前沿日报</p>
        </div>

        {/* HTML模板 */}
        <div>
          <label className="label">HTML 模板（高级，留空使用内置默认模板）</label>
          <textarea
            value={template.html_template || ''}
            onChange={(e) => setTemplate({ ...template, html_template: e.target.value })}
            className="input font-mono text-xs"
            rows={6}
            placeholder="留空使用系统内置的精美 HTML 模板。如需自定义，请在此输入 Jinja2 格式的 HTML 模板。"
          />
          <p className="text-xs text-gray-400 mt-1">支持 Jinja2 模板语法。可用的变量：digest_title, date, summary, sections（每个 section 有 name 和 items）</p>
        </div>

        {/* 启用状态 */}
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={template.is_active}
              onChange={(e) => setTemplate({ ...template, is_active: e.target.checked })}
              className="w-4 h-4 rounded text-purple-600 focus:ring-purple-400"
            />
            <span className="text-sm text-gray-700">启用此模板</span>
          </label>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-3 pt-4 border-t border-gray-100">
          <button onClick={handleSave} disabled={saving} className="btn-primary">
            {saving ? '保存中...' : '保存配置'}
          </button>
          <button onClick={handlePreview} disabled={previewing} className="btn-secondary">
            {previewing ? '生成预览中...' : '👁️ 预览邮件'}
          </button>
        </div>
      </div>

      {/* 预览弹窗 */}
      {showPreview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" onClick={() => setShowPreview(false)}>
          <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold text-gray-800">邮件预览</h3>
              <button
                onClick={() => setShowPreview(false)}
                className="text-gray-400 hover:text-gray-600 p-1"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="px-4 py-2 bg-gray-50 border-b">
              <p className="text-sm text-gray-500">标题：</p>
              <p className="text-sm font-medium text-gray-800">{previewSubject}</p>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <iframe
                srcDoc={previewHtml}
                className="w-full h-full min-h-[400px] border-0"
                title="邮件预览"
                sandbox="allow-same-origin"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
