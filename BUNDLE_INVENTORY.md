# GB10 Hackathon Bundle — 详细清单

> **目的**：给队友 / AI agent 一份独立可读的清单，让对方不必看其他文档就能理解 SSD 上的全部内容、各组件的角色，以及快速开始的最佳路径。
>
> 上次校验：**2026-06-12 13:48 PDT**，SHA-256 全部 32 项 OK
> 总占用：**137 GB** / SSD 总容量 **3.6 TB** / 剩余 **3.2 TB**

---

## 0. 一眼概览

| 类别 | 内容 | 大小 |
|---|---|---|
| 模型权重 | 3 个（Nemotron 120B / 30B + BGE embedding） | 109 GB |
| Docker 镜像 | 4 个 arm64 镜像（已 docker save） | 19 GB |
| 源码仓库 | 4 个 NVIDIA / 开源仓库 | 7.9 GB 原始 + 583 MB tar.gz |
| Python wheels | 155 个 app + 11 个 openshell（aarch64 manylinux） | 543 MB |
| Mock 数据 | RAG + Text-to-SQL + 工具调用沙盒 | 40 MB |
| 工具二进制 | uv (aarch64) | 24 MB |
| 文档脚本 | playbook / runbook / 下载脚本 | < 50 MB |

**目标硬件**：Dell Pro Max (DGX Spark / GB10) — ARM aarch64 + Blackwell sm_121 GPU + 128 GB 统一内存 + DGX OS 7 (Ubuntu 24.04, glibc 2.39)。

---

## 1. SSD 根目录布局

```
/Volumes/SSD-3/Hackathon/                # SSD 上的根
├── ON_SITE_PLAYBOOK.md      23 KB       ★ 现场部署手册（Phase 1-6 + 降级阶梯）
├── BUNDLE_INVENTORY.md                  ★ 本文件
├── RUNBOOK.md               12 KB       原版 runbook（更多背景设计哲学）
├── README.md                1.3 KB      项目根说明
├── MANIFEST.txt             738 B       文件清单（脚本生成）
├── SHA256SUMS.txt           4.2 KB      32 个文件的 SHA-256
│
├── bin/                                 工具二进制
│   ├── uv-aarch64-unknown-linux-gnu.tar.gz       22 MB
│   └── uv-aarch64-unknown-linux-gnu.tar.gz.sha256
│
├── images/                              docker save 的镜像
│   ├── nvcr.io_nvidia_vllm_26.01-py3.tar.gz       5.8 GB
│   ├── avarok_vllm-dgx-spark_latest.tar.gz        11 GB
│   ├── ghcr.io_nvidia_openshell_gateway_latest.tar.gz  29 MB
│   ├── ghcr.io_ggml-org_llama.cpp_server-cuda.tar.gz   2.4 GB
│   └── PINNED_DIGESTS.txt                         430 B (digest 对照)
│
├── models/                              HuggingFace 权重
│   ├── nemotron-3-super-120b-nvfp4/    75 GB  ← 主推理模型
│   ├── nemotron-3-nano-30b-fp8/        31 GB  ← 备用 / 降级
│   └── bge-large-en-v1.5/              3.8 GB ← embedding 模型
│
├── repos/                               源码仓库（exFAT 可能丢符号链接）
│   ├── NemoClaw/                       2.4 GB
│   ├── OpenShell/                      1.0 GB
│   ├── Nemotron-cookbook/              673 MB
│   └── llama.cpp/                      3.8 GB
├── repos.tar.gz                         583 MB ★ 现场优先解这个（不丢 symlink）
│
├── wheels/                              Python 离线依赖
│   ├── app/         155 个 wheel        ← agent 主依赖
│   └── openshell/   11 个 wheel         ← OpenShell 0.0.62 + 依赖
│
├── mock_data/                           演示数据
│   ├── ops_agent/                       RAG + 工具调用沙盒
│   ├── analytics_agent/                 Text-to-SQL 沙盒
│   ├── gen_mock_data.py                 数据生成脚本（可调种子重生）
│   └── README_mockdata.md
│
└── download/                            离线下载脚本（仅作参考）
    ├── 00_DOWNLOAD_GUIDE.md
    ├── 00_PREP_CHECKLIST.md
    ├── 01_clone_repos.sh
    ├── 02_download_models.sh
    ├── 03_download_images.sh
    ├── 04_download_wheels.sh
    ├── 05_verify_and_manifest.sh
    ├── auto_pipeline.sh                 wrapper：跑 04+05（带 caffeinate）
    ├── config.env                       下载脚本统一配置
    └── requirements.app.txt             app 依赖清单
```

