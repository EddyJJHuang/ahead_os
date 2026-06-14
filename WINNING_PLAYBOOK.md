# WINNING_PLAYBOOK — 如何赢这场 Hackathon

> 怎样最高效地用 Claude Code + 已有资源拿下 Dell × NVIDIA "Local AI on GB10" 比赛。
>
> 本文件比 `ON_SITE_PLAYBOOK.md`（部署技术细节）和 `DEMO_SCRIPT.md`（演示台词）更上层——
> **讲战略、心智模型、和真正能赢的非技术维度**。
>
> 出发前读一遍，比赛前夕再读一遍。

---

## 0. Hackathon 黄金法则

> **赢家不是用最多 agent / 写最多代码 / 上最多技术的人。**
> **赢家是「最早跑通 demo + 故事讲得最清楚」的人。**

记住下面 4 条不要变：

1. **演示能跑 > 代码漂亮** — 评委看 demo，不看 git history
2. **故事清楚 > 技术深** — 评委 8 分钟内决定胜负
3. **预演 ≥ 新功能** — 第 6 个 demo 不如第 5 个 demo 跑稳
4. **冷静沟通 > 完美执行** — 现场炸了讲清楚比硬撑强

---

## 1. 核心心智模型：并行化的"成本 vs 收益"

任何"多线程 / 多 agent"模式都有协调成本。只有 **(节省时间 - 协调成本) > 0** 才值得做。

### 成本谱

```
[低成本/高收益]         [中成本/看情况]        [高成本/Hackathon 慎用]

后台 bash daemon       多终端 Claude          多设备多 agent 协同
subagent for research                         agent swarm 框架
                                              复杂任务编排
                                              "AI 互相对话"模式
```

### 决策树

每次想"让多个东西同时跑"时，问自己 3 个问题：

```
Q1: 这两个任务是真独立的吗？
   - 改同一个文件 → ❌ 不要并行
   - 一个等另一个的输出 → ❌ 不要并行
   - 完全分开模块 → ✅ 可以并行

Q2: 协调成本 < 单线程做完的时间？
   - 单线程 5 分钟搞定 → ❌ 不值得并行
   - 单线程 30+ 分钟 → ✅ 考虑并行

Q3: 我能监控两条线吗？
   - 一个我看不到的进程在跑 → ❌ 出问题不知道
   - 后台 + 通知 → ✅ 安全
```

---

## 2. ✅ 你**应该**用的并行模式（5 个，按收益降序）

### 模式 1 — **后台 bash daemon**（**收益最高，零协调成本**）

#### 什么时候用
任何**长跑 + 不需要持续注意力**的命令。

#### 具体场景

| 任务 | 时长 | 后台理由 |
|---|---|---|
| `docker run vllm ...` | 60-180s 加载 | 你写代码时它在加载 |
| `docker logs -f vllm` | 持续 | 后台跑，红色出错才看 |
| `uvicorn mock_server:app` | 持续 | daemon |
| `bash 02_download_models.sh` | 10-30 min | 下载完通知你 |
| `python build_index.py` | 1-2 min | 嵌入计算时干别的 |
| `shasum -a 256 -c SHA256SUMS.txt` | 5 min | 验完通知 |
| `docker pull ...` | 5-15 min | 拉镜像 |
| Gradio dev server | 持续 | UI 调试时不挂前台 |

#### 用法

```
你（对 Claude Code）：「起 vLLM 120B 在后台。然后等它 ready 后跑 healthcheck，
   同时帮我改 agent.py 的 _extract_sql 加上对嵌套 ``` 围栏的支持」

Claude:
  [后台: docker run -d vllm ...]
  [前台: 改 agent.py 的代码]
  (vLLM ready 通知触发)
  [前台: bash healthcheck.sh]
  → 你已经在改下一个 bug
