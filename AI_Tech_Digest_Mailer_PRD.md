# PRD：AI 前沿信息汇总与邮件发送器

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| 产品名称 | AI Tech Digest Mailer |
| 产品类型 | 自托管 AI 信息简报系统 |
| 目标用户 | 个人开发者、技术管理者、AI 从业者、研究人员 |
| 核心场景 | 自动采集前沿技术资讯，经 LLM 总结整理后，通过 QQ 邮箱定时发送日报 |
| 当前版本 | MVP v1.0 |
| 文档版本 | v1.0 |
| 主要模块 | 信息采集、LLM 总结、邮件发送、Admin 后台、任务调度、存储管理 |

---

## 2. 产品背景

当前 AI、开源、云计算、开发者工具等领域信息更新极快，信息来源分散，包括：

- OpenAI、Anthropic、Google DeepMind 等厂商动态
- GitHub Trending
- Hacker News、Reddit、V2EX 等技术社区
- RSS 博客
- 技术媒体
- 论文平台
- 开源项目 Release

用户每天需要花费大量时间筛选、阅读和判断信息价值。

本产品希望通过自动化方式完成：

```text
信息采集 → 清洗去重 → LLM 总结 → 邮件排版 → 定时发送
```

最终每天生成一封结构清晰、适合阅读的中文技术简报邮件。

---

## 3. 产品目标

### 3.1 核心目标

构建一个自托管系统，每日自动从配置好的信源中采集信息，调用 LLM 进行总结、分类、重要性排序和格式美化，最后通过 QQ 邮箱 SMTP 定时发送给指定收件人。

### 3.2 MVP 目标

MVP 阶段重点实现：

1. Admin 登录
2. QQ 邮箱 SMTP 授权码配置
3. 收件人配置
4. LLM 模型配置
5. RSS 信源配置
6. GitHub Trending 配置
7. 每日定时采集
8. LLM 生成日报
9. HTML 邮件发送
10. 日志查看
11. 手动触发测试

### 3.3 非目标

MVP 阶段暂不重点实现：

1. 多租户 SaaS
2. 复杂权限体系
3. 浏览器插件
4. 移动端 App
5. IMAP 自动解析用户回复
6. 复杂爬虫集群
7. 商业化订阅计费
8. 大规模群发营销能力

---

## 4. 用户画像

### 4.1 个人 AI 开发者

特点：

- 关注 AI 模型动态
- 关注 GitHub 新项目
- 关注 Agent、RAG、MCP、LLM 应用工程
- 希望每天快速了解技术趋势

核心诉求：

- 不想每天刷多个网站
- 想收到中文总结
- 想知道哪些内容真正值得关注

### 4.2 技术负责人 / CTO

特点：

- 关注技术趋势和产业动态
- 需要快速判断某些技术是否值得团队跟进
- 时间有限

核心诉求：

- 每天看一封邮件即可了解重点
- 内容需要简洁、有判断、有优先级
- 希望区分技术动态、产品动态、开源动态

### 4.3 研究人员 / 学生

特点：

- 关注 AI 模型、论文、开源项目
- 需要持续跟踪研究方向
- 偏好结构化信息

核心诉求：

- 自动收集论文、博客、GitHub 项目
- 需要摘要和推荐理由
- 希望保存历史记录用于回顾

---

## 5. 核心使用流程

### 5.1 初次配置流程

```text
用户访问 Admin 后台
  ↓
登录系统
  ↓
配置 QQ 邮箱 SMTP 授权码
  ↓
配置收件人邮箱
  ↓
配置 LLM 模型
  ↓
添加 RSS / GitHub / 社区信源
  ↓
配置邮件模板和发送时间
  ↓
点击测试采集
  ↓
点击测试生成日报
  ↓
点击发送测试邮件
  ↓
启用每日定时任务
```

### 5.2 每日自动任务流程

```text
到达设定时间
  ↓
任务调度器触发采集任务
  ↓
从所有启用信源抓取新内容
  ↓
清洗、去重、过滤
  ↓
根据关键词和权重进行初步排序
  ↓
将候选内容发送给 LLM
  ↓
LLM 返回结构化日报 JSON
  ↓
后端使用模板渲染 HTML 邮件
  ↓
通过 QQ SMTP 发送邮件
  ↓
写入任务日志和邮件日志
```