---

## 2. 模型详情

### 2.1 `nemotron-3-super-120b-nvfp4/` （主推理，75 GB，17 shards）

| 字段 | 值 |
|---|---|
| HF 仓库 | `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4`（gated） |
| 架构 | `NemotronHForCausalLM`（Latent MoE，激活约 12B） |
| `model_type` | `nemotron_h` |
| Hidden size | 4096 |
| Layers | 88 |
| Attention heads | 32 |
| Vocab | 131072 |
| 量化 | NVFP4（modelopt 后端） |
| 文件 | 17 个 `.safetensors` + `config.json` + `chat_template.jinja` + `configuration_nemotron_h.py` (custom code) + tokenizer 文件 |
| 用 vLLM 启动需要 | env: `VLLM_USE_FLASHINFER_MOE_FP4=1` `VLLM_FLASHINFER_MOE_BACKEND=latency` `VLLM_MOE_PADDING_SIZE=512`<br>flags: `--quantization nvfp4 --tensor-parallel-size 1 --kv-cache-dtype fp8 --max-model-len 4096 --gpu-memory-utilization 0.85 --trust-remote-code --mamba-backend triton --mamba-ssm-cache-dtype float32 --reasoning-parser nemotron_v3 --enable-auto-tool-choice --tool-call-parser qwen3_coder --served-model-name nemotron-super`<br>⚠️ parser 名字（nemotron_v3 / qwen3_coder）必须 dry-run 验证 |
| 启动时间 | 预估 60-180 秒（含权重加载） |

### 2.2 `nemotron-3-nano-30b-fp8/` （备用 / 降级，31 GB，10 shards）

