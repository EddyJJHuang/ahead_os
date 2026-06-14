# 🚀 START HERE — Mission Briefing

> **如果你是新 AI agent（Claude Code / ChatGPT / Cursor 等）首次读这个目录：**
> 你的任务是帮用户在接下来 6-10 小时内，在 NVIDIA GB10 上完成 hackathon demo。所需材料全部在本 SSD。**按下面顺序读取并执行**，不要发明新方案。
>
> **如果你是新加入的人类队友：**
> 同样的目标。这份文件 5 分钟读完，然后跟用户对齐分工。

---

## 🎯 项目目标（30 秒版）

为 Dell × NVIDIA "Local AI on Dell Pro Max with GB10" Hackathon 构建并演示一个**完全本地运行的自治业务 agent**。Agent 能：

1. **RAG**：检索 IT/HR 知识库（员工手册、排障指南）
2. **Text-to-SQL**：查询销售数据库（虚构公司 Meridian Robotics）
3. **工具调用**：调用内部工具（查员工、开工单、申请 PTO 等）

**一切跑在 GB10 一台机器上**，推理走本地（无云端依赖）。

---

## 📍 当前状态（更新于 2026-06-14）

| 项 | 状态 |
|---|---|
| 137 GB 离线包（模型 / 镜像 / wheel / mock 数据 / 源码） | ✅ 全在 SSD，SHA-256 校验过 |
| 代码骨架（`agent.py` / `mock_server.py` / `build_index.py`） | ✅ 写好可跑 |
| RAG 索引（`rag_index.faiss` + `rag_chunks.json`） | ✅ 在 Mac 上预建好了 |
| 部署 runbook（`ON_SITE_PLAYBOOK.md`） | ✅ 6 个 Phase + L0-L5 降级阶梯 |
| 演示脚本（`DEMO_SCRIPT.md`） | ✅ 3 个固定演示场景 |
| Claude Code 工作流（`CLAUDE.md` + `.claude/settings.local.json`） | ✅ 预批准 + 上下文 |
| **vLLM 启动参数现场实测** | ⏳ **可能未做 dry-run**，看用户当下情况 |
| **Gradio UI** | ⏳ 未做 |
| **Demo 视频备份** | ⏳ 未做 |

---

## 🚀 你（新 AI / 队友）现在要做的事

**按顺序，不要跳步**。

### Step 1（5 分钟）— 读这些（按顺序）

1. **此文件**（你正在读）
2. `CLAUDE.md` — 项目约束、不能装什么、约定俗成
3. `DEMO_SCRIPT.md` — 具体要演什么（**3 个固定场景**）
4. `ON_SITE_PLAYBOOK.md` 的 Phase 1-6 — 部署指令
5. `BUNDLE_INVENTORY.md` — 仅在需要查细节时回来翻

读完后，跟用户对齐**当前在哪个 Phase**，再开始动手。

### Step 2（15 分钟）— 验证环境

```bash
bash healthcheck.sh
```

任何 ✗ 都停下来修。绿光后才能往下。

### Step 3（30-60 分钟）— 部署 stack

按 `ON_SITE_PLAYBOOK.md` Phase 1-5 走。**里程碑**：

```bash
curl http://localhost:8000/v1/models   # 返回模型 ID 才算通过
```

**这步没通过，绝对不要往下走。** 先解决推理后端，再谈 agent。

### Step 4（1-3 小时）— 让 demo 跑通

```bash
cd $HOME/hack && source .venv/bin/activate
python3 agent.py     # smoke test
```

然后对照 `DEMO_SCRIPT.md` 的 Demo 1 / 2 / 3，**每个跑两遍稳定通过**才算搞定。

### Step 5（1-2 小时）— 打磨

按时间剩余选做：
1. Gradio UI（5 行包出聊天框）
2. 手机录 demo 视频（**保命**）
3. 1 张架构图 + 1 张 "what's special" 卖点图

---

## ✅ "完成"的定义

演示前必须全满足：

- [ ] `DEMO_SCRIPT.md` 三个场景**每个连跑两遍**都通过
- [ ] 单个 demo 端到端 < 30 秒
- [ ] **手机录屏一份完整 demo**（GB10 现场炸了的保险）
- [ ] 1 张架构图（agent → :8000 → vLLM）
- [ ] 1 张差异化卖点图（128GB UMA、sm_121 NVFP4、本地零云端）

---

## 📂 文件优先级

| 级别 | 文件 | 作用 |
|---|---|---|
| 🔴 P0 | `START_HERE.md` | 本文件——任务简报 |
| 🔴 P0 | `CLAUDE.md` | 项目约束 + AI 指引 |
| 🔴 P0 | `DEMO_SCRIPT.md` | 具体演示场景 |
| 🔴 P0 | `ON_SITE_PLAYBOOK.md` | 部署 + 降级阶梯 |
| 🟠 P0.5 | `WINNING_PLAYBOOK.md` | **如何高效赢**——并行模式、时段策略、故事框架、20 题 Q&A 准备。**比赛前夕必读** |
| 🟡 P1 | `agent.py` | 主要要改的代码 |
| 🟡 P1 | `mock_server.py` | 后端依赖，一般 `uvicorn ... &` 起着 |
| 🟡 P1 | `healthcheck.sh` | 快速自检 |
| 🟢 P2 | `BUNDLE_INVENTORY.md` | 查物料、查 wheel 版本时翻 |
| 🟢 P2 | `RUNBOOK.md` | 设计哲学背景 |
| ⚪ P3 | `download/` | 历史下载脚本，**现场不再用** |

