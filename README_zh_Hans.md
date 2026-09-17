# Glasser

**作者：** glasser-ai
**版本：** 0.3.2
**类型：** tool

[English](README.md)

用**一个 Glasser Key** 给 Dify 的 Agent 和 Workflow 提供高级数据：找人、公司情报、SEO 研究、网页研究、社交研究，背后是 Apollo、People Data Labs、Hunter、BuiltWith、DataForSEO、Semrush、Ahrefs、Serper、Exa、ScrapeCreators 等。Agent 只说要什么数据，Glasser 决定由哪家 provider 提供。按次付费，不需要在每个供应商处注册。

Glasser 是一个经纪层。它以单个 Key 出售可执行的第三方 API 操作。每次工具调用就是一次 Glasser run；返回的是 provider 的原始输出，附带精确扣费和 Glasser 控制台里这次 run 的链接。

## 工具

五个业务级工具覆盖常见任务。每个工具接收 `action` 和 `provider`；`provider = auto`（默认）由插件为该操作选择合适的数据源，指定 provider 则强制使用它。Agent 只说要什么数据，不用知道该调哪家供应商。

| 工具 | Agent 能做什么 | 背后的数据源 |
|---|---|---|
| **找人** (`people_search`) | 按职位、级别、地区、雇主搜索人物；补全一个人；查找工作邮箱 | Apollo、People Data Labs、Hunter、Prospeo、LeadMagic、ZoomInfo |
| **公司情报** (`company_intelligence`) | 公司档案与画像、技术栈、网站流量、竞争对手、融资、新闻 | Apollo、PDL、Hunter、Prospeo、PredictLeads、LeadMagic、BuiltWith、DataForSEO、Ahrefs、Serpstat、Apify、Serper |
| **SEO 研究** (`seo_research`) | 关键词指标与拓展、域名自然流量概览、排名关键词、外链、引荐域名、域名评分、Google 结果 | Semrush、DataForSEO、Ahrefs、Serpstat、Serper |
| **网页研究** (`web_research`) | 网页、新闻、地点、学术、商品、图片、视频搜索；读取网页；语义搜索、问答、相似页面 | Serper、SerpApi、Exa、DataForSEO |
| **社交研究** (`social_research`) | Reddit、X、YouTube、TikTok、Instagram、LinkedIn：搜索帖子、读取主页和频道、查找社交账号 | ScrapeCreators、Apify、TikHub |

Glasser 目录里其余 1,400 多个端点可通过 Glasser 的 MCP 服务器（`https://api.glasser.ai/mcp`，Dify 可直接作为 MCP 工具添加）和 CLI 使用。

### 业务级调用如何工作

1. 工具通过路由表（`utils/routes.py`）把 `(action, provider)` 解析成一个 Glasser 端点，并把扁平参数转换成该端点的 provider 原生输入。
2. 执行该端点。结果就是 Glasser API 返回的 run（provider 输出、精确的 `charge_usd`、`run_url`），外加一个 `routed` 块，说明这次调用由哪个端点服务、收到了什么输入。
3. 路由、回退和定价由 Glasser 决定；插件不保存状态，除了断线时复用幂等键之外不做任何重试。

完整路由表见英文 README 的 Routing table 一节。

### 示例提示词

- "找 stripe.com 的 CTO。"（people_search，search，apollo：免费）
- "Patrick Collison 在 stripe.com 的工作邮箱是什么？"（people_search，find_email，hunter）
- "shopify.com 用了哪些技术？"（company_intelligence，tech_stack，builtwith）
- "'espresso machine' 在英国的搜索量和难度。"（seo_research，keyword_overview，semrush）
- "读取 https://example.com 并总结。"（web_research，scrape，serper）
- "这周 Reddit 上大家怎么说我们的品牌？"（social_research，reddit_search，scrapecreators）
- "用 Ahrefs 查" 会强制 `provider = ahrefs`。

## 安装

1. **创建 Glasser Key。** 登录 https://app.glasser.ai，打开 **Keys**，创建一个 Key（以 `gl_` 开头）。Workspace 需要有余额：run 是预付费、按次扣费。
2. **在 Dify 安装本插件**，在 Provider 设置里粘贴 Key。校验只调用免费的 `GET /v1/balance`。
3. **把工具挂到 Agent 应用**，或者作为节点加进 Workflow。七个工具共用同一个凭据。

### 网络要求

插件只向 **`api.glasser.ai`** 发出 HTTPS（443 端口）请求。没有其它主机，没有入站连接，没有遥测。运行在 Dify 标准插件运行时，使用默认权限（不需要 storage、model、endpoint 权限）。

## 使用说明

- **每次调用就是一次付费 run**，按路由到的端点的公布价格计费；结果里的 `routed` 块说明是哪个端点。`limit` 保持小量：计费规则可能读取它。
- **两个指标，不是一个。** run 的状态和 provider 的回答是两回事。provider 回 404（"person not found"）的 COMPLETED run 是正常结果，按端点条款计费。条款允许时，FAILED 的 run 也可能有非零扣费。
- **重试绝不重复扣费。** 每个 run 都带插件生成的幂等键（结果里以 `idempotency_key` 回显）；插件重试断开的连接时复用它，重试读到的是原来的 run。
- **异步端点**（Apify 路由）会等待最多 180 秒，超时则按当前状态和 run URL 返回。
- **金额是精确的小数字符串**（`"0.0005"`），不是浮点数。不要对 `charge_usd`、`balance_usd` 或价格做浮点运算。
- **限流。** `rate_limited` 错误带 `retry_after_ms`。插件等待这么久后重试同一调用一次；仍被限流则原样返回错误。
- **错误就是 API 自己的信封**：`{"error": {"code", "message", ...}, "request_id"}`。`insufficient_balance` 表示 Workspace 余额不足以覆盖价格，去控制台充值，不要重试。

## Run 状态

| 状态 | 含义 |
|---|---|
| `QUEUED` | 已受理，尚未派发给 provider |
| `RUNNING` | 已派发，provider 尚未回答 |
| `COMPLETED` | 终态。provider 已回答（回答本身仍可能是 "not found"） |
| `FAILED` | 终态。没有可用的 provider 回答；`failure` 字段说明原因 |
| `STOPPED` | 终态。在 Glasser 控制台派发前停止，扣费为 0 |

## 隐私

工具输入（查询、域名、姓名、邮箱、URL）和 Key 会发送到 `api.glasser.ai` 以完成每次请求。插件不存储任何数据，不收集遥测。请求在 `User-Agent` 头里标明插件名称和版本。详见 [PRIVACY.md](PRIVACY.md)。

## 开发

```sh
uv sync                      # Python 3.12、dify_plugin、pytest
uv run pytest                # 离线测试，不联网
dify plugin package .        # 生成 glasser.difypkg
```

对接 Dify 工作区远程调试：把 `.env.example` 复制为 `.env`，填入工作区插件页的 debug key，然后 `uv run python -m main`。

## 支持

- 源码仓库：https://github.com/glasser-ai/dify-glasser
- Glasser 文档：https://glasser.ai/docs
- 控制台：https://app.glasser.ai
- 联系：support@glasser.ai