| 字段 | 值 |
|---|---|
| HF 仓库 | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8`（gated） |
| 架构 | 同上 `NemotronHForCausalLM`（dense） |
| `model_type` | `nemotron_h` |
| Hidden size | 2688 |
| Layers | 52 |
| Attention heads | 32 |
| Vocab | 131072 |
| 量化 | FP8（hf_quant_config.json 配置） |
| 文件 | 10 个 `.safetensors` + 相同 chat template + custom code |
| 启动 | flags 同 120B 但**去掉 `--quantization nvfp4`**（FP8 自动检测）；`--served-model-name nemotron-nano`；其他 mamba / reasoning / tool flag 完全照搬（同为 `nemotron_h` 架构、同为推理模型） |
| 用途 | 120B OOM / 太慢时的降级；或考虑作为**交互主力**（dense 30B vs MoE 120B-A12B 实测延迟未定，dry-run 决定） |

### 2.3 `bge-large-en-v1.5/` （RAG embedding，3.8 GB）

| 字段 | 值 |
|---|---|
| HF 仓库 | `BAAI/bge-large-en-v1.5`（公开） |
| 架构 | `BertModel`（标准 BERT，非 causal） |
| `model_type` | `bert` |
| Hidden size | 1024 |
| Layers | 24 |
| Vocab | 30522 |
| Dtype | float32（小，没量化） |
| 文件 | 单 `model.safetensors` + `pytorch_model.bin` + **`onnx/` 子目录（含 `model.onnx` / `model_quantized.onnx`）** + tokenizer |
| 用法 | RAG 向量化。**走 ONNX + onnxruntime 路径（无 torch）**：要么用 chromadb 默认嵌入，要么直接喂 `bge-large-en-v1.5/onnx/model.onnx`。**不要装 sentence-transformers**（会拖 torch 进来）。建议赛前在 Mac 上预建 faiss/chroma 索引并 ship 到 SSD |
| 输出维度 | 1024 |

---

## 3. Docker 镜像（全部 arm64，已 docker save）

| Image | Tag | 压缩后 | Digest | 角色 |
|---|---|---|---|---|
| `nvcr.io/nvidia/vllm` | `26.01-py3` | 5.8 GB | `sha256:e497b124...` | **主推理引擎**（NVIDIA 官方 sm_121 build） |
| `avarok/vllm-dgx-spark` | `latest` | 11 GB | `sha256:2f39672c...` | 备用 vLLM（社区维护，DGX-Spark 专用） |
| `ghcr.io/nvidia/openshell/gateway` | `latest` | 29 MB | `sha256:7bc26fb5...` | OpenShell 沙盒网关（如果走全栈 agent） |
| `ghcr.io/ggml-org/llama.cpp` | `server-cuda` | 2.4 GB | `sha256:841b199a...` | 最后兜底（vLLM 全炸时的 GGUF 推理） |

加载：`gunzip -c IMAGE.tar.gz | docker load`

`PINNED_DIGESTS.txt` 里有原始 digest，加载后用 `docker image inspect` 对照可验证没串包。

---

## 4. 源码仓库

| Repo | URL | 大小 | Commit | 角色 |
|---|---|---|---|---|
| `NemoClaw` | github.com/NVIDIA/NemoClaw | 2.4 GB | `0e30bff88` (2026-06-12) | NVIDIA 自治 agent 框架；含 `install.sh`、`onboard` CLI |
| `OpenShell` | github.com/NVIDIA/OpenShell | 1.0 GB | `fb83d1a3` (2026-06-11) | 安全 agent 运行时（沙盒 + 网络策略）；Rust+Python，需要 maturin |
| `Nemotron-cookbook` | github.com/eugr/Nemotron | 673 MB | `d68bdb3` (2026-03-13) | Nemotron 部署指南；找 `usage-cookbook/Nemotron-3-Super/SparkDeploymentGuide/` |
| `llama.cpp` | github.com/ggml-org/llama.cpp | 3.8 GB | `ebc10770a` (2026-06-12) | 通用本地推理引擎；现场可编译，用 GGUF 模型 |

> **重要**：`repos/` 是直接 clone 的，exFAT 不保留 git 内的符号链接，可能损坏部分文件。**优先使用 `repos.tar.gz`** 解压到本机：
> ```bash
> tar -xzf /mnt/ssd/Hackathon/repos.tar.gz -C $HOME/hack/
> ```

---

## 5. Python Wheels

### 5.1 `wheels/app/` — agent 主依赖（155 个 wheel，aarch64 manylinux）

按功能分组的关键包：

| 类别 | 关键包 |
|---|---|
| **Agent / orchestration** | `langchain` 1.3.9, `langchain-core` 1.4.7, `langgraph` 1.2.5, `llama_index` 0.14.22, `llama_index_llms_openai_like` 0.7.2, `llama_index_embeddings_openai` 0.6.0 |
| **OpenAI 客户端** | `openai` 2.41.1, `httpx` 0.28.1, `tenacity` 9.1.4 |
| **RAG / 向量** | `faiss_cpu` 1.14.2, `chromadb` 1.5.9, `rank_bm25` 0.2.2 |
| **文档解析** | `pypdf` 6.13.2, `python_docx` 1.2.0, `beautifulsoup4` 4.15.0, `markdown_it_py` 4.2.0 |
| **数据分析** | `pandas` 3.0.3, `duckdb` 1.5.3, `sqlalchemy` 2.0.50 |
| **API/UI** | `fastapi` 0.136.3, `uvicorn` 0.49.0, `pydantic` 2.13.4, `gradio` 6.18.0, `sse_starlette` 3.4.4 |
| **HF 工具** | `huggingface_hub` 1.19.0, `hf_xet` 1.5.1, `tokenizers` 0.23.1, `tiktoken` 0.13.0 |
| **可观测** | `opentelemetry_*` 1.42.1（langchain/llama-index 自动 instrument） |

**重要排除**：**没有 `torch` / `vllm` / `nvidia-*` / `transformers`**。这些都在 vLLM 镜像里，不要在 GB10 上 pip 装 GPU 栈。

离线安装：
```bash
pip install --no-index --find-links wheels/app \
  -r /mnt/ssd/Hackathon/download/requirements.app.txt