---

## 🚫 绝对不要做（Anti-Goals）

1. ❌ **不要 `pip install torch / vllm / nvidia-*`** — 它们在 vLLM docker 镜像里，pip 装会和 CUDA/sm_121 撞挂，浪费几小时
2. ❌ **不要写测试**（pytest / unittest）— hackathon 时间宝贵，code review > 测试
3. ❌ **不要重构 agent.py 架构** — 沉没成本，改某个函数就好
4. ❌ **不要加新 Python 包** — wheel set 已固定。新包需要 arm64 manylinux_2_39 wheel，现场拉是大坑
5. ❌ **不要改 L0-L5 降级阶梯** — 已设计周全，作为逃生通道使用
6. ❌ **距 demo < 4 小时还做大改动** — 风险/收益失衡
7. ❌ **不要为错误指标优化** — 瓶颈是**带宽 ~273 GB/s**，不是 FLOPs。别去调 GPU 计算

---

## 📜 关键决策日志（为什么是 X 而不是 Y）

| 决策 | 原因 |
|---|---|
| vLLM 用 docker，不 pip install | sm_121 需要 NGC 专门构建的 CUDA 栈，pip 版本不支持 |
| 主模型 = 120B-NVFP4（不是 30B） | A12B MoE → 每 token 激活 ~12B 参数，在 273GB/s 带宽下 decode 速度有竞争力（**未实测，dry-run 才知道**） |
| Embedding 用 bge-large 而不是其他 | 有 ONNX export，无需 torch 依赖 |
| RAG 用 onnxruntime + faiss（不用 sentence-transformers） | sentence-transformers 会拖 torch 进来，arm64 torch 是大坑 |
| Tool 用 FastAPI mock（不直接接 NemoClaw 全栈） | hackathon 速度 > 栈完整度 |
| 02 下载用 `HF_HUB_DISABLE_XET=1` | macOS 上 Xet 协议出现死锁，纯 HTTP 路径稳定 |
| Wheel container 用 ubuntu:24.04 base | 匹配 DGX OS 7 的 glibc 2.39，否则 manylinux_2_39 wheel 装不上 |
| `--mamba-backend triton` 这类 flag | Nemotron-H 是 Mamba+Transformer 混合架构，不加可能起不来 |

**新 AI 不要推翻这些决策**——它们都有踩过的坑作为支撑。如果你觉得某条不对，先跟用户讨论再改。

---

## ⚠️ 故障 → 立刻做（Escalation Patterns）

| 失败 | 立刻做 |
|---|---|
| vLLM 起不来 | `docker logs vllm`；找 `parser not found` / `sm_121 not supported` 等关键字 |
| `:8000/v1/models` 404 | 容器端口；确认 `--network host` 是否在启动命令里 |
| `--reasoning-parser nemotron_v3` 报 "unknown parser" | 去掉这个 flag，靠 agent.py 的 `_extract_sql` 正则兜底 |
| `--tool-call-parser qwen3_coder` 不触发 | 去掉这个 flag，靠 agent.py 的 `_try_parse_inline_tool` ReAct 兜底 |
| 120B OOM | 切到 30B FP8（playbook 的 L2 路径）；改 agent.py 里 `MODEL = "nemotron-nano"` |
| Mock server 崩了 | `uvicorn mock_server:app --host 0.0.0.0 --port 8088 &` |
| Agent 输出错的 SQL | 检查 `_extract_sql` 是否剥离了 `<think>`；prompt 简化重试 |
| RAG 返回空 | 看 `rag_index.faiss` 在 cwd 还是 SSD；环境变量 `SSD_ROOT` 设了吗 |
| 全炸 | 跌到 ON_SITE_PLAYBOOK 的 L3/L4 用 llama.cpp |

详细查表见 `ON_SITE_PLAYBOOK.md` 的 **常见错误速查表**。

---

## 🆘 当用户慌乱时

放慢，提出**最小可行 demo**：

- 1 个 vLLM + 1 个 SQL 查询能跑 = **已经有完整故事**（L4 fallback demo）
- RAG 和工具是锦上添花，**只在 SQL 稳定后再叠**

**评委奖励"能跑的东西"远多于"有野心但坏的东西"**。

---

## 🧠 现场速查（最常用 5 条命令）

```bash
# 看 vLLM 在干嘛
docker logs -f vllm

# 验证整链路
bash /Volumes/SSD-3/Hackathon/healthcheck.sh
# 或在 GB10：
bash /mnt/ssd/Hackathon/healthcheck.sh

# 快速试一个 chat completion
curl -s http://localhost:8000/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"nemotron-super","messages":[{"role":"user","content":"hi"}],"max_tokens":16}' | python3 -m json.tool

# 跑 agent smoke test
cd $HOME/hack && source .venv/bin/activate && python3 agent.py

# 看 GPU 状态
nvidia-smi
```

---

**现在去 Step 1**，从读 `CLAUDE.md` 开始。
