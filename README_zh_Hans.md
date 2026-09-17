# Glasser

**作者：** glasser-ai
**版本：** 0.1.0
**类型：** tool

[English](README.md)

用**一个 Glasser Key** 在 Dify 的 Agent 和 Workflow 里调用付费第三方 API 端点：搜索数据源、查看精确价格、执行、按次付费。不需要在每个供应商处注册。

Glasser 是一个经纪层。它以单个 Key 出售可执行的第三方 API 操作（endpoint）。你的 Agent 搜索目录，查看端点的契约和价格，然后执行。返回的是 provider 的原始输出，附带精确扣费和 Glasser 控制台里这次 run 的链接。

## 工具

插件暴露的七个动词与 Glasser 的 MCP 服务器和 CLI 完全相同。端点本身永远不是工具：目录是数据，运行时用 `search` 找到。

| 工具 | 作用 |
|---|---|
| **search** | 按关键词搜索数据源。每条结果带 provider、endpoint、价格、运行模式和相关性分数，分页。 |
| **inspect** | 一个端点的执行契约：provider 原生输入 schema、含全部计费条款的精确价格、端点版本、运行模式、超时。 |
| **run** | 执行一个端点，按公布的价格从 Workspace 扣费。返回 run：provider 输出、精确扣费、run URL。可选等待异步端点结束。 |
| **runs_get** | 按 id 取一个 run，可选等待到终态。 |
| **runs_list** | Workspace 的 runs，按时间倒序，可按状态、provider、endpoint 过滤。 |
| **runs_stop** | 请求停止一个进行中的 run。 |
| **balance** | 余额、预留、可用额度（美元）。也是最便宜的 Key 有效性检查。 |

### Agent 的标准流程

1. 用自然语言描述能力调用 `search`（如 "enrich a company by domain"、"domain rating"）。
2. `inspect` 选中的端点。执行前先读价格和计费条款。
3. 按 inspect 返回的 `input_schema` 构造输入，带上 inspect 给出的 `endpoint_version`，调用 `run`。
4. 汇报 run 状态、provider 的回答、扣费和 run URL。

### 示例提示词

- "example.com 的 Ahrefs 域名评分是多少？"
- "找到 jane@example.com 的 LinkedIn 资料和当前雇主。"
- "查 'best CRM for startups' 在德国的 Google 前 10 条结果。"
- "按域名补全 50 家公司要花多少钱？先 inspect，不要 run。"

## 安装

1. **创建 Glasser Key。** 登录 https://app.glasser.ai，打开 **Keys**，创建一个 Key（以 `gl_` 开头）。Workspace 需要有余额：run 是预付费、按次扣费。
2. **在 Dify 安装本插件**，在 Provider 设置里粘贴 Key。校验只调用免费的 `GET /v1/balance`。
3. **把工具挂到 Agent 应用**，或者作为节点加进 Workflow。七个工具共用同一个凭据。

### 网络要求

插件只向 **`api.glasser.ai`** 发出 HTTPS（443 端口）请求。没有其它主机，没有入站连接，没有遥测。运行在 Dify 标准插件运行时，使用默认权限（不需要 storage、model、endpoint 权限）。

## 使用说明

- **首次执行前先 inspect。** inspect 显示的价格是一次正常 COMPLETED 调用的费用。计费条款列出例外，例如 `NO_RESULT $0.00` 表示空结果免费。计费规则可能读取输入里的数量参数（`num`、`size`、`limit`、查询数组），所以从小量开始。
- **两个指标，不是一个。** run 的状态和 provider 的回答是两回事。provider 回 404（"person not found"）的 COMPLETED run 是正常结果，按端点条款计费。条款允许时，FAILED 的 run 也可能有非零扣费。
- **重试绝不重复扣费。** 每个 run 都带幂等键。你可以传自己的 UUID，或者让插件生成，结果里以 `idempotency_key` 回显。超时后用同一个键重试，返回的是原来的 run。插件自己重试断开的连接时也复用这个键。
- **异步端点。** `inspect` 会显示运行模式。同步端点在同一次调用里返回完成的 run。异步端点默认等待（超时可配置，默认 180 秒），超时则按当前状态返回，用 `runs_get` 继续轮询。
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
| `STOPPED` | 终态。派发前被停止，扣费为 0。已发给 provider 的 run 会正常完成并扣费 |

## 隐私

工具输入（查询、provider 和 endpoint 名称、run 输入、run id）和 Key 会发送到 `api.glasser.ai` 以完成每次请求。插件不存储任何数据，不收集遥测。请求在 `User-Agent` 头里标明插件名称和版本。详见 [PRIVACY.md](PRIVACY.md)。

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
