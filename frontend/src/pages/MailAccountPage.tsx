import { useState, useEffect } from 'react'
import client from '../api/client'
import { useToast } from '../components/Toast'
import Loading from '../components/Loading'

interface MailAccount {
  id?: number
  email: string
  sender_name: string
  smtp_host: string
  smtp_port: number
  smtp_security: string
  smtp_auth_code: string
  imap_host: string
  imap_port: number
  imap_security: string
  imap_auth_code: string
  enabled: boolean
  has_smtp_auth_code?: boolean
  has_imap_auth_code?: boolean
  smtp_auth_code_masked?: string
  imap_auth_code_masked?: string
}

const defaultAccount: MailAccount = {
  email: '',
  sender_name: 'AI Tech Digest',
  smtp_host: 'smtp.qq.com',
  smtp_port: 465,
  smtp_security: 'ssl',
  smtp_auth_code: '',
  imap_host: 'imap.qq.com',
  imap_port: 993,
  imap_security: 'ssl',
  imap_auth_code: '',
  enabled: false,
}

export default function MailAccountPage() {
  const [account, setAccount] = useState<MailAccount>(defaultAccount)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testingSmtp, setTestingSmtp] = useState(false)
  const [sendingTest, setSendingTest] = useState(false)
  const { showToast } = useToast()

  useEffect(() => {
    fetchAccount()
  }, [])

  const fetchAccount = async () => {
    setLoading(true)
    try {
      const res = await client.get('/mail-account')
      const list = Array.isArray(res.data) ? res.data : []
      if (list.length > 0) {
        const data = list[0]
        setAccount({
          ...defaultAccount,
          ...data,
          smtp_auth_code: '',
          imap_auth_code: '',
        })
      }
    } catch {
      // 没有配置也不报错
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!account.email) {
      showToast('请填写发件邮箱地址', 'warning')
      return
    }
    if (!account.smtp_auth_code && !account.has_smtp_auth_code) {
      showToast('请填写SMTP授权码', 'warning')
      return
    }
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        email: account.email,
        sender_name: account.sender_name,
        smtp_host: account.smtp_host,
        smtp_port: account.smtp_port,
        smtp_security: account.smtp_security,
        imap_host: account.imap_host,
        imap_port: account.imap_port,
        imap_security: account.imap_security,
        enabled: account.enabled,
      }
      // 只有填了新授权码才发送
      if (account.smtp_auth_code) {
        payload.smtp_auth_code = account.smtp_auth_code
      }
      if (account.imap_auth_code) {
        payload.imap_auth_code = account.imap_auth_code
      }

      if (account.id) {
        await client.put(`/mail-account/${account.id}`, payload)
      } else {
        await client.post('/mail-account', payload)
      }
      showToast('保存成功', 'success')
      fetchAccount()
    } catch (err) {
      showToast(err instanceof Error ? err.message : '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleTestSmtp = async () => {
    if (!account.id) {
      showToast('请先保存配置', 'warning')
      return
    }
    setTestingSmtp(true)
    try {
      const res = await client.post(`/mail-account/${account.id}/test-smtp`)
      showToast(res.data?.message || 'SMTP连接测试成功', res.data?.success ? 'success' : 'error')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'SMTP测试失败', 'error')
    } finally {
      setTestingSmtp(false)
    }
  }

  const handleSendTest = async () => {
    if (!account.id) {
      showToast('请先保存配置', 'warning')
      return
    }
    setSendingTest(true)
    try {
      const res = await client.post(`/mail-account/${account.id}/send-test`)
      showToast(res.data?.message || '测试邮件已发送', res.data?.success ? 'success' : 'error')
    } catch (err) {
      showToast(err instanceof Error ? err.message : '发送失败', 'error')
    } finally {
      setSendingTest(false)
    }
  }

  const handleChange = (field: keyof MailAccount, value: string | number | boolean) => {
    setAccount((prev) => ({ ...prev, [field]: value }))
  }

  if (loading) {
    return <Loading size="lg" text="正在加载邮箱配置..." />
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* QQ 邮箱提示 */}
      <div className="card p-4 bg-blue-50 border-blue-200">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-sm text-blue-700">
            <p className="font-semibold mb-1">QQ 邮箱授权码获取方式</p>
            <p className="text-blue-600">登录 QQ 邮箱 → 设置 → 账户 → 找到「POP3/IMAP/SMTP」服务 → 开启 SMTP 服务 → 生成授权码（16位）。将授权码填入下方即可。</p>
          </div>
        </div>
      </div>

      <div className="card p-6 lg:p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-semibold text-gray-800">邮箱配置</h3>
            <p className="text-sm text-gray-500 mt-1">已预填 QQ 邮箱默认参数，只需填写邮箱地址和授权码</p>
          </div>
          {/* 启用开关 */}
          <label className="flex items-center gap-2 cursor-pointer">
            <span className="text-sm text-gray-600">启用</span>
            <button
              onClick={() => handleChange('enabled', !account.enabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${account.enabled ? 'bg-green-500' : 'bg-gray-300'}`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${account.enabled ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </label>
        </div>

        {/* Basic Info */}
        <div className="mb-8">
          <h4 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-4">基本信息</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">发件邮箱 *</label>
              <input
                type="email"
                value={account.email}
                onChange={(e) => handleChange('email', e.target.value)}
                placeholder="your_qq@qq.com"
                className="input"
              />
              <p className="text-xs text-gray-400 mt-1">QQ 邮箱地址，同时作为 SMTP 登录用户名</p>
            </div>
            <div>
              <label className="label">发件人昵称</label>
              <input
                type="text"
                value={account.sender_name}
                onChange={(e) => handleChange('sender_name', e.target.value)}
                placeholder="AI Tech Digest"
                className="input"
              />
            </div>
          </div>
        </div>

        {/* SMTP Config */}
        <div className="mb-8">
          <h4 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-4">SMTP 配置（发信）</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">SMTP 主机</label>
              <input
                type="text"
                value={account.smtp_host}
                onChange={(e) => handleChange('smtp_host', e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="label">端口</label>
              <input
                type="number"
                value={account.smtp_port}
                onChange={(e) => handleChange('smtp_port', parseInt(e.target.value) || 0)}
                className="input"
              />
            </div>
            <div>
              <label className="label">加密方式</label>
              <select
                value={account.smtp_security}
                onChange={(e) => handleChange('smtp_security', e.target.value)}
                className="input"
              >
                <option value="ssl">SSL</option>
                <option value="starttls">STARTTLS</option>
                <option value="none">无加密</option>
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="label">SMTP 授权码 *</label>
              <input
                type="password"
                value={account.smtp_auth_code}
                onChange={(e) => handleChange('smtp_auth_code', e.target.value)}
                placeholder={account.has_smtp_auth_code ? `已保存（${account.smtp_auth_code_masked || '********'}），留空不修改` : '请输入 QQ 邮箱授权码（16位）'}
                className="input"
              />
              {account.has_smtp_auth_code && (
                <p className="text-xs text-green-600 mt-1">✓ 授权码已加密保存，当前显示：{account.smtp_auth_code_masked}</p>
              )}
            </div>
          </div>
        </div>

        {/* IMAP Config */}
        <div className="mb-8">
          <h4 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-4">IMAP 配置（收信，可选）</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">IMAP 主机</label>
              <input
                type="text"
                value={account.imap_host}
                onChange={(e) => handleChange('imap_host', e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="label">端口</label>
              <input
                type="number"
                value={account.imap_port}
                onChange={(e) => handleChange('imap_port', parseInt(e.target.value) || 0)}
                className="input"
              />
            </div>
            <div>
              <label className="label">加密方式</label>
              <select
                value={account.imap_security}
                onChange={(e) => handleChange('imap_security', e.target.value)}
                className="input"
              >
                <option value="ssl">SSL</option>
                <option value="starttls">STARTTLS</option>
                <option value="none">无加密</option>
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="label">IMAP 授权码</label>
              <input
                type="password"
                value={account.imap_auth_code}
                onChange={(e) => handleChange('imap_auth_code', e.target.value)}
                placeholder={account.has_imap_auth_code ? `已保存（${account.imap_auth_code_masked || '********'}），留空不修改` : '与 SMTP 授权码相同，可留空'}
                className="input"
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-3 pt-4 border-t border-gray-100">
          <button onClick={handleSave} disabled={saving} className="btn-primary">
            {saving ? '保存中...' : '保存配置'}
          </button>
          <button onClick={handleTestSmtp} disabled={testingSmtp || !account.id} className="btn-secondary">
            {testingSmtp ? '测试中...' : '🔗 测试 SMTP 连接'}
          </button>
          <button onClick={handleSendTest} disabled={sendingTest || !account.id} className="btn-success">
            {sendingTest ? '发送中...' : '✉️ 发送测试邮件'}
          </button>
        </div>
      </div>
    </div>
  )
}
