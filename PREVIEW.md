# PREVIEW.md — 现场对照清单

> 在 GB10 上拉起后,用这份逐项核对前端是否**真的连上了本地引擎**(而不是兜底假数据)。
> 配套:[`START_HERE.md`](START_HERE.md)(运行)、[`FRONTEND.md`](FRONTEND.md)(API 契约)。

---

## 0. 启动(GB10)

```bash
# 1. 拉最新 main
git checkout main && git pull
git log --oneline -5        # 应能看到 "wire PM OS dashboard to /api/pm/*" 等接线提交

# 2. 后端:模型 :8000 → 工具 :8088 + PM API :8100
cd ~/hack && source env.sh
sg docker -c 'bash ~/hack/dock.sh vllm30'        # Nemotron 30B FP8
bash serve.sh

# 3. 健康检查(全绿再开前端)
curl -s http://localhost:8100/health             # {"status":"ok","vllm":true,"mock":true}
curl -s -X POST http://localhost:8100/api/pm/analysis | head -c 300   # 应有 ship_readiness/...

# 4. 前端,指向后端
VITE_API_URL=http://localhost:8100 ./web.sh      # 同机
# 别的设备:VITE_API_URL=http://<GB10_LAN_IP>:8100 ./web.sh   (GB10 IP: hostname -I)
# 打开 http://localhost:5173
```

> `./web.sh` 默认读 `env.sh` 的 `VITE_API_URL`;前面加 `VITE_API_URL=...` 即可覆盖。

---

## 1. 一眼判断:live 还是兜底

| 检查点 | 离线兜底(后端没通) | ✅ GB10 live(期望) |
|---|---|---|
| 顶栏状态 | 灰点 **"Offline — mock data"** | 🟢 **"Agent connected"** |
| ① 面板角标 | **"Demo data"** | 无 "Demo data" 角标 |
| ④ 证据来源 | 可能出现旧的 VPN-503 / PTO | 只有 CHK-101/102、PR-88、Globex… |

**只要顶栏是绿点 "Agent connected" 且 ① 没有 "Demo data" 角标 → 已连真引擎。**

---

## 2. 四个面板期望内容(live)

数据来自 `mock_data/pm_os/*`,结论由 GB10 现算。

### ① Executive Decision
- **Headline**:`Enterprise Checkout launch is AT RISK`
- **Ship Readiness**:**NO**(红)
- **Recommendation**:`Delay launch from 2026-06-19 to 2026-06-23`
- **Risk Level**:**Critical**(红)
- **Summary**:一段 **Nemotron 现写**的 executive 叙述 —— *每次运行措辞会略变,这正是"活的"证据*
- **Based on**:`Jira + GitHub + Email + Calendar + Tasks + Docs`

### ② Top 3 Actions
- 三张卡:`Schedule checkout QA review` / `Request review on PR-88` / `Reply to Globex escalation`,各带 Impact·Effort
- 点 **Generate draft** → 弹窗是 **Nemotron 当场写的草稿**:
  - QA / PR → Slack 体(含 @-mention、bullet)
  - Globex → 邮件体(含 `Subject:`,自动拆成标题/正文)
  - 可一键 **Copy to clipboard**
- 与兜底区别:文字是模型生成的、更自然,不是写死的

### ③ Ask PM OS
- 点建议问题 `Can we ship Friday?`
- 先闪 trace:`retrieve_evidence → search_docs → state_snapshot`
- 然后**逐字流式**吐答案,引用 `CHK-101 / CHK-102 / PR-88 / Globex`,给出延期结论
- 与兜底区别:兜底是静态一句话,live 是证据接地 + 流式

### ④ Evidence Drawer
- 真·交叉链卡片:
  - `CHK-101 — Amex checkout failure`
  - `CHK-102 — Double-charge on payment retry`
  - `PR-88 — Enterprise Checkout launch PR (unreviewed)`
  - `EM-2001 — Globex escalation`
  - `GAP — No 'Checkout QA Review' scheduled`
  - `TASK-4 — Send stakeholder launch update`
- 可按 **Jira / GitHub / Email / Calendar / Tasks** 筛选;点开看 `Why it matters + Mitigation`
- **绝不该出现 VPN-503 / PTO** —— 出现 = 没拉到新代码

---

## 3. 排错速查

| 症状 | 原因 | 处理 |
|---|---|---|
| 顶栏一直灰 "Offline" | `:8100` 没通 | 看 `serve.sh` 终端;`curl :8100/health` |
| ①②④有数据,③问答/草稿报错或极慢 | vLLM(`:8000`)没起/加载中 | `/health` 看 `vllm`;等模型加载完 |
| ①②④正常但叙述是固定句、③不可用 | vLLM 没起,但确定性事实不依赖模型 | 属预期降级;起 vLLM 后恢复 |
| 证据抽屉出现 VPN/PTO | 跑的是旧代码 | `git pull` 拉最新 main,确认 demoData 已是 CHK-101 故事 |
| 跨设备打不开 | IP/CORS | 用 `hostname -I` 的 IP;后端已开 CORS `*` |

> 关键设计:**即使 vLLM 没起,①②④ 仍会显示**(Go/No-Go、风险、行动是确定性算的),只有 executive 叙述走 fallback、③问答和草稿生成不可用。所以现场 vLLM 万一抽风,主面板照样能讲故事。