---

## 6. 功能需求

### 6.1 Admin 登录模块

#### 功能说明

用于保护后台配置页面，防止未授权访问。

#### 功能点

- 管理员登录
- 管理员登出
- 修改密码
- 登录状态保持
- Token 过期处理

#### 字段

```text
用户名
密码
登录时间
最后一次登录 IP
账户状态
```

#### 规则

1. 系统初始化时生成默认管理员账户。
2. 首次登录后提示修改默认密码。
3. 密码必须哈希存储。
4. 后台接口必须校验登录状态。
5. 登录失败次数过多应进行短时间限制。

---

### 6.2 Dashboard 总览模块

#### 功能说明

展示系统运行状态和今日关键数据。

#### 页面内容

```text
今日采集数量
今日有效资讯数量
今日已处理数量
今日邮件发送状态
最近一次任务执行时间
最近一次错误信息
启用信源数量
启用收件人数量
默认模型状态
SMTP 状态
```

#### 快捷操作

```text
立即采集
立即生成日报
立即发送测试邮件
查看任务日志
查看邮件预览
```

---

### 6.3 QQ 邮箱配置模块

#### 功能说明

配置 QQ 邮箱 SMTP / IMAP 授权码，用于邮件发送，后续可扩展 IMAP 读取能力。

MVP 阶段主要使用 SMTP。

#### 字段设计

```text
发件邮箱
发送人昵称
SMTP 服务器
SMTP 端口
SMTP 加密方式
SMTP 授权码
IMAP 服务器
IMAP 端口
IMAP 加密方式
IMAP 授权码
是否启用
创建时间
更新时间
```

#### 默认配置

```text
SMTP Host: smtp.qq.com
SMTP SSL Port: 465
SMTP STARTTLS Port: 587

IMAP Host: imap.qq.com
IMAP SSL Port: 993
```

#### 安全要求

1. 授权码必须加密存储。
2. 前端不能回显完整授权码。
3. 只显示掩码，例如：

```text
********abcd
```

4. 日志中不得打印授权码。
5. 配置导出时默认不包含授权码。
6. 更新授权码时前端需要二次输入，不允许从后端读取原值。

#### 功能操作

```text
保存配置
测试 SMTP 连接
发送测试邮件
测试 IMAP 连接
启用 / 禁用邮箱配置
```

#### 验收标准

- 正确配置授权码后，可以成功发送测试邮件。
- 错误授权码时，页面展示明确错误原因。
- 授权码在数据库中不是明文。
- 前端永远不展示完整授权码。

---

### 6.4 收件人配置模块

#### 功能说明

管理日报邮件的接收对象。

#### 字段设计

```text
收件人名称
收件人邮箱
是否启用
接收类型
订阅主题
发送频率
备注
创建时间
更新时间
```

#### 接收类型

```text
To
CC
BCC
```

#### 发送频率

```text
daily
weekly
manual
```

MVP 阶段必须支持：

```text
daily
manual
```

#### 订阅主题

可配置：

```text
AI
LLM
Agent
RAG
MCP
GitHub
DevTools
Cloud
Security
Research
Startup
```

#### 功能操作

```text
新增收件人
编辑收件人
删除收件人
启用 / 禁用收件人
发送测试邮件给该收件人
```

#### 验收标准

- 可以新增多个收件人。
- 可以对单个收件人启用或禁用。
- 禁用的收件人不会收到自动日报。
- 邮箱格式校验有效。

---

### 6.5 LLM 模型配置模块

#### 功能说明

配置用于生成日报的 LLM 模型。

MVP 模型适配范围限定为：

1. OpenAI-compatible Completion 接口
2. OpenAI-compatible Responses 接口
3. Anthropic Messages 接口

不在 MVP 中优先支持：

```text
Gemini 原生接口
Ollama 原生接口
Azure OpenAI 专用接口
LangChain 多 Provider
复杂模型路由
多 Agent 工作流
```

#### 6.5.1 模型供应商类型

系统内置三种接口类型：

```text
openai_completion
openai_responses
anthropic_messages
```

#### 6.5.2 通用字段

```text
配置名称
接口类型
API Base URL
API Key
模型名称
Temperature
Max Output Tokens
Timeout 秒数
重试次数
是否启用
是否默认
创建时间
更新时间
```

