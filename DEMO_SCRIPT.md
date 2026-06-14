# DEMO_SCRIPT — 现场固定演示脚本

> **为什么固定**：hackathon 评审现场即兴会翻车。本文件锁定 **3 个核心 demo + 2 个备用 demo**，每个标注期望行为、判定通过条件、失败时降级方案。
>
> 上场前每个连跑两遍稳定通过，才能上台。

---

## 演示哲学

1. **三个 demo 各打中一个能力维度**：RAG / Text-to-SQL / Tool calling
2. **Demo 1 是头牌**——多工具串联，最能体现 agent 自治
3. **顺序：先简单后复杂**——Demo 2（最稳）→ Demo 1（头牌）→ Demo 3（亮点）
4. **每个 < 30 秒**——评委时间有限
5. **每个有降级路径**——失败时不能空手而归

---

## 演示 1：跨能力自治 Agent（**头牌**）

### 用户输入

> "Hi, I'm Alice. My email is alice@meridian.com. My VPN is throwing error VPN-503 and I can't connect. Can you help?"

### 期望 agent 行为

```
[1] tool_call: lookup_employee(email="alice@meridian.com")
    → 返回: {employee_id: "E1001", name: "Alice Nguyen", department: "IT", ...}

[2] rag_search(query="VPN-503 error troubleshooting")
    → 命中 it_troubleshooting_guide.md 的 §1 VPN 段落 + §4 错误码表
    → "VPN-503 = Gateway saturated, switch to secondary gateway"

[3] 模型综合返回：
    "Hi Alice (E1001). VPN-503 means our primary VPN gateway is saturated.
     Try connecting to the secondary gateway at vpn-east.meridian.com.
     If that doesn't work in 5 minutes, I'll open a P2 ticket for you."

[4] (用户确认仍不通后)
    tool_call: create_ticket(
        requester_email="alice@meridian.com",
        category="network",
        priority="P2",
        summary="VPN-503 error - cannot connect via primary gateway",
        details="Tried secondary gateway, also failing. Employee verified as E1001."
    )
    → 返回: {ticket_id: "T-348291", status: "open", ...}

[5] 最终回复：
    "I've created ticket T-348291 (P2 priority). IT will reach out within 4 hours.
     In the meantime, you can try Office Wi-Fi as a workaround."
```

### 判定通过

- ✅ `tool_calls` 字段确实触发了（不是只在 content 里输出 JSON）
- ✅ `lookup_employee` 实际返回了 Alice 的记录
- ✅ RAG 命中包含 "VPN-503" 关键词的 chunk
- ✅ `create_ticket` 真的回了一个 ticket_id（不是模型瞎编的）
- ✅ 端到端 < 30 秒

### 失败降级

| 失败模式 | 立刻做 |
|---|---|
| `tool_calls` 字段空 | agent.py 的 `_try_parse_inline_tool` ReAct 兜底应已自动接管；看 console 是否触发 |
| RAG 返回空 | 改用关键词回答（直接 cat `it_troubleshooting_guide.md`，让模型解释）|
| 工具调用错对象 | 简化 prompt，告诉模型 "Step 1: verify identity. Step 2: search docs. Step 3: file ticket if needed." |
| 整个流程超 60 秒 | 切到 30B 主力（playbook L2）|

---

## 演示 2：Text-to-SQL（**最稳，先演这个建立信心**）

### 用户输入

> "What were our top 5 products by completed revenue in 2025? Show product name, category, and revenue."

### 期望 agent 行为

生成大致 SQL：

```sql
SELECT p.name, p.category,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM order_items oi
JOIN orders o   ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.status = 'completed'
  AND strftime('%Y', o.order_date) = '2025'
GROUP BY p.product_id
ORDER BY revenue DESC
LIMIT 5;
```

执行后返回结构化表格：

```
| name                  | category  | revenue    |
| --------------------- | --------- | ---------- |
| Meridian Fleet Pro    | Hardware  | 1,250,000  |
| Meridian Insight      | Software  | 980,500    |
| ...                                              |
```

### 判定通过

- ✅ SQL 实际能执行（不是只生成不跑）
- ✅ 表里有 5 行（除非数据不足 5 个产品类别）
- ✅ Revenue 是数字、单调递减
- ✅ `_extract_sql` 干净剥离了 `<think>` 和代码围栏
- ✅ 端到端 < 15 秒

### 失败降级

| 失败模式 | 立刻做 |
|---|---|
| SQL 报语法错 | 看模型完整输出（包括 `<think>`）；如果是 SQLite 不支持的方言，简化 prompt 强调 "SQLite syntax only" |
| 没 JOIN 进 products | system prompt 里把 schema 加更具体 example |
| 数字看着对但格式难看 | agent.py 里加一行 `pandas.DataFrame(rows, columns=columns).to_markdown()` |

### 备用问题（评委追问 / 同类型）

- **Q4: 月度营收趋势** "Show monthly revenue trend for the last 12 months. Is there a Q4 bump?"
- **Q5: CSAT 分析** "Average CSAT by ticket priority. Which priority has the worst customer satisfaction?"
- **Q6: 退款率** "Refund rate by region (refunded / total orders)."

