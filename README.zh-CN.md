# FlowPilot Arena

> 受治理的企业级 computer-use Agent 与可重置的合成 Arena。W16 将本地系统
> 封装为可复现、可审计的发布材料。

## 一分钟了解

FlowPilot 面向合成企业应用协调 Joiner/Mover/Leaver 流程。Agent 能够观察变化
页面、规划跨系统的类型化动作、从中断中恢复，并在高风险操作前停下来等待人工
审批；但 Agent 不是权威来源。Control Plane 负责身份、租户/RBAC、审批、审计、
队列/租约/栅栏和 receipt/idempotency，只有独立 Sandbox database-fact
Grader 决定业务成功。

受治理流程为：

observe -> plan -> execute -> recover -> verify

当前 Demo 使用合成数据和 deterministic fake provider。真实
provider/model/OCR/VLM/embedding 调用和真实成本严格为零。

## 系统架构

~~~mermaid
flowchart LR
  U["本地合成用户"] --> Web["Control Web"]
  Web --> API["Control API"]
  API --> ID["Keycloak + Control PostgreSQL"]
  API --> WF["私有 Workflow Worker"]
  WF --> T["Temporal + Recovery"]
  WF --> PA["Planning / DOM / Vision / Hybrid"]
  PA --> BW["隔离 Browser Worker"]
  BW --> SB["合成 Sandbox"]
  SB --> G["独立 database-fact Grader"]
  API --> TR["不透明 trace/replay"]
~~~

W1-W15 边界见 [docs/architecture.md](docs/architecture.md) 和
[docs/threat-model.md](docs/threat-model.md)。W16 Helm 只是封闭的、
namespace-scoped 部署封装，不是新的控制通路。

## 五分钟快速启动

依赖：Python 3.13、uv、Node.js 24/npm 和 Docker Compose。不需要云账号、镜像
仓库凭据或外部 Benchmark。

~~~powershell
$env:RECOVERY_ENVELOPE_KEY = '<runtime-only local key>'
docker compose -f deploy/compose/compose.yaml config
docker compose -f deploy/compose/compose.yaml up --build -d
docker compose -f deploy/compose/compose.yaml ps
docker compose -f deploy/compose/compose.yaml --profile acceptance run --build --rm acceptance-smoke
python tests/integration/w16_demo_smoke.py
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
Remove-Item Env:RECOVERY_ENVELOPE_KEY
~~~

其他 profile 覆盖 vision、hybrid planning、recovery、context、identity、
approval、production、observability、security 和 W15 Development-only
evaluation。上面的 Compose 体积清理是本地 reset，不会授权产品删除。API
健康端点为 /healthz，Web 健康端点为 /；trace/replay 和独立 Grader 由已有
smoke 覆盖。

## W16 材料

- W16 PR 45 已合并于 `d1b03993...`；单独授权的 closure 位于
  `codex/w16-release-closure`。
- Helm：[deploy/helm/flowpilot-arena](deploy/helm/flowpilot-arena)
- Private 候选镜像 workflow：
  [.github/workflows/release-images.yml](.github/workflows/release-images.yml)。
  它只接受 main 上精确的 40 位 commit，只发布四个 `linux/amd64`
  `sha-<commit>` 候选，生成 SBOM/Trivy/provenance 证据并执行 kind/Helm
  生命周期；不会创建 `latest` 或 `v1.0.0`。
- Demo：[docs/demo.md](docs/demo.md) 与
  [tests/integration/w16_demo.py](tests/integration/w16_demo.py)
- 架构：[docs/architecture.md](docs/architecture.md)
- Release Notes：[docs/release-notes-v1.0.0.md](docs/release-notes-v1.0.0.md)
- SBOM：[docs/sbom.spdx.json](docs/sbom.spdx.json) 与
  [docs/sbom-status.md](docs/sbom-status.md)
- 模型卡：[docs/model-card.md](docs/model-card.md)
- 贡献/安全/许可证：[CONTRIBUTING.md](CONTRIBUTING.md) ·
  [SECURITY.md](SECURITY.md) · [LICENSE](LICENSE)

W15 冻结的 synthetic Reporting 结果、矩阵、hash 和 WorkArena 状态见
[week-15-report](docs/evidence/week-15-report.md) 和
[benchmark-card](docs/benchmark-card.md)。三次重复不支持显著性、真实成本、
生产 SLO、ROI 或安全认证结论。

## Demo 媒体

GIF/视频必须来自真实的本地确定性运行并完成 Cookie、Bearer、nonce、DSN、
机器路径、个人数据、secret 和调试信息脱敏。本环境没有录屏工具，因此媒体
如实为 unavailable；[docs/demo.md](docs/demo.md) 提供带字幕的静态 fallback。
不使用 AI 生成画面冒充产品运行。

## 安全边界与已知限制

仓库仍为 Private，本 closure 不改变可见性。没有真实云部署、公共入口、生产身份、
生产 provider、任意浏览器/API/代码执行、物理删除、impersonation、delegation、
break-glass、外部 Benchmark 或生产认证。合成结果不是实际模型质量；WorkArena
因仓库没有版本化本地资产、许可材料和 checksum 而 unavailable。Helm 4.2.0 与
kind 0.32.0 在修复 NetworkPolicy 后已通过本地验证；完整的 registry digest/许可
SBOM、录屏、云部署和公开就绪仍为 unavailable。Trivy 在每个本地候选镜像中均
发现 HIGH/CRITICAL 项，因此公开可见性、`v1.0.0` 和 Release 均被阻断。

## 明确不支持的生产操作

不要用本发布材料修改真实 HR/IAM/ITSM/mail/asset 系统、处理薪酬或法律数据、
绕过审批、授予全局管理员、上传真实凭据、暴露服务入口，或把 Agent 完成状态、
Dashboard、Reporting、Helm、Demo 输出当成业务成功。

修改仓库前请先阅读 [W16 plan](docs/plans/week-16-release.md) 和
[W16 contract](docs/agent-contract.md)。授权的 closure 提交主题为
`chore: close W16 release verification`。只允许 closure PR/CI/squash merge 和
一次 Private 候选镜像 dispatch；不允许公开可见性、tag、Release 或云操作。