```

### 5.2 `wheels/openshell/` — OpenShell 0.0.62（11 个 wheel）

`openshell-0.0.62-py3-none-manylinux_2_39_aarch64.whl` + 6 个直接依赖（cloudpickle, grpcio, httpx, httpcore, protobuf, typing_extensions, anyio, certifi, idna, h11）。

manylinux_2_39 标签**只能在 glibc ≥ 2.39 系统装得上**——这正是 DGX OS 7 / Ubuntu 24.04（这也是为什么下载阶段必须用 `ubuntu:24.04` 容器拉 wheel）。

---

## 6. Mock 数据

虚构公司 **Meridian Robotics, Inc.**。

### 6.1 `ops_agent/` — RAG + 工具调用

| 文件 | 大小 | 用途 |
|---|---|---|
| `employee_handbook.md` / `.pdf` | 3.3 KB / 5 KB | 员工手册（PTO / 报销 / 安全 / 福利）→ RAG 知识库 |
| `it_troubleshooting_guide.md` / `.pdf` | 3 KB / 5 KB | IT 排障（VPN-503、密码重置、SLA、升级矩阵）→ RAG 知识库 |
| `product_api_docs.md` | 1.6 KB | 虚构产品 Meridian Fleet API（演示"查 API 文档"） |
| `internal_tools_openapi.json` | 6.7 KB | **5 个工具的 OpenAPI 3.1 规范**（见下表） |
| `incident_logs.csv` | 281 KB | 4000 行服务日志，含 14:00-15:00 故障窗口（演示根因分析）|

**OpenAPI endpoints**（agent 通过这些做工具调用）：

| Method | Path | operationId | 用途 |
|---|---|---|---|
| GET | `/employees/lookup` | `lookup_employee` | 通过 email/ID 核身员工 |
| POST | `/tickets` | `create_ticket` | 开 IT/HR/security 工单 |
| GET | `/tickets/{ticket_id}` | `get_ticket_status` | 查工单状态 |
| POST | `/pto/request` | `request_pto` | 提交 PTO 请求 |
| POST | `/account/reset_password` | `reset_password` | 触发密码重置 |

> ⚠️ **目前只有规范，没有实现**。需要现场（或预先）写一个 FastAPI server 监听 `:8088`。Playbook 第 6.1 节给了 30 行骨架。

### 6.2 `analytics_agent/` — Text-to-SQL

`company.db`（SQLite，299 KB） + 7 张 CSV 等价导出。

| 表 | 行数 | 关键列 |
|---|---|---|
| `regions` | 5 | region_id, name, country |
| `sales_reps` | 10 | rep_id, name, region_id→regions, hire_date, quota_usd |
| `customers` | **110** | customer_id, segment (SMB/Mid-Market/Enterprise), region_id, signup_date |
| `products` | 8 | product_id, sku, category (Hardware/Software/Service/Accessory), unit_price |
| `orders` | **2500** | order_id, customer_id, rep_id, order_date, status (completed/refunded/pending) |
| `order_items` | **6271** | order_item_id, order_id, product_id, quantity, unit_price |
| `support_tickets` | **1800** | ticket_id, customer_id, opened_date, closed_date, priority, csat (1..5) |

**Revenue 口径**：`SUM(order_items.quantity * order_items.unit_price) WHERE orders.status = 'completed'`

`data_dictionary.md` 里有 **8 个适合给 agent 打分的示范问题** + 一条标准答案 SQL（Q1）。

---

## 7. 工具二进制 / 脚本 / 文档

### 7.1 `bin/`

- `uv-aarch64-unknown-linux-gnu.tar.gz` — uv 0.11.21 的 aarch64 linux 版（OpenShell 内部用）

### 7.2 `download/` —— 原始下载脚本（**现场不再用**，作历史参考）

| 文件 | 用途 |
|---|---|
| `00_DOWNLOAD_GUIDE.md` | Mac 端下载流程总说明 |
| `00_PREP_CHECKLIST.md` | 出发前账号 / token / 工具准备清单 |
| `01_clone_repos.sh` | 上面 4 个 repo + uv + 拉 openshell wheel |
| `02_download_models.sh` | HF 模型下载（已加 `HF_HUB_DISABLE_XET=1` 防止 macOS 死锁） |
| `03_download_images.sh` | 拉 4 个 docker 镜像，arch 校验，写 digest |
| `04_download_wheels.sh` | 在 ubuntu:24.04 arm64 容器里 pip download |
| `05_verify_and_manifest.sh` | 生成 MANIFEST + SHA256SUMS（用 stat 跨平台） |
| `auto_pipeline.sh` | wrapper：跑 03→04→05，含 caffeinate 防睡眠 |
| `config.env` | 统一配置（SSD 路径、HF repo id、镜像 tag、UV 版本） |
| `requirements.app.txt` | 53 行 app 依赖清单（torch/vllm/nvidia-* 故意排除） |

### 7.3 顶层文档

| 文件 | 用途 |
|---|---|
| `ON_SITE_PLAYBOOK.md` | **★ 现场打开这个** —— 6 Phase + L0-L5 降级阶梯 + 错误速查 + agent 骨架 + 命令速查卡 |
| `RUNBOOK.md` | 原版 runbook，含背景设计哲学（vLLM/llama.cpp 详细 flag、网络策略、OOM 管理） |
| `README.md` | 项目顶层说明（设计目标、三件套对应） |
| `BUNDLE_INVENTORY.md` | 本文件 |
| `MANIFEST.txt` | 自动生成的目录大小快照 |
| `SHA256SUMS.txt` | 32 个文件的 SHA-256，用 `shasum -a 256 -c SHA256SUMS.txt` 验证 |

---

## 8. 关键依赖关系（谁需要谁）

```
                   ┌──────────────────┐
                   │  Your agent code │ ← 你要写的（playbook §6.2 有骨架）
                   └─────────┬────────┘
                             │ OpenAI HTTP
                             ▼
              ┌──────────────────────────────┐
              │ http://localhost:8000/v1     │ ← 任何后端都监听这里
              └──────────────┬───────────────┘
                             │
        ┌──────────┬─────────┼──────────┬─────────────┐
        ▼          ▼         ▼          ▼             ▼
    [vLLM NGC] [vLLM avarok] [vLLM 30B] [llama.cpp]  [build.nvidia.com]
       L0        L1           L2         L3/L4          L5
        │           │              │
        └──────┬────┴──────────────┘
               │
               ▼
       models/{120B,30B,bge}     ← 都从本机 NVMe 读