---

## 演示 3：多轮工具调用（**亮点：上下文记忆 + 时间运算**）

### 用户输入（多轮）

**Turn 1**:
> "I want to take vacation from December 23rd through 27th this year."

**Turn 2**（agent 问 ID 后）:
> "My employee ID is E1001."

### 期望 agent 行为

```
Turn 1:
  agent: "I'd be happy to file that. What's your employee ID?"
  (不直接调工具，因为缺少 employee_id)

Turn 2:
  tool_call: request_pto(
      employee_id="E1001",
      start_date="2026-12-23",
      end_date="2026-12-27",
      note="(empty or auto-generated)"
  )
  → 返回: {request_id: "PTO-...", status: "submitted",
           approver_email: "diane@meridian.com", ...}

  agent: "Submitted! Request ID PTO-XXXXX. Your manager Diane Park
          (diane@meridian.com) will approve. Enjoy your time off."
```

### 判定通过

- ✅ Turn 1 agent 知道**还缺信息，不调工具**（防止 hallucination）
- ✅ Turn 2 agent 正确解析了"December 23rd through 27th"为 ISO 日期
- ✅ `request_pto` 真的被调了
- ✅ 回复里包含 ticket id 和 approver 邮箱

### 失败降级

| 失败模式 | 立刻做 |
|---|---|
| Turn 1 就硬调工具 | system prompt 加 "Don't call tools if required arguments are missing—ask the user instead." |
| 日期解析错（年份猜错） | 显式告诉它今年是 2026；或 prompt 里说 "Assume current year is 2026" |
| 中文输入混入 | 加一个 "Output language: same as input language" |

---

## 备用演示（评委追问时上）

### 备用 1：根因分析（incident_logs.csv 加分项）

> "Last Tuesday around 2 PM, we had a spike in support tickets. What might have caused it?"

期望 agent：
1. text-to-SQL 查 `support_tickets` 在 14:00-15:00 那段
2. 关联 `incident_logs.csv` 找同期的 system error
3. 总结："telemetry-ingest backed up → fleet-api 429 errors → users couldn't connect → tickets surged"

> ⚠️ 这个需要把 `incident_logs.csv` 接入 agent，**默认 agent.py 没接**。临时演时间够再加。

### 备用 2：安全事件（多类工具）

> "I think someone tried to log into my account from China. I'm Bob (bob@meridian.com)."

期望：
1. `lookup_employee(email="bob@meridian.com")`
2. RAG 找安全策略（"report within 1 hour"）
3. `create_ticket(category="security_incident", priority="P1", ...)`
4. `reset_password(employee_id="E1002")`

---

## 演示日时间表（**建议**）

| 时间 | 做什么 |
|---|---|
| 开始前 30 分钟 | 跑 `healthcheck.sh`，确认 ✓ 全绿 |
| 开始前 15 分钟 | 把 3 个 demo 各跑一遍，记录每个耗时 |
| 开始前 5 分钟 | 打开屏幕到 Gradio UI（或终端 ready），打开 `DEMO_SCRIPT.md` 在另一显示器 |
| 开始 | **Demo 2 → Demo 1 → Demo 3** 顺序演（先稳后亮） |
| Q&A | 备用 1 或 2 视提问而定 |

---

## 现场救命：**视频备份**

**演示前 1 小时手机录屏一遍**，跑通三个 demo。

文件命名建议：`demo_2026-06-XX_HHMM.mp4`，存在手机和 iCloud / Google Drive。

万一现场 vLLM 炸了：
1. **承认问题，不慌**："Live demo, you know how it goes."
2. **放视频** + 讲架构（架构图）
3. **现场尝试恢复**（按 `ON_SITE_PLAYBOOK` 降级阶梯）

评委对**临场冷静**的印象远高于"啥都顺"。

---

## "What's Special"——评委必问

预备好这几条卖点的回答：

| 评委问 | 你的回答 |
|---|---|
| "为什么这模型选 120B？" | "MoE A12B 激活 12B 参数，在 GB10 的 273 GB/s 带宽下 decode 速度有竞争力，且 NVFP4 量化压缩到 75 GB 能装进 128 GB 统一内存" |
| "agent 跑得慢，咋办？" | "降到 30B FP8（一行 docker run 切换），agent 代码零修改——后端可换，OpenAI 端点不变" |
| "断网怎么办？" | "整个 stack 离线运行：模型权重、镜像、wheel、文档全在 SSD。可以现场拔网线证明" |
| "为啥不用 NemoClaw 全栈？" | "时间预算下，OpenAI-compatible :8000 + FastAPI mock tools 给同样的 agent 体验。NemoClaw 兼容路径在 SSD 准备过，剩余时间够就接" |
| "你的差异化是？" | "本地（隐私+延迟）+ 多能力组合（RAG + SQL + tools）+ 完整降级阶梯（断网/OOM/sm_121 兼容性都有备案）" |

---

**底线**：哪怕只有 Demo 2 一个能跑，**那也是完整故事**。先稳一个，再叠两个，再做演示视频。这个顺序绝不能反过来。