#### 6.5.3 OpenAI-compatible Completion 接口

##### 适用场景

适用于兼容 OpenAI Chat Completions 风格的模型服务，例如：

```text
/v1/chat/completions
```

很多第三方模型平台都兼容该接口格式。

##### 配置字段

```text
接口类型: openai_completion
Base URL
API Key
Model
Temperature
Max Tokens
Timeout
```

##### 请求抽象结构

```json
{
  "model": "model-name",
  "messages": [
    {
      "role": "system",
      "content": "你是一个专业技术资讯分析助手。"
    },
    {
      "role": "user",
      "content": "请根据以下资讯生成日报。"
    }
  ],
  "temperature": 0.3,
  "max_tokens": 4000
}
```

##### 返回解析

系统需要从返回结果中解析：

```text
choices[0].message.content
```

##### 注意

虽然用户口头可能会说 completion，但实际工程上建议兼容的是：

```text
Chat Completions
```

即：

```text
/v1/chat/completions
```

传统 text completions 接口不建议作为 MVP 优先项。

#### 6.5.4 OpenAI-compatible Responses 接口

##### 适用场景

适用于支持新格式 Responses API 的模型服务。

##### 配置字段

```text
接口类型: openai_responses
Base URL
API Key
Model
Temperature
Max Output Tokens
Timeout
```

##### 请求抽象结构

```json
{
  "model": "model-name",
  "input": [
    {
      "role": "system",
      "content": "你是一个专业技术资讯分析助手。"
    },
    {
      "role": "user",
      "content": "请根据以下资讯生成日报。"
    }
  ],
  "temperature": 0.3,
  "max_output_tokens": 4000
}
```

##### 返回解析

系统需要优先兼容：

```text
output_text
```

如目标服务未直接提供 `output_text`，则需要从 `output` 数组中提取文本内容。

##### 设计要求

后端需要统一封装为：

```text
LLMClient.generate_digest(input_items, config) -> DigestResult
```

无论底层是 Completion 还是 Responses，上层调用方式保持一致。

#### 6.5.5 Anthropic Messages 接口

##### 适用场景

适用于 Anthropic Claude 系列模型。

##### 配置字段

```text
接口类型: anthropic_messages
Base URL
API Key
Model
Temperature
Max Tokens
Anthropic Version
Timeout
```

##### 请求抽象结构

```json
{
  "model": "claude-model-name",
  "max_tokens": 4000,
  "temperature": 0.3,
  "system": "你是一个专业技术资讯分析助手。",
  "messages": [
    {
      "role": "user",
      "content": "请根据以下资讯生成日报。"
    }
  ]
}
```

##### 返回解析

系统需要从返回内容数组中解析文本：

```text
content[0].text
```

##### Header 要求

需要支持配置或默认使用：

```text
x-api-key
anthropic-version
content-type: application/json
```

默认版本可以设置为：

```text
2023-06-01
```

#### 6.5.6 模型测试功能

Admin 页面应提供“测试模型”按钮。

##### 测试输入

```text
请用一句话回复：模型连接正常。
```

##### 成功标准

模型返回可读文本即视为成功。

##### 失败展示

需要展示：

```text
HTTP 状态码
错误类型
错误摘要
是否超时
是否鉴权失败
```

但不能展示完整 API Key。

#### 6.5.7 模型调用策略

MVP 推荐策略：

```text
只允许一个默认模型
日报生成使用默认模型
失败后按配置重试
仍失败则任务标记失败
```

后续版本可扩展：

```text
备用模型
不同信源使用不同模型
长文本模型和短文本模型分离
自动降级
成本统计
```

---

### 6.6 信源配置模块

#### 功能说明

用于配置系统需要采集的信息来源。

#### MVP 支持信源

```text
RSS
GitHub Trending
网页链接型信源
Hacker News RSS
Arxiv RSS
```

其中 MVP 第一优先级：

```text
RSS
GitHub Trending
```

#### 6.6.1 信源通用字段

```text
信源名称
信源类型
URL
分类
语言
关键词包含
关键词排除
抓取频率
最大抓取数量
是否启用
是否抓取全文
是否交给 LLM
重要性权重
创建时间
更新时间
```

#### 6.6.2 信源类型