```

**关键点**：Claude Code 的 `run_in_background: true` 会异步通知。你不用主动 poll。

#### 反例（**别这么干**）

```
❌ 不要：跑 `docker run vllm` 在前台，等 3 分钟，然后做下一件事
✅ 要：扔后台，前台继续干活
```

---

### 模式 2 — **"三终端"工作站**（**最适合 GB10 现场**）

#### 物理布局

```
┌──────────────────────────────────┬──────────────────────────────────┐
│ 终端 1（占 60% 屏幕）             │ 终端 2（占 20% 右上）             │
│   主 Claude Code 对话             │   docker logs -f vllm           │
│   - 写代码、改 prompt             │   - 持续观察推理引擎             │
│   - TaskCreate 跟踪 demo 完成度   │   - 红色错误一眼可见             │
│   - 跑测试                        │                                 │
│                                  ├──────────────────────────────────┤
│                                  │ 终端 3（占 20% 右下）             │
│                                  │   ad-hoc bash                   │
│                                  │   - curl http://...             │
│                                  │   - sqlite3 company.db          │
│                                  │   - python3 -c "..."            │
└──────────────────────────────────┴──────────────────────────────────┘
```

#### 为什么这样分

- **终端 1**：你的"思考密度"在这。Claude 主导，深度迭代
- **终端 2**：被动监控。你不主动看，但出错时眼角扫到
- **终端 3**：瞬时验证。改了 SQL prompt 后立刻 curl 一下，不需要让 Claude 操心

#### 关键命令配置

终端 2 启动（vLLM 跑起来后立刻起）：
```bash
docker logs -f vllm 2>&1 | grep -E "ERROR|WARN|Application startup|Traceback"
# 用 grep 过滤掉日志噪声，只保留关键信号
```

终端 3 常用预设（写进 `.zshrc` 或 alias）：
```bash
alias t='curl -s http://localhost:8000/v1/models | python3 -m json.tool | head -10'
alias tt='curl -s http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d "@/tmp/q.json" | python3 -m json.tool'
alias h='bash /mnt/ssd/Hackathon/healthcheck.sh --quick'
alias logs='docker logs --tail 50 vllm'
alias q='sqlite3 /mnt/ssd/Hackathon/mock_data/analytics_agent/company.db'
```

这样输 `t` 就能验证 :8000，输 `h` 就能 healthcheck。**省下每次的 30 秒打字**，一天累积下来是几小时。

---

### 模式 3 — **Mac 当"辅助大脑"**（**单人团队的最大武器**）

#### 核心思想
GB10 = 推理引擎 + 主开发；Mac = 不依赖 vLLM 的辅助工作。**两台机器不抢同一资源**。

#### 严格分工（重要！）

| Mac Claude 干 | GB10 Claude 干 |
|---|---|
| `gradio_app.py` UI 代码 | `agent.py` 核心逻辑 |
| `SLIDES.md` / 架构图 | vLLM 启动调参 |
| `demo_video_script.md` 录制脚本 | mock_server 调整 |
| `PITCH.md` 故事打磨 | 实际跑 demo 验证 |
| 翻 `NemoClaw repo` 找文档 | 测试集成 |
| 准备 Q&A 模拟问题 | 跑实际推理 |
| README / 提交说明 | 实际数据流验证 |

#### **绝对不能让两个 Claude 同时改**

- ❌ 同一个 `.py` 文件
- ❌ 同一个 prompt 模板
- ❌ 同一个配置文件

git 冲突 + 上下文不一致 = 半小时调试。**严格按文件 / 模块分工**。

#### 同步节奏

每 **30-45 分钟**对一次（口头或微信）：
- "我搞定 Demo 1 了"
- "Gradio 的 streaming 接好了"
- "slide 第 3 页要不要加一个图"

不要 2 小时不沟通各跑各的——分歧会越积越大。

#### Mac Claude 启动 prompt（开赛前贴一遍给它）

```
我们在 Dell × NVIDIA GB10 Hackathon。SSD 在 /Volumes/SSD-3/Hackathon。
请先读 START_HERE.md → CLAUDE.md → DEMO_SCRIPT.md。

你的角色：辅助大脑。GB10 上有另一个 Claude 写主代码。
你只动这些文件（绝不动 agent.py / mock_server.py）：
  - gradio_app.py（要新建）
  - SLIDES.md
  - PITCH.md
  - demo_video_script.md
  - 任何 docs/

