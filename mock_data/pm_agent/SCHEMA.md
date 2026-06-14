# PM OS Demo 数据契约（SCHEMA）

> **这是 demo 的唯一数据源目录。** 后端所有功能（四面板、分析、证据、自治监控、Ask PM OS）都从这里读。
>
> **剧本是两套数据 + 一个触发开关：**
> - `peacetime/` —— **平时**：日常收到的邮件、Jira、PR、Slack、日历、任务。**始终加载。**
> - `emergency/` —— **紧急情况**：被触发后才**叠加**进来的新记录（突发 P0、客户升级邮件…），模拟"日常中突然出事"。
> - 触发开关 `trigger_emergency.sh`（或 API）控制 emergency 是否生效。
>
> 实时数据 = `peacetime` ∪（触发后才加上 `emergency`）。一关掉就恢复平时。

---

## 0. 目录布局

```
mock_data/pm_agent/
├── peacetime/        ← 队友把【平时】数据放这里（6 个文件）
│   ├── jira.json
│   ├── github.json
│   ├── emails.json
│   ├── slack.json
│   ├── calendar.json
│   └── tasks.json
├── emergency/        ← 队友把【紧急情况新增的】数据放这里（同样 6 个文件，结构相同）
│   ├── jira.json     (只放紧急时新冒出来的记录，如一个新的 P0)
│   ├── github.json
│   ├── emails.json   (升级邮件)
│   ├── slack.json
│   ├── calendar.json
│   └── tasks.json
├── docs/             ← RAG 知识库（*.md：launch plan / strategy / metrics …），平时紧急共用
├── SCHEMA.md         ← 本文件
└── .emergency_active ← 触发状态标记（由脚本/ API 管理，别手动碰）
```

> **emergency/ 里只放"紧急时新增/变化"的记录，不要重复 peacetime 的内容**——它是叠加，不是替换。
> 例如平时 Jira 没有 P0；触发后 `emergency/jira.json` 放一条 `priority:"P0"` 的新单，AI 立刻就检测到。

切换整套数据集：设环境变量 `PM_DATA_DIR=/path/to/another/dir`（见根目录 `env.sh`）。
完整可运行的单套范例见 `mock_data/pm_os/`（扁平布局，无 peacetime/emergency，仅作字段参考）。

---

## 1. 触发开关（demo 的高潮时刻）

```bash
cd ~/hack
./trigger_emergency.sh on       # 🚨 注入紧急情况 + 让 AI 立刻扫描
./trigger_emergency.sh off      # ✅ 恢复平时
./trigger_emergency.sh status   # 查看当前状态
```
也可走 API（前端按钮可调）：
```bash
curl -s -X POST localhost:8100/api/pm/autonomy/emergency -H 'Content-Type: application/json' -d '{"active":true}'
curl -s     localhost:8100/api/pm/autonomy/emergency      # 查询状态
```

触发后：emergency 记录合并进实时数据 → 自治监控下一次扫描（≤20s，触发时会立即扫一次）发现新的
P0 / 升级 → Decision 翻转、风险卡更新、Ask PM OS 给出基于证据的可靠建议。**全程无需重启。**

---

## 2. 决策引擎怎么读你的数据（关键）

Go/No-Go 是**确定性算出来的**，所以你能用数据**精确编排结论**。四条 criteria，任一 FAIL → `decision = NO`：

| Criterion | 何时 FAIL | 引擎看的字段 |
|---|---|---|
| Zero open P0 bugs | 有 `priority="P0"` 且 `status` ∉ {Done, Closed} 的 jira | `jira.priority`, `jira.status` |
| QA sign-off complete | 日历无标题含 "QA" 的事件 **或** "QA sign-off" 任务未 done | `calendar.title`, `tasks.title`+`tasks.status` |
| All launch PRs merged | 有 `blocking_launch=true` 且 `status≠"merged"` 的 PR | `github.blocking_launch`, `github.status` |
| Stakeholder comms sent | 含 "stakeholder" 的任务未 done | `tasks.title`+`tasks.status` |

风险卡 / Top Actions 还用到：升级邮件（`emails.escalation=true`）、未评审的阻塞 PR（`approvals` 为空）。