```text
rss
github_trending
web_page
hackernews_rss
arxiv_rss
custom_api
```

MVP 可以先实现：

```text
rss
github_trending
```

#### 6.6.3 RSS 信源

##### 字段

```text
RSS URL
分类
语言
最大条数
关键词过滤
是否抓取全文
是否启用
```

##### 示例信源

```text
OpenAI News
Anthropic News
Google DeepMind Blog
Microsoft AI Blog
GitHub Blog
Hugging Face Blog
Vercel Blog
Cloudflare Blog
InfoQ
机器之心
量子位
阮一峰科技爱好者周刊
```

##### 解析字段

```text
标题
链接
摘要
发布时间
作者
来源名称
原始内容
```

#### 6.6.4 GitHub Trending 信源

##### 字段

```text
编程语言
时间范围
关键词
最小 Stars
最大条数
是否启用
```

##### 时间范围

```text
daily
weekly
monthly
```

##### 关键词示例

```text
llm
agent
rag
mcp
ai
devtool
workflow
automation
coding
inference
```

##### 输出字段

```text
仓库名称
仓库地址
描述
语言
Stars
Forks
今日新增 Stars
作者
匹配关键词
```

#### 6.6.5 网页信源

MVP 可作为实验功能。

##### 字段

```text
页面 URL
列表选择器
标题选择器
链接选择器
摘要选择器
日期选择器
```

##### 注意

网页抓取存在不稳定性，MVP 不建议作为核心能力。

---

### 6.7 信息采集模块

#### 功能说明

负责根据信源配置抓取信息，并写入原始内容表。

#### 采集流程

```text
读取启用信源
  ↓
根据类型调用对应 Fetcher
  ↓
解析内容
  ↓
标准化字段
  ↓
生成内容 hash
  ↓
去重
  ↓
写入 raw_items
```

#### 去重规则

优先级：

```text
URL 完全相同
标题 + 来源相同
标题相似度较高
内容 hash 相同
```

MVP 可使用：

```text
url_hash
title_hash
```

#### 错误处理

单个信源失败不应导致整个任务失败。

每个信源要记录：

```text
开始时间
结束时间
抓取数量
新增数量
失败原因
HTTP 状态码
```

---

### 6.8 信息过滤与排序模块

#### 功能说明

在发送给 LLM 前，先做初步筛选，降低 token 消耗。

#### 过滤规则

保留符合以下条件的内容：

```text
发布时间在指定时间窗口内
命中包含关键词
未命中排除关键词
来源处于启用状态
未被处理过
```

#### 排序规则

综合分数：

```text
score = 来源权重 + 关键词分 + 新鲜度分 + GitHub 热度分
```

#### 推荐 MVP 规则

MVP 阶段可以简单实现：

```text
优先保留最新的内容
优先保留高权重信源
优先保留命中关键词的内容
每个分类限制最大条目数
```

---

### 6.9 LLM 日报生成模块

#### 功能说明

将过滤后的资讯交给 LLM，生成结构化日报内容。

#### 输入内容

每条输入内容包括：

```text
标题
来源
链接
摘要
发布时间
分类
关键词
权重
```

#### 输出格式

强制要求 LLM 输出 JSON。

```json
{
  "title": "AI 前沿日报｜2026-07-01",
  "summary": "今日重点关注模型动态、Agent 工程化和 GitHub 开源项目。",
  "sections": [
    {
      "name": "AI 模型动态",
      "items": [
        {
          "title": "示例标题",
          "summary": "简短总结。",
          "why_it_matters": "为什么值得关注。",
          "source": "OpenAI News",
          "url": "https://example.com",
          "importance": 5,
          "tags": ["AI", "LLM"]
        }
      ]
    }
  ]
}
```

#### 重要性等级

```text
1 = 普通
2 = 可读
3 = 值得关注
4 = 重要
5 = 今日重点
```

#### Prompt 要求

##### System Prompt

```text
你是一个专业的技术资讯分析助手，负责将多来源、杂乱的技术信息整理成一份适合技术人员阅读的中文日报。

要求：
1. 使用中文输出。
2. 不要机械翻译标题。
3. 合并重复或相似信息。
4. 优先保留 AI、LLM、Agent、RAG、MCP、开源项目、开发者工具、云计算相关内容。
5. 每条内容必须包含标题、摘要、为什么值得关注、来源、链接和重要性评分。
6. 不得编造输入中不存在的信息。
7. 如果原始信息不足，请标记为“信息有限”。
8. 输出必须是合法 JSON。
9. 不要输出 Markdown。
10. 不要输出 JSON 以外的解释性文字。
```