不要尝试连本地 :8000——你在 Mac 上，那是 GB10 的端点。
所有需要跑推理验证的事让 GB10 Claude 干。
```

---

### 模式 4 — **Subagent 做"深挖型"任务**

#### 何时派出 subagent

主 Claude 对话不应该被"读 50 个文件找 1 个答案"消耗 token。**派 Explore subagent 去找，主线程继续**。

#### 典型场景

| 任务 | 适合 Explore | 适合 general-purpose |
|---|---|---|
| "NemoClaw 怎么 air-gapped install" | ✅（读 repo） | |
| "vLLM 26.01 里 mamba-backend 默认值是啥" | ✅ | |
| "我们 mock_data 里的故障窗口数据具体长啥样" | ✅ | |
| "帮我写一个 Gradio 的 streaming UI" | | ✅ |
| "把 incident_logs 接进 agent" | | ✅（多步任务）|

#### 用法示例

```
你：「我搞不清楚 NemoClaw 离线 install 要哪些预下镜像。让 Explore agent 翻 repos/NemoClaw，
   告诉我：1) install.sh 会拉哪些 image，2) 哪些可以 air-gapped，3) 现场 fallback 方案」

Claude: [spawn Explore agent in parallel]
       [主线程：你可以继续改 agent.py 不被打断]
       (~ 5 分钟后)
       [Explore agent 返回 200 字结论 + 命令]
```

#### 关键好处
- Explore agent 读 50 个文件 → 你看 200 字结论
- 不污染你的主对话上下文（节省 token）
- 主对话保持专注（不被资料淹没）

#### **不要这么用 subagent**

- ❌ "让 3 个 agent 提议架构，再投票" → 浪费时间，结果通常平庸
- ❌ "派 agent 写 demo 代码再 review" → 你自己 review 更快
- ❌ "agent 之间相互对话" → coordination 噩梦

---

### 模式 5 — **TaskCreate 当"demo 检查清单"**（不是 todo list）

#### 用法误区

```
❌ 错：
TaskCreate("改 agent.py")
TaskCreate("加 Gradio UI")
TaskCreate("跑测试")
TaskCreate("修 bug")
... (变成普通 todo list，没意义)
```

```
✅ 对：把 demo deliverable 写成 task
TaskCreate("Demo 1: Alice VPN-503 → 端到端 < 30s 连跑 2 次稳定")
TaskCreate("Demo 2: SQL Top 5 revenue → markdown 表格 < 15s")
TaskCreate("Demo 3: 多轮 PTO → Turn 1 缺信息不调工具，Turn 2 调成功")
TaskCreate("Gradio UI 三个 demo 都能跑")
TaskCreate("手机录视频备份")
TaskCreate("架构图 1 张 + 卖点 slide 3 张")
TaskCreate("Q&A 20 题预演")
```

#### 为什么这样更好

- **是 demo 维度的**，不是技术维度的——评委只关心这些
- **能停下来检查**：每个 task complete 是真完成（"我跑了 2 次都过了"）
- **不会无限增长**：列表固定 ~10 项

#### 跟 Claude 配合
Claude 看到 TaskList 会自动追踪、提醒未完成、检查 blocker。比纸 todo 强 10 倍。

---

## 3. ❌ **绝对不要**用的并行模式（4 个反模式）

### 反模式 1 — **多个 Claude 改同一个文件**

#### 典型翻车

- Mac Claude 给 `agent.py` 加 Gradio
- GB10 Claude 同时改 `_extract_sql` 函数
- 你 git pull/push → 冲突
- 修冲突时不知道谁覆盖谁
- 30-90 分钟蒸发

#### 对策

**强制：一个文件一个 Claude**。在文件顶部加 `# OWNED BY: gb10` 注释，跨设备 sync 时只 push owned 文件。或者干脆**两台机器不共享 git**——Mac 写的是独立文件，scp 到 GB10。

---

### 反模式 2 — **Agent swarm / 编排框架**

#### LangChain Swarm / CrewAI / AutoGen 类的玩法

**Hackathon 不要碰**。理由：

- 配置时间 > 节省时间
- 调试时间 ≫ 单 agent 调试
- 评委也不关心"你 agent 之间怎么协同"
- 你的故事是**端到端业务应用**，不是**多 agent 研究**

#### 比赛主题对照

| 题目类型 | 适合 multi-agent 协同？ |
|---|---|
| "做一个 agent 解决业务问题" | ❌ 不需要——单 agent 已经够 |
| "research agent collaboration" | ✅ 但这不是你这次的题 |

