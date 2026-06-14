# Claude Code 项目上下文 — GB10 Hackathon

> ## ⚠️ 如果你是新加入的 AI / 队友，**先读 `START_HERE.md`**
>
> `START_HERE.md` 是 60 秒任务简报：当前状态、立刻该做什么、demo 标准、关键决策依据。
> 那份读完再回头看这份 `CLAUDE.md`（约束 + 工作环境）和 `DEMO_SCRIPT.md`（演示具体台词）。
>
> **另外**：`WINNING_PLAYBOOK.md` 详述了**如何高效用 Claude Code 赢这场比赛**——
> 并行模式（什么该并、什么不该并）、时段策略、故事框架、Q&A 准备。比赛前夕至少粗读一遍。

> 把这份文件**复制到 `$HOME/hack/CLAUDE.md`**，每次起 Claude Code 会话时它会自动加载。
>
> 这是给 Claude 看的导航文件——告诉它你在哪、能用什么、不能做什么。

---

## 我们在哪、在做什么

- **比赛**：Dell × NVIDIA "Local AI on Dell Pro Max with GB10" Hackathon
- **硬件**：GB10 / Dell Pro Max — ARM aarch64 + Blackwell sm_121 + 128 GB 统一内存
- **网络**：现场**有网**，但比赛主题是 "Local AI"，**推理必须本地**（云端只作 L5 兜底）
- **核心架构**：Agent → `http://localhost:8000/v1`（OpenAI 兼容）→ vLLM serving Nemotron。后端可换、agent 代码不动。

## SSD 离线包位置

```
/mnt/ssd/Hackathon/                       # 全部预下好的东西在这里
├── ON_SITE_PLAYBOOK.md       ★ 主参考  现场部署 6 个 Phase + L0-L5 降级阶梯
├── BUNDLE_INVENTORY.md       ★ 物料清单 137 GB 内容详细列表
├── RUNBOOK.md                  原版设计哲学
├── agent.py                  ★ 可跑骨架 text_to_sql + rag_search + chat_with_tools + ReAct 降落伞
├── mock_server.py            ★ OpenAPI 5 个 endpoint 的 FastAPI 实现，:8088
├── build_index.py              已在 Mac 上跑过，索引已在 SSD（rag_index.faiss）
├── rag_index.faiss           ★ 23 chunks 预建好的索引，零嵌入计算
├── rag_chunks.json
├── bin/                        uv 二进制（aarch64）
├── download/                   离线下载脚本 + config.env（仅作历史参考）
├── images/                     4 个 arm64 docker 镜像 tarball（vLLM × 2、OpenShell、llama.cpp）
├── mock_data/
│   ├── ops_agent/              RAG 知识库 + OpenAPI 工具规范 + 故障日志
│   └── analytics_agent/        SQLite (company.db, 7 张表)
├── models/                     Nemotron 120B-NVFP4 + 30B-FP8 + bge-large-en-v1.5
├── repos.tar.gz                NemoClaw / OpenShell / Nemotron-cookbook / llama.cpp 源码
└── wheels/                     155 个 arm64 manylinux_2_39 wheel + 11 个 openshell wheel
```

## 工作目录 `$HOME/hack/`

```
$HOME/hack/
├── CLAUDE.md           # 本文件
├── .venv/              # python venv（用 wheels 离线装）
├── models/             # 从 SSD 拷过来的（NVMe 比 SSD 快）
├── images/             # 同上
├── repos/              # 解压 repos.tar.gz
├── wheels/             # 直接挂 SSD 也行
├── mock_data/          # 直接挂 SSD 也行
├── agent.py            # 从 SSD 拷一份过来开始改
├── mock_server.py
└── rag_index.faiss
```

## 不可破坏的约束（**Claude，写代码前务必检查**）

1. **绝不安装 torch / vllm / nvidia-* / flash-attn / transformers-with-cuda**——它们在 vLLM 镜像里，pip 装会和 CUDA 撞挂，浪费几小时
2. **Agent 永远对着 `http://localhost:8000/v1` 说话**（OpenAI 兼容客户端），不要直接 `requests.post` 到 vLLM 内部 endpoint
3. **wheel 安装一律 `pip install --no-index --find-links wheels/app`**——venue 可能限网
4. **新 Python 包不要随便加进 `requirements.app.txt`**——你装不上，arm64 wheel 全部已经预下，新增就要现场离线下载
5. **改 vLLM 启动参数**前先看 `ON_SITE_PLAYBOOK.md` Phase 5——里面的 `--mamba-backend / --reasoning-parser / --tool-call-parser` 是 Nemotron-H 架构特有的必备 flag
6. **不要写测试**——hackathon 时间宝贵，code review > 测试

## Claude 常用模型选择（hackathon 场景）

- **Sonnet 4.6**：90% 的工作。写代码、改 bug、迭代 agent 逻辑
- **Haiku 4.5**：批量小任务、调用工具、解析日志
- **Opus 4.7（当前）**：复杂架构决策、奇怪的 bug 排查

## 现场快速验证一切就绪

```bash
# 1. 推理后端通了吗？
curl -s http://localhost:8000/v1/models | python3 -m json.tool

# 2. mock server 通了吗？
curl -s http://localhost:8088/health

# 3. agent 完整链路 smoke test
cd $HOME/hack && source .venv/bin/activate && python3 agent.py
```

## Demo 黄金问题（**演示固定这几个，不要临场即兴**）

1. **Text-to-SQL**：从 `mock_data/analytics_agent/data_dictionary.md` 选 2-3 个（推荐 Q1 / Q4 / Q5）
2. **工具调用**：演示 lookup_employee → create_ticket 串联（如 "我 VPN 报 503，开个 P2 单"）
3. **RAG**：演示 "VPN-503 怎么解" → 检索到 it_troubleshooting_guide 给出步骤

## 紧急逃生

- vLLM 起不来 → 看 ON_SITE_PLAYBOOK §5 的 L0→L5 降级阶梯
- agent 出怪结果 → 看 ON_SITE_PLAYBOOK §6.2 的 `_extract_sql` / `_try_parse_inline_tool`
- 全炸 → 备 demo 视频（**出发前录一段**）

---

**一句话总结：`:8000` 通 → mock_server 通 → `python agent.py` 通 → demo 三题，结束。**