##### User Prompt

```text
以下是今天采集到的技术资讯，请生成中文技术日报。

资讯列表：
{{items}}

请严格按照以下 JSON 结构输出：

{
  "title": "",
  "summary": "",
  "sections": [
    {
      "name": "",
      "items": [
        {
          "title": "",
          "summary": "",
          "why_it_matters": "",
          "source": "",
          "url": "",
          "importance": 1,
          "tags": []
        }
      ]
    }
  ]
}
```

---

### 6.10 邮件模板模块

#### 功能说明

将 LLM 返回的结构化 JSON 渲染为 HTML 邮件。

#### 邮件结构

```text
邮件标题
今日摘要
今日重点
分类内容
GitHub Trending
延伸阅读
页脚
```

#### 邮件标题模板

支持变量：

```text
{{date}}
{{digest_title}}
{{top_topic}}
```

示例：

```text
{{date}} AI 前沿日报：{{top_topic}}
```

#### 邮件 HTML 要求

1. 支持移动端阅读。
2. 样式使用内联 CSS。
3. 不依赖外部 JS。
4. 不依赖远程字体。
5. 原文链接可点击。
6. 每条资讯展示来源。
7. 每条资讯展示重要性。
8. 内容过长时应限制长度。

#### 邮件内容示例结构

```html
<h2>AI 前沿日报｜2026-07-01</h2>

<p><strong>今日摘要：</strong>今日重点关注模型发布、Agent 工具链和 GitHub 热门项目。</p>

<h3>🔥 今日重点</h3>

<div>
  <h4>1. 示例标题</h4>
  <p>这里是摘要内容。</p>
  <p><strong>为什么值得关注：</strong>这里是推荐理由。</p>
  <p><strong>来源：</strong>OpenAI News</p>
  <p><a href="https://example.com">阅读原文</a></p>
</div>
```

---

### 6.11 邮件发送模块

#### 功能说明

通过 QQ 邮箱 SMTP 发送 HTML 日报邮件。

#### 发送流程

```text
读取默认邮箱配置
  ↓
读取启用收件人
  ↓
生成邮件标题
  ↓
渲染 HTML 正文
  ↓
通过 SMTP 发送
  ↓
记录发送日志
```

#### 支持能力

```text
HTML 邮件
多收件人
CC
BCC
发送测试邮件
发送失败重试
```

MVP 最低要求：

```text
HTML 邮件
To 收件人
发送日志
失败日志
```

#### 发送限制

为了防止误发：

```text
单次发送收件人数量限制
每日发送次数限制
测试邮件频率限制
失败重试次数限制
```

---

### 6.12 任务调度模块

#### 功能说明

负责每日定时执行采集、总结和发送任务。

#### 默认时间

```text
07:00 采集
07:10 清洗与过滤
07:20 LLM 生成日报
07:30 发送邮件
```

#### 可配置字段

```text
是否启用自动任务
时区
每日采集时间
每日发送时间
是否工作日发送
失败重试次数
失败重试间隔
```

默认时区：

```text
Asia/Shanghai
```

#### 手动任务

Admin 支持：

```text
立即采集
立即生成日报
立即发送日报
发送测试邮件
```

---

### 6.13 存储管理模块

#### 功能说明

管理系统采集的原始数据、处理后数据、邮件日志和任务日志。

#### 页面内容

```text
原始资讯列表
处理后资讯列表
日报任务列表
邮件发送日志
LLM 调用日志
信源抓取日志
```

#### 操作

```text
搜索
筛选
查看详情
删除单条数据
清理历史数据
导出配置
导入配置
数据库备份
```

#### 数据清理策略

可配置：

```text
保留 7 天
保留 30 天
保留 90 天
永久保留
```

MVP 默认：

```text
保留 30 天
```

---

## 7. 页面需求

### 7.1 页面结构

```text
/login
/admin/dashboard
/admin/mail
/admin/recipients
/admin/models
/admin/sources
/admin/storage
/admin/email-template
/admin/schedule
/admin/settings
```