#### 你的 demo 已经够"多步"

`agent.py` 里 `chat_with_tools` 已经多轮调用工具——这就是 agentic 行为。**不需要叠一层 orchestration 框架**来证明这点。

---

### 反模式 3 — **用 multi-agent 做"创意发散"**

#### 听起来很美

"让 3 个 agent 各自提议演示方向，再投票选最好的"。

#### 现实

- 你的架构已经定了（`START_HERE.md` 决策日志）
- 重新发散浪费 30-60 分钟
- "投票"出来的方案常常是**最平庸的**（每个 agent 都妥协）
- 没人愿意担责（共识 = 没人在乎）

#### 替代方案

**你**做决策，Claude 执行。或者让**一个**Claude 给你 3 个选项 + 优劣，**你**拍板。

---

### 反模式 4 — **过度使用 Plan mode**

#### 什么时候 Plan mode 有用
- 大重构（不会发生在 hackathon）
- 复杂迁移（不会发生）
- 跨多文件的设计决定（罕见）

#### Hackathon 99% 的情况
- "把这个函数改一下" → 直接 Edit
- "加个 Gradio UI" → 直接 Write
- "测一下" → 直接 Bash

**Plan mode 的 review 步骤就是 1-2 分钟成本**。1 天里如果你用 30 次 plan mode，浪费 30-60 分钟。

#### 正确用法

只在**真不确定该不该做**时用：
- "我要不要把整个 agent.py 重写成 LangGraph？" → 用 Plan mode，让 Claude 给你 pros/cons 决定
- "把 prompt 加一行" → 直接动手

---

## 4. 时段化 Workflow（小时级时间预算）

按 **9-10 小时 hackathon** 估算。实际多/少按比例调。

### 时段 1 — 开赛 **0-1 小时**（**单线程，全注意力**）

#### 目标
**`curl http://localhost:8000/v1/models` 返回模型 ID**。

#### 节奏
```
- 0-10 min:  ON_SITE_PLAYBOOK Phase 1（硬件验证、Docker 检查）
- 10-25 min: Phase 2（挂 SSD、shasum 校验）
- 25-50 min: Phase 3（拷贝到本机 NVMe）
- 50-55 min: Phase 4（docker load 镜像）
- 55-60 min: Phase 5 L0（vLLM 启动）
```

#### 这小时**只用**一个 Claude（GB10 上）

- 没有任何并行
- Mac Claude 还没启动
- 全注意力在让推理通

#### 关键检查点
**第 50 分钟还没到 Phase 5？** 停下来评估——是否要直接跳 30B（L2 路径）省时间。

#### 反例：**绝对别在这小时做**
- ❌ 写 Gradio UI（vLLM 还没通）
- ❌ 准备 slides（早了）
- ❌ 派 subagent 研究 NemoClaw（不在关键路径）

---

### 时段 2 — 开赛 **1-4 小时**（**双线程，按文件分工**）

#### 目标
3 个 Demo 各自至少跑通一次。

#### 双线程配置

**GB10 Claude 干**：
1. 验证 vLLM 启动参数（`--reasoning-parser` / `--tool-call-parser` 真的工作？）
2. 跑 `agent.py` smoke test
3. 调 `_extract_sql` 直到 SQL 干净
4. 跑 Demo 2（最简单先打）
5. 跑 Demo 1（多工具串联）
6. 跑 Demo 3（多轮）

**Mac Claude 干**（同时）：
1. 写 `gradio_app.py`（不依赖实际 vLLM 跑通）
2. 准备 `PITCH.md`（故事）
3. 准备 `SLIDES.md`（4-5 张幻灯片）
4. 翻 `NemoClaw` 看 air-gapped 可能性（备选话题）

#### 同步点
- **1.5h**：第一次对齐（"我搞到 Demo 2 了") 
- **2.5h**：第二次对齐
- **3.5h**：第三次对齐 + 评估剩余时间分配

#### 失败处理
**3 小时还没 Demo 1 跑通？** 评估降级：
- 跌到 30B FP8 + 简化 Demo 1（去掉一个工具调用）
- 或：放弃 Demo 3，集中弄 Demo 1+2

---

### 时段 3 — 开赛 **4-7 小时**（**收敛到单线程 + subagent**）

