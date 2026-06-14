# 沙盒 Mock 数据说明

全部为虚构数据,公司名 **Meridian Robotics, Inc.**。覆盖两个最常见、也最容易出彩的 agent 方向。两套数据可以单用,也可以组合成一个"既能查数据、又能调工具"的自治业务 agent。

## A) `ops_agent/` — IT/HR 运维支持 Agent(RAG + 工具调用)
- `employee_handbook.md` / `.pdf` — 员工手册(PTO、报销、安全、福利…)。RAG 知识库。
- `it_troubleshooting_guide.md` / `.pdf` — IT 排障指南(VPN、改密、错误码、SLA、升级矩阵)。
- `product_api_docs.md` — 虚构产品 Meridian Fleet API 文档(给 RAG 演示"查 API 文档")。
- `internal_tools_openapi.json` — **OpenAPI 3.1 工具规范**:`lookup_employee` / `create_ticket` / `get_ticket_status` / `request_pto` / `reset_password`。让 OpenClaw/agent 演示**多步骤自治工具调用**(先核身→再开单/改密)。
- `incident_logs.csv` — 4000 条服务日志,内置一个 14:00–15:00 的相关性故障窗口(telemetry-ingest 积压 → fleet-api 429),适合演示"根因分析" agent。

**示范故事**:用户问"我 VPN 连不上,报 VPN-503" → agent 检索 IT 指南给出修复步骤 → 调 `lookup_employee` 核身 → 调 `create_ticket` 开 P2 单 → 返回单号。

## B) `analytics_agent/` — Text-to-SQL / 数据分析 Agent
- `company.db` — SQLite(7 张表:regions / sales_reps / customers / products / orders / order_items / support_tickets;2500 订单、6271 行明细、1800 工单)。
- `*.csv` — 每张表的 CSV 导出(给非 SQL / pandas 路线)。
- `data_dictionary.md` — 表结构 + 营收口径 + **8 个适合给 agent 打分的示范问题** + 一条标准答案 SQL。

**示范故事**:"2025 年各产品类别的完成营收是多少?" → agent 生成 SQL → 查 `company.db` → 出表/图。

## 组合用法(自治业务 agent)
让一个 agent 同时挂上"知识库检索 + Text-to-SQL + OpenAPI 工具",演示它**自己决定**该查文档、查数据库,还是调工具——正好契合本次"企业级自治 agent"命题。

## 现场把数据喂进去
- RAG:把 `*.md` / `*.pdf` 切块 → 用 bge-large-en 向量化 → faiss/chroma。
- Text-to-SQL:把 `data_dictionary.md` 的 schema 放进系统提示,让模型对 `company.db` 生成只读 SQL。
- 工具调用:用 `internal_tools_openapi.json` 起一个本地 mock server(`:8088`),把 operationId 暴露成函数给模型。

> 想重新生成或调规模,改 `gen_mock_data.py` 里的种子/数量即可(已随包附带)。