**剧本建议**：让 peacetime 处于"基本健康"（decision 接近 YES 或只有轻微项），把真正的爆点
（新 P0、升级邮件、阻塞 PR）放进 `emergency/`，这样触发前后对比最强烈。

---

## 3. 各文件字段契约 + 范例（peacetime/ 和 emergency/ 结构完全相同）

复制改写即可。`*` = 引擎依赖字段。

### jira.json → `{"issues": [ ... ]}`
```json
{ "id": "CHK-101", "title": "Checkout fails for Amex cards (HTTP 500)",
  "priority": "P0", "status": "Open", "component": "payments" }
```
`id*` `title*`；`priority*` = `P0|P1|P2|P3`（P0 阻塞）；`status*` = `Open|In Progress|In Review|Done|Closed`；`component` 可选。

### github.json → `{"pull_requests": [ ... ]}`
```json
{ "number": 88, "title": "Enterprise Checkout v2 flow", "status": "open",
  "blocking_launch": true, "approvals": [], "days_open": 5,
  "requested_reviewers": ["raj@meridian.com"], "linked_jira": ["CHK-110"] }
```
`number*` `title*`；`status*` = `open|merged`；`blocking_launch*` 布尔；`approvals*` 数组（**空=未评审**）；其余可选。

### emails.json → `{"messages": [ ... ]}`
```json
{ "id": "EM-2001", "subject": "RE: Checkout still failing for our team",
  "from": "ops@globex.com", "account": "Globex", "escalation": true,
  "thread_id": "TH-77", "links": { "jira": ["CHK-101"] } }
```
`id*` `subject*` `from*`；`escalation*` 布尔（**true=客户升级**）；`account`/`thread_id`/`links` 可选。

### slack.json → `{"messages": [ ... ]}`
```json
{ "id": "SL-1", "channel": "#launch", "from": "sarah",
  "text": "QA pass is not scheduled yet.", "ts": "2026-06-14T09:00:00" }
```
自由格式（引擎不直接判定，用于检索/展示）；建议含 `id` `from` `text`。

### calendar.json → `{"events": [ ... ]}`
```json
{ "id": "EV-1", "title": "Enterprise Checkout — Launch Go/No-Go", "type": "review", "date": "2026-06-18" }
```
`id*` `title*`（**标题含 "QA" = QA 评审已排期**）；`type`/`date` 可选。

### tasks.json → `{"tasks": [ ... ]}`
```json
{ "id": "TASK-2", "title": "QA sign-off on Enterprise Checkout", "status": "not_started" }
```
`id*` `title*`；`status*` = `not_started|in_progress|blocked|done`；标题含 "QA sign-off" / "stakeholder" 被引擎按关键词识别。

---

## 4. RAG 知识库（docs/）

改了 `docs/*.md` 后重建索引：
```bash
cd ~/hack && source env.sh
RAG_DOCS_DIR=mock_data/pm_agent/docs RAG_INDEX_OUT=rag_pm.faiss RAG_CHUNKS_OUT=rag_pm_chunks.json python build_index.py
```

---

## 5. 自检

```bash
# 平时
./trigger_emergency.sh off
curl -s -X POST localhost:8100/api/pm/analysis | python3 -c "import sys,json;d=json.load(sys.stdin);print('peacetime decision:',d['ship_readiness']['decision'],'risks:',len(d['risks']))"
# 紧急
./trigger_emergency.sh on
curl -s -X POST localhost:8100/api/pm/analysis | python3 -c "import sys,json;d=json.load(sys.stdin);print('EMERGENCY decision:',d['ship_readiness']['decision'],'risks:',len(d['risks']))"
```
确认 peacetime 与 emergency 两种状态下的 `decision` / `risks` 符合你的剧本预期。

> 注意：6 个文件都为空时 `decision = NO`（"无 QA 排期"+"无 stakeholder 任务"按缺失判 FAIL）。
> 想要平时是干净的 YES，需要：无 open P0、无未合并 blocking PR、有标题含 "QA" 的日历事件且
> "QA sign-off" 任务 done、"stakeholder" 任务 done。