### 7.2 Dashboard 页面

展示：

```text
今日采集数
今日处理数
今日发送状态
最近失败任务
启用信源数
启用模型状态
SMTP 状态
```

操作按钮：

```text
立即采集
生成日报
发送测试邮件
查看日志
```

### 7.3 邮箱配置页面

表单字段：

```text
发件邮箱
发送人昵称
SMTP Host
SMTP Port
SMTP 加密方式
SMTP 授权码
IMAP Host
IMAP Port
IMAP 授权码
是否启用
```

按钮：

```text
保存
测试 SMTP
测试 IMAP
发送测试邮件
```

### 7.4 收件人页面

功能：

```text
收件人列表
新增收件人
编辑收件人
删除收件人
启用 / 禁用
发送测试邮件
```

### 7.5 模型配置页面

功能：

```text
模型配置列表
新增模型
编辑模型
删除模型
设为默认
测试模型
```

接口类型下拉：

```text
OpenAI-compatible Chat Completions
OpenAI-compatible Responses
Anthropic Messages
```

### 7.6 信源配置页面

功能：

```text
信源列表
新增 RSS
新增 GitHub Trending
编辑信源
删除信源
启用 / 禁用
测试抓取
查看最近抓取结果
```

### 7.7 邮件模板页面

功能：

```text
邮件标题模板配置
邮件风格配置
HTML 模板编辑
预览邮件
发送预览邮件
```

### 7.8 任务调度页面

功能：

```text
启用 / 禁用自动任务
配置每日采集时间
配置每日发送时间
手动执行任务
查看任务历史
```

---

## 8. 数据库设计

### 8.1 admin_users

```text
id
username
password_hash
role
is_active
last_login_at
created_at
updated_at
```

### 8.2 mail_accounts

```text
id
email
sender_name
smtp_host
smtp_port
smtp_security
smtp_auth_code_encrypted
imap_host
imap_port
imap_security
imap_auth_code_encrypted
enabled
created_at
updated_at
```

### 8.3 recipients

```text
id
name
email
recipient_type
topics
frequency
enabled
remark
created_at
updated_at
```

### 8.4 model_configs

```text
id
name
provider_type
base_url
api_key_encrypted
model_name
temperature
max_output_tokens
timeout_seconds
retry_count
anthropic_version
enabled
is_default
created_at
updated_at
```

其中 `provider_type` 取值：

```text
openai_completion
openai_responses
anthropic_messages
```

### 8.5 sources

```text
id
name
source_type
url
category
language
include_keywords
exclude_keywords
fetch_interval
max_items
need_full_text
send_to_llm
weight
enabled
created_at
updated_at
```

### 8.6 raw_items

```text
id
source_id
title
url
author
summary
content
published_at
fetched_at
url_hash
title_hash
content_hash
status
created_at
updated_at
```

### 8.7 processed_items

```text
id
raw_item_id
digest_job_id
title
summary
why_it_matters
category
tags
importance
source_name
source_url
llm_model
created_at
updated_at
```

### 8.8 digest_jobs

```text
id
job_date
job_type
status
raw_count
filtered_count
processed_count
email_sent_count
started_at
finished_at
error_message
created_at
updated_at
```

状态：

```text
pending
running
success
failed
partial_success
```

### 8.9 digest_outputs

```text
id
digest_job_id
title
summary
json_content
html_content
text_content
created_at
updated_at
```

### 8.10 email_logs

```text
id
digest_job_id
recipient_id
recipient_email
subject
status
sent_at
error_message
created_at
updated_at
```

### 8.11 source_fetch_logs

```text
id
source_id
status
fetched_count
new_count
started_at
finished_at
error_message
created_at
```

### 8.12 llm_call_logs

```text
id
digest_job_id
model_config_id
provider_type
model_name
status
input_tokens
output_tokens
latency_ms
error_message
created_at
```

注意：

```text
不记录完整 Prompt
不记录 API Key
不记录敏感配置
```

---

## 9. API 设计

### 9.1 Auth

```text
POST /api/admin/auth/login
POST /api/admin/auth/logout
GET  /api/admin/auth/me
POST /api/admin/auth/change-password
```

### 9.2 Dashboard

```text
GET /api/admin/dashboard/summary
```