Tools 调用 → http://localhost:8088 → mock_server.py (用 wheels/app 起 FastAPI)
                                            │
                                            └→ 实现 ops_agent/internal_tools_openapi.json 5 个 endpoint

RAG       → bge-large-en-v1.5 向量化 ops_agent/*.md → faiss/chromadb
Text-to-SQL → sqlite3 analytics_agent/company.db
```

---

## 9. 已知缺口 / 风险点（**开始前必看**）

| 缺口 | 影响 | 现场对策 |
|---|---|---|
| **没有可跑的 OpenAPI mock server** | 工具调用演示需要 | 建议**赛前在 Mac 上对着 Ollama/LM Studio 写好测好塞进 SSD**（不是现场写）；playbook §6.1 有 30 行 FastAPI 骨架 |
| **没有写好的 agent.py** | 必须现场写 | 同上，**赛前 Mac 上跑通**整条 RAG/SQL/Tool 链路后再 ship；playbook §6.2 已含 _extract_sql + ReAct 降落伞 |
| **GGUF 模型没下到**（`bartowski/...GGUF` 仓库可能改名） | L3 路径需要权重 | 现场临时联网下，或用 llama.cpp 的 `convert_hf_to_gguf.py` 把 30B 转一份 |
| **没在 Arm Linux 上预演过 `nemoclaw onboard`** | NemoClaw install.sh 可能在离线下挂在拉依赖 | 走 L1 路径（agent 直连 vLLM，跳过 NemoClaw 沙盒），仍是完整本地 demo。**注**：若赛事规则要求 NemoClaw+OpenShell+OpenClaw 全栈（待确认），这就是 dry-run 头号目标，不能跳 |
| **vLLM 版本对 sm_121 上 NVFP4 敏感** | 0.18.x 在 sm_121 上有 quantization 兼容报告 | dry-run 时跑 `docker exec vllm vllm --version` 确认；备 pin 0.17.2rc1 / 换 avarok（L1） |
| **tool-call parser 在 GB10 上未验证** | playbook 用了 `qwen3_coder` 占位 | dry-run 实测；不行就试 `hermes` / `llama3_json` / 完全去掉走 ReAct 降落伞 |
| **RAG 无 torch 路径未验证** | playbook 给了 chromadb 默认嵌入和 bge-ONNX 两套方案 | **赛前在 Mac 上预建 faiss/chroma 索引**，把索引文件直接 ship 到 SSD（现场零嵌入计算） |
| **`incident_logs.csv` 没接入 agent** | 4000 行日志含 14:00-15:00 故障窗口 | 可选：把它做成"always-on agent 监控异常自动开工单"的 demo 亮点（产品决策，看时间） |

---

## 10. 队友 / AI Agent 最快上手路径

### 10.1 假设角色是"队友只看这个 SSD 第一次接触"

1. **5 分钟读懂全局**：本文件 §0 + §1 + §8（依赖图）
2. **10 分钟读懂部署**：`ON_SITE_PLAYBOOK.md` 的 Phase 1-6
3. **15 分钟看 demo 数据**：
   ```bash
   sqlite3 mock_data/analytics_agent/company.db < <(echo '.schema')
   sqlite3 mock_data/analytics_agent/company.db "SELECT * FROM products;"
   cat mock_data/ops_agent/internal_tools_openapi.json | jq '.paths | keys'
   cat mock_data/analytics_agent/data_dictionary.md   # 8 个示范问题
   ```
4. **跑通本地**（不需要 GB10，先在 Mac 上）：用 LM Studio / Ollama 暴露 `:8000`，把 playbook 里 `agent.py` 的 `MODEL = "/model"` 改成 LM Studio 给的模型名 → 跑通整条链路

### 10.2 假设角色是"AI agent 帮我写代码"

可以把这份清单 + `ON_SITE_PLAYBOOK.md` 喂给 Claude / ChatGPT，要求它：

- **任务 A**：照 `internal_tools_openapi.json` 写 FastAPI mock server，监听 `:8088`，5 个 endpoint 各返回合理假数据。
- **任务 B**：基于 playbook §6.2 的 agent.py 骨架扩展，加入：
  - RAG：用 bge-large 向量化 ops_agent 下 3 个 markdown 文档，存 faiss
  - 决策路由：让 LLM 自己选 RAG / Text-to-SQL / tool calling
  - Gradio 前端：1 个聊天框 + 调用历史可视化
- **任务 C**：写一份 **demo 脚本**（不是代码，是台本）—— 列出 3-5 个会演示的提问，每个标注预期 agent 行为 + 标准答案。

### 10.3 三件最值得"出发前在 Mac 上预先做"的事

| # | 任务 | 收益 | 时间 |
|---|---|---|---|
| 1 | 写 OpenAPI mock server (`mock_server.py`) 存到 SSD | 现场少写 30 行 + 早一步整链路测试 | 15 分钟 |
| 2 | 用 Ollama/LM Studio 在 Mac 上跑通 agent.py | 验证 RAG/SQL/tool 全链路；现场零意外 | 30-60 分钟 |
| 3 | 录一段 demo 视频（Mac 上 mock 推理也行） | 现场炸了能放视频讲思路保命 | 20 分钟 |

---

## 11. 命令速查（直接拷）

```bash
# 挂 SSD
sudo mount -t exfat /dev/sda1 /mnt/ssd

# 完整性校验
cd /mnt/ssd/Hackathon && shasum -a 256 -c SHA256SUMS.txt

# 看模型架构
python3 -c "import json; print(json.dumps(json.load(open('/mnt/ssd/Hackathon/models/nemotron-3-super-120b-nvfp4/config.json')), indent=2))" | head -50

# 看 docker 镜像清单
ls -lh /mnt/ssd/Hackathon/images/*.tar.gz

# 看 company.db
sqlite3 /mnt/ssd/Hackathon/mock_data/analytics_agent/company.db ".tables"
sqlite3 /mnt/ssd/Hackathon/mock_data/analytics_agent/company.db ".schema orders"

# 看 OpenAPI 工具列表
python3 -c "import json; d=json.load(open('/mnt/ssd/Hackathon/mock_data/ops_agent/internal_tools_openapi.json')); [print(m,p,s.get('operationId')) for p,ms in d['paths'].items() for m,s in ms.items()]"

# 看 wheels 数量
ls /mnt/ssd/Hackathon/wheels/app | wc -l
ls /mnt/ssd/Hackathon/wheels/openshell | wc -l
```

---

## 一句话总结

**137 GB 自包含离线包，能让一个 GB10 在没网/限网情况下从开机到运行起本地 agent 完整 demo。核心设计：agent 永远对 `:8000` 说话，后端可随时换。**