#### 目标
- 3 个 demo 都跑过至少 2 次
- Gradio UI 集成完成
- 故事打磨完成

#### 为什么收敛
集成阶段——所有东西要拼起来。**多线程会引入冲突**。回到单 Claude 主导。

#### 配置
```
单 Claude Code（主写集成代码）
+ Explore subagent 偶尔派出去查文档（比如 "NemoClaw 这个 config 选项是啥"）
+ 后台 daemon 继续跑
```

#### 关键任务
1. **集成 Gradio UI + agent.py**（如果 Mac Claude 已经写好）
2. **跑 demo 至少 2 次稳定**
3. **量化每个 demo 耗时**
4. **改 prompt 直到 Demo 1 始终 < 30s**

#### 检查点
**第 6 小时还没 3 个 demo 都跑通？** 砍：放弃复杂度最高的那个，确保剩下 2 个 rock solid。

---

### 时段 4 — 开赛 **7-9 小时**（**演练 + 录视频 + slides**）

#### 目标
- 演讲台词练 2-3 遍
- 手机录屏完整 demo 1 遍
- Slides 终稿

#### 节奏
```
- 7-7.5h:  演练 Demo 1+2+3 完整流程，发现并修小 bug
- 7.5-8h:  演练 + 计时（每个不超 30s）
- 8-8.5h:  录视频（GB10 屏幕 + 手机录 + 上传 iCloud）
- 8.5-9h:  Slides 终稿 + 打印讲稿
```

#### 这阶段**禁止**
- ❌ 加新功能
- ❌ 改 prompt（除非现场炸了）
- ❌ 重启 vLLM（避免引入新问题）

#### Claude Code 在这阶段
- 帮你跑 demo 各 2-3 遍记录稳定性
- 帮你预测评委可能问的 20 个问题 + 答案
- 帮你写 slides 文案

---

### 时段 5 — 开赛 **9 - end**（**冷静 + 演**）

#### 立刻做
- **吃饭、上厕所、喝水**（不要饿着上台）
- **不再碰键盘**（除非现场救火）

#### 出场前 5 分钟
- 终端切到 demo 屏幕
- Slides 打开第 1 页
- 手机视频开屏幕（评委要看时秒拿出）
- 深呼吸 3 次

#### 上场
```
Demo 2（SQL，最稳）→ Demo 1（头牌）→ Demo 3（亮点）→ Q&A
```

**绝不打乱顺序**——先稳后亮，给评委建立信心。

---

## 5. Claude Code 杀手锏（Hackathon 高频功能）

### `/verify` skill

改完代码后让 Claude 实际跑一次验证（不只是看代码 reasoning）。

```
你：「改完 agent.py 的 _extract_sql，跑 /verify 确保 Demo 2 仍然通过」
Claude: [跑 agent.py + 跑 Demo 2 的标准问题 + 检查输出 + 报告]
```

### `/run` skill

启动 app 并自动 screenshot。Gradio UI 调好后用这个验证。

```
你：「跑 gradio_app.py 并 screenshot 主页，看看排版」
```

### `TaskCreate` + 后台

```
1. TaskCreate demo 检查清单（5-7 个）
2. 后台跑 vLLM / mock_server / Gradio
3. 主对话改代码
4. Claude 自动管理任务状态
```

### Subagent 派遣

```
"派 Explore agent 去 repos/NemoClaw 找 air-gapped install 步骤，
 限定 200 字回复，要可执行命令"
```

### 模型选择

| 模型 | 何时用 | 速度 / 成本 |
|---|---|---|
| **Sonnet 4.6** | 90% 的工作——写代码、改 bug、迭代 | 快、性价比最高 |
| **Haiku 4.5** | 批量小任务、解析日志、简单查询 | 极快 / 极便宜 |
| **Opus 4.7（你当前）** | 复杂架构、奇怪 bug 排查、关键决策 | 慢 / 贵但最深 |

**hackathon 90% 用 Sonnet**，Opus 留给"我搞不懂这个 bug 是什么"时刻。

---

## 6. "赢"的非技术维度（**与技术同等重要**）

### 6.1 故事 ≫ 技术

#### 评委到你 demo 时

他们已经看了 10 个其他 demo，疲惫、走神。**你前 30 秒决定他们打分**。