### 9.3 邮箱配置

```text
GET  /api/admin/mail-account
POST /api/admin/mail-account
PUT  /api/admin/mail-account/{id}
POST /api/admin/mail-account/{id}/test-smtp
POST /api/admin/mail-account/{id}/test-imap
POST /api/admin/mail-account/{id}/send-test
```

### 9.4 收件人配置

```text
GET    /api/admin/recipients
POST   /api/admin/recipients
GET    /api/admin/recipients/{id}
PUT    /api/admin/recipients/{id}
DELETE /api/admin/recipients/{id}
POST   /api/admin/recipients/{id}/send-test
```

### 9.5 模型配置

```text
GET    /api/admin/models
POST   /api/admin/models
GET    /api/admin/models/{id}
PUT    /api/admin/models/{id}
DELETE /api/admin/models/{id}
POST   /api/admin/models/{id}/test
POST   /api/admin/models/{id}/set-default
```

### 9.6 信源配置

```text
GET    /api/admin/sources
POST   /api/admin/sources
GET    /api/admin/sources/{id}
PUT    /api/admin/sources/{id}
DELETE /api/admin/sources/{id}
POST   /api/admin/sources/{id}/test-fetch
POST   /api/admin/sources/{id}/enable
POST   /api/admin/sources/{id}/disable
```

### 9.7 任务接口

```text
POST /api/admin/jobs/fetch-now
POST /api/admin/jobs/generate-digest
POST /api/admin/jobs/send-now
GET  /api/admin/jobs
GET  /api/admin/jobs/{id}
```

### 9.8 存储接口

```text
GET    /api/admin/raw-items
GET    /api/admin/processed-items
GET    /api/admin/email-logs
GET    /api/admin/llm-logs
DELETE /api/admin/storage/cleanup
POST   /api/admin/config/export
POST   /api/admin/config/import
```

### 9.9 邮件模板接口

```text
GET  /api/admin/email-template
PUT  /api/admin/email-template
POST /api/admin/email-template/preview
POST /api/admin/email-template/send-preview
```

---

## 10. 技术架构建议

### 10.1 推荐技术栈

#### 后端

```text
Python
FastAPI
SQLAlchemy
Pydantic
APScheduler
Jinja2
feedparser
httpx
BeautifulSoup
smtplib
imaplib
cryptography
```

#### 数据库

MVP：

```text
SQLite
```

进阶：

```text
PostgreSQL
```

#### 前端

```text
Next.js
React
Tailwind CSS
shadcn/ui
```

#### 部署

```text
Docker
Docker Compose
```

### 10.2 系统架构

```text
Admin Frontend
      ↓
FastAPI Backend
      ↓
Config Service
Source Fetcher
Digest Service
LLM Adapter
Mail Service
Scheduler
Storage Service
      ↓
SQLite / PostgreSQL
```

### 10.3 LLM Adapter 架构

建议设计统一接口：

```text
BaseLLMClient
  ├── OpenAICompletionClient
  ├── OpenAIResponsesClient
  └── AnthropicMessagesClient
```

统一输出：

```json
{
  "text": "",
  "raw_response": {},
  "model": "",
  "provider_type": "",
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0
  }
}
```

上层 Digest Service 不关心具体模型接口，只调用：

```text
generate(system_prompt, user_prompt, config)
```

---

## 11. 安全需求

### 11.1 密钥安全

必须加密存储：

```text
QQ SMTP 授权码
QQ IMAP 授权码
LLM API Key
```

### 11.2 日志安全

不能记录：

```text
明文授权码
明文 API Key
完整邮件认证信息
敏感 Header
```

### 11.3 Admin 安全

必须支持：

```text
登录鉴权
密码哈希
Token 过期
接口权限校验
登录失败限制
```

### 11.4 邮件安全

必须支持：

```text
发送频率限制
HTML 内容转义
收件人格式校验
测试发送确认
```

---

## 12. 异常处理

### 12.1 信源异常

场景：

```text
RSS 无法访问
RSS 格式错误
网页解析失败
GitHub Trending 抓取失败
网络超时
```

处理：

```text
记录日志
跳过该信源
继续执行其他信源
Dashboard 显示失败数量
```

### 12.2 LLM 异常

场景：

```text
API Key 错误
模型不存在
接口超时
返回非 JSON
Token 超限
内容被截断
```

处理：

```text
失败重试
重试仍失败则任务失败
保留原始输入
记录错误摘要
允许后台手动重试
```

### 12.3 邮件异常

场景：

```text
SMTP 授权失败
收件人邮箱错误
连接超时
发送频率过高
```

处理：

```text
记录失败日志
不影响日报内容保存
允许重新发送
```

---

## 13. 验收标准

### 13.1 基础验收

- 可以登录 Admin。
- 可以配置 QQ 邮箱 SMTP。
- 可以发送测试邮件。
- 可以配置至少一个收件人。
- 可以配置至少一个 LLM 模型。
- 可以配置 RSS 信源。
- 可以手动触发采集。
- 可以手动生成日报。
- 可以手动发送日报。

### 13.2 自动任务验收

- 系统能在设定时间自动采集。
- 系统能自动调用 LLM。
- 系统能生成 HTML 邮件。
- 系统能自动发送给启用收件人。
- 任务结果可在日志中追踪。

### 13.3 模型兼容验收

至少通过以下三类模型接口测试：

```text
OpenAI-compatible Chat Completions
OpenAI-compatible Responses
Anthropic Messages
```

每类接口需要验证：

```text
连接测试成功
日报生成成功
错误提示明确
API Key 不泄漏
```

### 13.4 安全验收

- 授权码不是明文存储。
- API Key 不是明文存储。
- 前端不回显完整密钥。
- 日志不打印敏感信息。
- 未登录不能访问后台接口。

---

## 14. MVP 开发拆解

### 第一阶段：系统基础

```text
项目初始化
数据库初始化
Admin 登录
基础布局
配置加密模块
```

### 第二阶段：配置模块

```text
邮箱配置
收件人配置
模型配置
信源配置
```

### 第三阶段：采集模块

```text
RSS 抓取
GitHub Trending 抓取
数据去重
采集日志
```

### 第四阶段：LLM 模块

```text
OpenAI Completion Adapter
OpenAI Responses Adapter
Anthropic Messages Adapter
Prompt 模板
JSON 解析与校验
```

### 第五阶段：邮件模块

```text
HTML 模板
邮件渲染
SMTP 发送
发送日志
测试邮件
```

### 第六阶段：任务调度

```text
APScheduler 集成
每日任务
手动任务
失败重试
任务日志
```

### 第七阶段：完善 Admin

```text
Dashboard
存储管理
邮件预览
任务日志
错误提示
```

---

## 15. 版本规划

### v1.0 MVP

```text
Admin 登录
QQ SMTP
收件人配置
模型配置
RSS
GitHub Trending
定时日报
HTML 邮件
日志
```

### v1.1

```text
网页信源
Hacker News
Arxiv
邮件模板编辑器
配置导入导出
```

### v1.2

```text
周报
多模型备用
失败自动降级
更细粒度主题订阅
```

### v2.0

```text
IMAP 回复解析
用户偏好学习
多用户系统
团队共享
网页阅读面板
```

---

## 16. 推荐 MVP 边界

为了快速落地，建议 MVP 严格控制范围。

必须做：

```text
SMTP 发送
RSS
GitHub Trending
三类模型接口
Admin 配置
日报生成
日志
```

暂缓做：

```text
复杂 IMAP 逻辑
复杂网页爬虫
多用户权限
模型成本统计
高级推荐算法
复杂模板市场
```

---

## 17. 最终产品定位

这个产品可以定位为：

> 一个自托管的 AI 技术前沿日报生成器，自动追踪 RSS、GitHub Trending、厂商动态和技术社区信息，调用兼容 OpenAI / Anthropic 的 LLM 接口生成中文技术简报，并通过 QQ 邮箱定时发送给用户。

MVP 最核心的一句话是：

> 每天早上自动给你发一封高质量中文 AI 技术日报。

---

## 18. 后续建议

建议下一步进入：

1. 数据库 ERD + SQLAlchemy Model 设计
2. FastAPI 后端模块骨架
3. LLM Adapter 详细接口设计
4. Admin 页面路由与组件拆解
5. Docker Compose 部署方案

优先建议先做：

> LLM Adapter 详细设计 + 数据库模型设计

因为这两个会决定后面代码的稳定性。