#### Pitch 框架（出发前固化到 `PITCH.md`）

```
1. 问题（10s）：[一个真实的、可感知的痛点]
   "企业 IT 工单平均 2 小时响应，员工常常重复问同样的问题"

2. 洞察（10s）：[为什么现在能解，过去不能]
   "本地大模型让 24/7 一线响应成为可能，但隐私让企业不能用云端"

3. 解决方案（10s）：[一句话]
   "Meridian Helpdesk Agent — 完全本地运行的智能 IT 一线"

4. 为什么 GB10（10s）：[硬件契合]
   "128 GB 统一内存装得下 120B；NVFP4 量化 + sm_121 推理；本地零数据外泄"

5. 看 Demo（80s × 3）：[演 3 个]

6. 商业价值（20s）：
   "每企业每年节省 50 万运营成本；员工等待时间 -80%"
```

**总 4 分钟讲完**，剩下 4 分钟 Q&A。

### 6.2 预演的边际收益（**比写新功能高 10×**）

#### 每多预演一遍

- 发现 1 个 prompt 边缘 case
- 发现 1 个 SQL 偶尔生成错误
- 演讲台词更熟
- 拿到耗时基线
- **建立心理冷静**

#### 用 Claude 帮你预演

```
你：「按 DEMO_SCRIPT.md 的 Demo 1 流程跑一遍，记录每步耗时，
   告诉我有没有 prompt 边缘 case」
```

让 Claude 反复跑 demo（每次自动记录），3-5 次后 bug 都暴露完了。

### 6.3 降低评委理解成本

```
❌ "我用 NemoClaw + OpenShell + Nemotron-3-Super-120B-A12B-NVFP4..."
   评委：[zone out]

✅ "It's a local IT helpdesk. Watch—I ask, it answers, it acts."
   评委：[lean in]
```

技术词只在**评委追问时**才出。开场用人话。

让 Claude 把所有技术词翻译成人话（这是 LLM 最擅长的）。

### 6.4 Q&A 预演 20 题

#### 评委肯定会问的

```
1. 为什么选这个模型？
2. 跑得多快？(token/s)
3. 隐私怎么保证？
4. 比 GPT-4 强在哪？
5. 现在能不能商业化？
6. 多少员工能用？
7. 训练成本？
8. 维护成本？
9. 如何扩展到新场景？
10. 准确率怎么测？
11. 出错了怎么办？
12. 集成现有系统难吗？
13. 多语言支持？
14. 跟 Microsoft Copilot 比？
15. 数据从哪来？真实数据测过吗？
16. 评估指标？
17. 部署多久？
18. 谁负责更新？
19. 一年 ROI？
20. 你们怎么继续做？
```

#### 让 Claude 帮你写每题 30 秒答案

存到 `Q_AND_A.md`。**开场前花 20 分钟熟读**。

---

## 7. 现场认知管理（**身体 / 大脑能耗管理**）

### 体能法则

- 每 90 分钟**强制起身 5 分钟**（厕所 / 喝水 / 远眺）
- 每 3-4 小时**吃东西**——血糖低 = 决策差
- 喝够水 → 思维清晰
- **不要喝太多咖啡**——后期心慌手抖影响演讲

### 大脑能耗管理

```
高能耗任务（≤ 2 小时连续）：
  - 写架构、调 prompt、改 SQL
  - 故事打磨

低能耗任务（可以累时做）：
  - 跑 demo 预演
  - 看 Claude 输出
  - 录视频
  - 准备 slides

绝不在 fatigued 时做：
  - 修 vLLM 启动参数
  - 重构 agent.py
  - 重大架构决定
```

### "Kill switch" 心理预案

#### 现场某事炸了，决策原则

1. **0-5 分钟**：尝试快速修
2. **5-15 分钟**：尝试降级（L0 → L1）
3. **15+ 分钟**：**放视频，讲故事，做 Q&A**
4. **绝不**：在评委面前 30 分钟 debug

#### 提前定义你的 "kill switch"

```
触发 → 立刻做

vLLM 30 min 起不来 → 放弃 120B，切 30B 或 llama.cpp
agent.py 改了 1h 没好转 → 回滚到上次能跑的版本
demo 第 3 次连续失败 → 放弃这个 demo，强化剩下 2 个
Gradio 没集成完 → 走纯 curl/CLI demo
全炸 → 录的视频 + 讲故事 + Q&A
```

**事前定义这些** = 事中冷静执行。

---

## 8. 现场速查卡（**贴屏幕边**）

### 三屏布局
```
主屏：Claude Code + 你的代码
副屏 / 右上：docker logs -f vllm（grep ERROR/WARN）
副屏 / 右下：ad-hoc curl + sqlite + python -c
```

### 5 个最常用命令

```bash
# 验证整链路（最常跑）
bash /mnt/ssd/Hackathon/healthcheck.sh --quick

# 看 vLLM 在干嘛
docker logs --tail 30 vllm

# 快速验证 :8000
curl -s http://localhost:8000/v1/models | python3 -m json.tool

# 看 GPU
nvidia-smi

# Demo smoke test
cd $HOME/hack && source .venv/bin/activate && python3 agent.py
```

### 5 个 "不要" 提醒

```
1. 不要在 demo < 2h 时改 vLLM 启动参数
2. 不要在最后 1h 里加新功能
3. 不要 chain 超过 3 个工具调用（容易出错）
4. 不要在评委面前 debug 超过 5 分钟
5. 不要忘记吃饭 + 录视频
```

### 5 个 "黄金时刻"

```
0-1h:     单线程让 :8000 通
1-4h:     双 Claude 按文件分工
4-7h:     收敛到单 Claude，集成
7-9h:     演练 ×3，录视频
9+:       冷静上台，先 Demo 2
```

---

## 9. 常见 Hackathon 陷阱（**已踩过坑的总结**）

| 陷阱 | 表现 | 对策 |
|---|---|---|
| **完美主义** | "再调一下 prompt"，停不下来 | TaskCreate 列固定 demo，每个跑过 2 次就 ✅ 不再动 |
| **范围蔓延** | "再加一个工具就更酷了" | DEMO_SCRIPT.md 锁定，超出的写到"如有时间" |
| **rabbit hole** | 调一个 bug 调 2 小时 | 30 分钟硬时限——超了就降级 / 跳过 |
| **过度抽象** | "为了以后扩展，先封装一下" | hackathon 没有"以后"——直接硬编码 |
| **优化错位** | 优化推理速度，但带宽是瓶颈 | 看 `nvidia-smi`+`docker stats` 找真瓶颈 |
| **疏于演练** | 评委来时第一次跑 demo → 翻车 | 现场前每个 demo 至少跑 3 遍 |
| **慌乱叙述** | 评委到了，技术名词飞出来 | 提前固化 PITCH.md 的开场 60 秒 |
| **能耗失衡** | 上午狂改，下午演讲时累了 | 每 90min 起身，预留 1h 不做任何事 |
| **忘录视频** | 现场炸了没保底 | demo prep 阶段就录，不在最后做 |
| **依赖网络** | 现场限网，临时下东西 | 全离线测试一次：拔网线 + healthcheck.sh |

---

## 10. 总结

**赢这场 Hackathon 的不是技术，是**：

1. **早跑通 demo**（不是写更多代码）
2. **故事讲清楚**（不是技术词堆叠）
3. **演练充分**（不是新功能）
4. **冷静沟通**（不是完美执行）

**Claude Code 的角色**：

- **不是**：让你写更多代码 / 用更多技术
- **是**：让你**更快得出"能用的 demo"**，把省下的时间花在故事、演练、Q&A 准备上

**最重要的并行**：

- 后台 bash 跑 daemon（vLLM、mock_server）
- 主 Claude 写代码 + 副 Claude (Mac) 写故事
- 主线程深度 + Subagent 探查

**最有害的"并行"**：

- 多 Claude 改同一文件
- agent swarm 框架
- "让 agents 讨论"
- 过度 plan mode

---

**最后一句**：

> 你的 SSD 上已经有 137 GB 准备好的资源、3 份完整文档、4 份代码骨架、1 份 demo 脚本、1 份 Claude Code 配置。**比 99% 的参赛者起点高得多**。
>
> 不要被自己的丰富资源诱惑去做更多东西。
> **少做、做稳、讲清楚** = 赢。

祝你 demo 飞起，奖杯抱回家。
