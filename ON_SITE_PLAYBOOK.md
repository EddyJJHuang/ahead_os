# GB10 现场部署 Playbook
> Dell × NVIDIA "Local AI on Dell Pro Max with GB10" Hackathon
> 适用环境：Dell Pro Max (DGX Spark / GB10, ARM aarch64, Blackwell sm_121, 128 GB 统一内存, DGX OS 7 / Ubuntu 24.04)
> 配套：本 SSD `/mnt/ssd/Hackathon/` 离线包

---

## 黄金原则（任何时候反复念）

1. **先让一个本地模型在 `:8000` 上能 `curl` 通，再叠任何 agent / NemoClaw / OpenShell。** 不要全栈起一把梭。
2. **Agent 永远对着 `http://localhost:8000/v1` 说话。** 后端可换（120B / 30B / vLLM / llama.cpp / 云端），agent 代码一行不动。
3. **瓶颈是 ~273 GB/s 带宽，不是显存。** 模型越小、量化越狠（NVFP4 > FP8 > Q4），decode 越快。
4. **任何步骤超过 5 分钟没动静**，就停下来看日志，不要傻等。

---

## 时间预算（理想路径）

| Phase | 内容 | 估时 |
|---|---|---|
| 1 | 硬件验证 | 10 min |
| 2 | SSD 挂载 + 校验 | 10 min |
| 3 | 拷贝到本机 NVMe | 15-25 min |
| 4 | docker load + pip 离线装 | 10 min |
| 5 | **首次 `:8000` 跑通**（里程碑） | 10-20 min |
| 6 | 接 mock_data + agent | 剩余时间 |

理想情况：**90 分钟以内拿到能 demo 的本地模型**。

---

## 抗灾 Cheat Sheet（**打印贴在电脑边**）

```
L0  vLLM 120B NVFP4  (NGC image)         ← 理想
L1  vLLM 120B NVFP4  (avarok image)      ← NGC 镜像不兼容时
L2  vLLM 30B  FP8                         ← 120B OOM / 太慢时
L3  llama.cpp:server-cuda (docker)        ← 两个 vLLM 都败
L4  llama.cpp 现场源码编译                ← Docker GPU 出问题
L5  build.nvidia.com 云端                 ← 全废 + 现场有网 + 规则允许
```

**每往下一级，先确认 :8000 通了再切。** 不要在一级上死磕超过 15 分钟。

---

# Phase 1 — 抵达 + 硬件验证

> 目标：确认拿到的是真 GB10，Docker 能用 GPU。

```bash
# 1. 开机、登录、桌面就绪
# 2. 硬件核对（任何一项 ❌ 都先停下找主办方）
uname -m              # 必须 aarch64
nvidia-smi            # 必须能看到 Blackwell GPU
free -h               # 应当 ~128 GB 总内存
df -h $HOME           # 本机 NVMe 至少 200 GB 空余

# 3. Docker 守护进程
docker info >/dev/null && echo "docker OK" || echo "docker NOT READY"

# 4. 容器能不能看到 GPU（NVIDIA Container Toolkit 正常吗）
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi 2>&1 | head -20
# 看到 GPU 表 = OK；报 unknown runtime 等 → 找主办方配 toolkit

# 5. 网络情况（决定要不要走云端兜底）
ping -c 2 1.1.1.1 && echo "online" || echo "offline"
```

**任何步骤红了**：不要往下走，先解决。SSD 还没插。

---

# Phase 2 — 挂载 SSD + 完整性校验

> 目标：确认 SSD 在传输/存放过程中没损坏。

```bash
# 1. 插 SSD，找到设备名
lsblk
# 假设是 /dev/sda1（exFAT）。挂载到 /mnt/ssd：
sudo mkdir -p /mnt/ssd
sudo mount -t exfat /dev/sda1 /mnt/ssd
ls /mnt/ssd/Hackathon

# 1.1 如果 mount 报 "unknown filesystem type 'exfat'"：
#     DGX OS 7 默认带 exfat；若真的没有：
#     sudo apt-get install -y exfat-fuse exfatprogs
#     需要本地包或临时联网

# 2. 跳到 SSD 根目录
cd /mnt/ssd/Hackathon

# 3. SHA-256 校验（约 5 分钟读完 ~125 GB）
shasum -a 256 -c SHA256SUMS.txt
# 期望 32 行全部 ": OK"。任何 FAILED 都要查那个文件、必要时从 Mac 重拷。

# 4. 顶层目录扫一眼，记下你看到什么
ls -la /mnt/ssd/Hackathon/
du -sh /mnt/ssd/Hackathon/*/
```

预期看到：
```
bin/        (~24 MB)     uv 二进制
images/     (~19 GB)     4 个 docker 镜像 tar.gz + PINNED_DIGESTS.txt
models/     (~109 GB)    3 个模型目录
mock_data/  (~3 MB)      RAG + Text-to-SQL 沙盒
repos/      (~7.9 GB)    源码仓库（exFAT 可能丢符号链接）
repos.tar.gz (~583 MB)   源码 tar 备份 ★ 优先用这个
wheels/     (~543 MB)    Python wheels
download/                离线下载脚本（仅作参考）
RUNBOOK.md               原版 runbook
ON_SITE_PLAYBOOK.md      本文件
SHA256SUMS.txt
MANIFEST.txt
```

---

# Phase 3 — 拷贝大文件到本机 NVMe

> **为什么**：USB-C 上的 SSD 读速远低于本机 NVMe，模型每次启动要全文件扫一遍。多花 20 分钟拷，省后续每次启动 5+ 分钟。

```bash
# 1. 工作目录
WORK=$HOME/hack
mkdir -p $WORK && cd $WORK

# 2. 模型权重（必拷，~109 GB，最耗时）
cp -r /mnt/ssd/Hackathon/models .

# 3. 镜像 tar（必拷，~19 GB；docker load 读 SSD 慢）
cp -r /mnt/ssd/Hackathon/images .

# 4. 源码仓库——用 tar.gz 而不是 repos/，避免 exFAT 把 .git 里的符号链接丢了
cp /mnt/ssd/Hackathon/repos.tar.gz .
tar -xzf repos.tar.gz
# 解到 $WORK/repos/{NemoClaw, OpenShell, Nemotron-cookbook, llama.cpp}

# 5. Wheels（小，直接挂着用也行，但拷一份省得 SSD 拔了断）
cp -r /mnt/ssd/Hackathon/wheels .

# 6. Mock data（小）
cp -r /mnt/ssd/Hackathon/mock_data .

# 7. 不要拷的：bin/（22 MB，用一次就够）

# 8. 验证空间
df -h $HOME
du -sh $WORK
```

---

# Phase 4 — 装载镜像 + 装 Python 依赖

> 目标：四个 docker 镜像在本机能 `docker images` 看见；venv 里有 fastapi/openai/faiss 等。

```bash
cd $WORK

# 1. docker load 全部 4 个镜像（~5 分钟）
for t in images/*.tar.gz; do
  echo "==> loading $t..."
  gunzip -c "$t" | docker load
done

# 2. 列出装载后的真实镜像名（这是你 docker run 时要用的）
docker images
# 期望看到：
#   nvcr.io/nvidia/vllm                26.01-py3
#   avarok/vllm-dgx-spark              latest
#   ghcr.io/nvidia/openshell/gateway   latest
#   ghcr.io/ggml-org/llama.cpp         server-cuda

# 3. 验证每个镜像都是 arm64
for img in $(docker images --format '{{.Repository}}:{{.Tag}}' | grep -v '<none>'); do
  arch=$(docker image inspect "$img" --format '{{.Architecture}}')
  echo "  $img → $arch"
done
# 任何一个 != arm64：弃用那个镜像

# 4. 对照 SSD 上的 digest（可选，但能确认没串包）
cat /mnt/ssd/Hackathon/images/PINNED_DIGESTS.txt

# 5. 装 uv（OpenShell 后续要用）
tar -C /tmp -xzf /mnt/ssd/Hackathon/bin/uv-aarch64-unknown-linux-gnu.tar.gz
sudo install /tmp/uv*/uv /usr/local/bin/uv
uv --version

# 6. Python venv + 离线装 app 依赖
python3.12 -m venv .venv
source .venv/bin/activate
pip install --no-index --find-links wheels/app -r /mnt/ssd/Hackathon/download/requirements.app.txt
# 验证关键包能 import
python -c "import openai, fastapi, faiss, gradio, sqlalchemy, duckdb; print('app deps OK')"

# 7. 离线装 openshell（如果要走 NemoClaw 全栈）
pip install --no-index --find-links wheels/openshell openshell
python -c "import openshell; print('openshell OK')"
```

**如果 pip 报某个 wheel "not a supported wheel on this platform"**：你的 wheels 是 manylinux_2_39_aarch64，DGX OS 7 是 glibc 2.39，应当兼容。如果真的撞了：
```bash
pip install --no-index --find-links wheels/app --no-deps <报错包名>
# 或先临时联网装这一个：pip install <包名>
```

---

# Phase 5 — 首次 `:8000` 跑通（**里程碑**）

> **任何路径里 `curl localhost:8000/v1/models` 能返回模型 ID 就算通。**
> **不通就立刻往下降一级，不要死磕。**

## L0：vLLM 120B NVFP4 + NGC 镜像（理想路径）

```bash
# 0. 先清除可能存在的旧容器
docker rm -f vllm 2>/dev/null

# 1. 启动
docker run -d --name vllm --gpus all --shm-size=16gb --network host \
  -v $WORK/models/nemotron-3-super-120b-nvfp4:/model \
  -e VLLM_USE_FLASHINFER_MOE_FP4=1 \
  -e VLLM_FLASHINFER_MOE_BACKEND=latency \
  -e VLLM_MOE_PADDING_SIZE=512 \
  nvcr.io/nvidia/vllm:26.01-py3 \
  vllm serve /model \
    --served-model-name nemotron-super \
    --quantization nvfp4 \
    --tensor-parallel-size 1 \
    --kv-cache-dtype fp8 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.85 \
    --trust-remote-code \
    --mamba-backend triton \
    --mamba-ssm-cache-dtype float32 \
    --reasoning-parser nemotron_v3 \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder
# ⚠️ parser 名字（nemotron_v3、qwen3_coder）务必在 dry-run 里验过再用！
# 如果启动后 docker logs 报 "unknown parser xxx"，先去掉那两行起来再调。
# 可选提速 flag（语法各 vLLM 版本不一样，没 dry-run 验证前别加）：
#   --speculative_config.method mtp --speculative_config.num_speculative_tokens 5
#   --async-scheduling  --enable-flashinfer-autotune

# 2. 看日志，等到 "Application startup complete"（约 60-180 秒）
docker logs -f vllm
# 看到这行就 Ctrl-C 退出 logs，然后：

# 3. 验证（另开终端 / 同一终端用 & 退到背景再 curl）
curl -s http://localhost:8000/v1/models | python3 -m json.tool

curl -s http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "nemotron-super",
    "messages": [{"role": "user", "content": "Say hi in 5 words."}],
    "max_tokens": 32
  }' | python3 -m json.tool
```

### 进阶验证（Phase 6 前必须通过）

**只验证"会说话"是远远不够的**——agent 链路依赖工具调用和推理分离，必须实测：

```bash
# (a) 工具调用是否真的触发：返回里要有 tool_calls 字段
curl -s http://localhost:8000/v1/chat/completions -H 'Content-Type: application/json' -d '{
  "model": "nemotron-super",
  "messages": [{"role":"user","content":"Look up the employee alice@meridian.com"}],
  "tools": [{"type":"function","function":{
    "name":"lookup_employee","description":"Look up an employee by email",
    "parameters":{"type":"object","properties":{"email":{"type":"string"}},"required":["email"]}}}],
  "tool_choice":"auto","max_tokens":256
}' | python3 -m json.tool
# ✅ 期望：choices[0].message.tool_calls 非 null
# ❌ 失败：tool_calls 为 null 或模型把调用写到 content 里 → --tool-call-parser 没生效
#    立刻去掉 --tool-call-parser 那行重启，或换 parser 名（hermes / llama3_json / ...）

# (b) 推理是否被分离干净：reasoning_content 有内容，content 是干净答案
curl -s http://localhost:8000/v1/chat/completions -H 'Content-Type: application/json' -d '{
  "model":"nemotron-super",
  "messages":[{"role":"user","content":"What is 17*23? Output only the number."}],
  "max_tokens":256
}' | python3 -m json.tool
# ✅ 期望：message.content ≈ "391"（不含 <think>）；思考过程在 message.reasoning_content
# ❌ 失败：content 里出现 <think>...</think> → --reasoning-parser 没生效，换名或暂时不用 parser、
#    在 agent 端用正则剥离（见 §6.2 的 _extract_sql 模式）
```

**这两条任一不对，就别往 Phase 6 走** —— 工具链废了再写 agent 是浪费时间。

**flag 解释**：
- `VLLM_USE_FLASHINFER_MOE_FP4=1`：启用 FlashInfer 的 MoE FP4 后端（Nemotron 3 Super 是 LatentMoE）
- `--served-model-name nemotron-super`：对外暴露的模型 ID（不写就是 `/model`）。agent 里要对齐
- `--quantization nvfp4`：告诉 vLLM 这是 NVFP4 量化权重
- `--tensor-parallel-size 1`：单卡，**不要**改成 >1（GB10 只有一颗 GPU）
- `--max-model-len 4096`：上下文窗口；起不来就降到 2048
- `--gpu-memory-utilization 0.85`：留 15% 给系统/Docker；别贪到 0.95
- `--kv-cache-dtype fp8`：KV cache 也压成 fp8，省 ~50% 内存
- `--mamba-backend triton` + `--mamba-ssm-cache-dtype float32`：Nemotron-H 是 **Mamba+Transformer 混合**架构，不加 mamba 后端可能起不来
- `--reasoning-parser nemotron_v3`：把推理模型的 `<think>...</think>` 部分单独分出来到 `message.reasoning_content`，干净答案留在 `message.content`
- `--enable-auto-tool-choice` + `--tool-call-parser qwen3_coder`：开启工具调用解析；**不加就没 `tool_calls`，agent 工具链全废**

## L1：换 avarok 镜像（同 120B，不同引擎）

```bash
docker rm -f vllm
docker run -d --name vllm --gpus all --shm-size=16gb --network host \
  -v $WORK/models/nemotron-3-super-120b-nvfp4:/model \
  -e VLLM_USE_FLASHINFER_MOE_FP4=1 \
  -e VLLM_FLASHINFER_MOE_BACKEND=latency \
  avarok/vllm-dgx-spark:latest \
  vllm serve /model \
    --served-model-name nemotron-super \
    --quantization nvfp4 \
    --tensor-parallel-size 1 \
    --kv-cache-dtype fp8 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.85 \
    --trust-remote-code \
    --mamba-backend triton \
    --mamba-ssm-cache-dtype float32 \
    --reasoning-parser nemotron_v3 \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder
docker logs -f vllm
```

## L2：降到 30B FP8（OOM / 太慢的兜底）

```bash
docker rm -f vllm
docker run -d --name vllm --gpus all --shm-size=16gb --network host \
  -v $WORK/models/nemotron-3-nano-30b-fp8:/model \
  nvcr.io/nvidia/vllm:26.01-py3 \
  vllm serve /model \
    --served-model-name nemotron-nano \
    --tensor-parallel-size 1 \
    --kv-cache-dtype fp8 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.80 \
    --trust-remote-code \
    --mamba-backend triton \
    --mamba-ssm-cache-dtype float32 \
    --reasoning-parser nemotron_v3 \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder
docker logs -f vllm
# 注意：30B FP8 用 vLLM 自动检测的量化类型，不需要 --quantization 那一行
# 但 30B 同样是 nemotron_h（Mamba+Transformer）混合架构，mamba/reasoning/tool flag 全部照加
# 若改用 30B 当主力，把 agent.py 里 MODEL 改成 "nemotron-nano"
```

## L3：llama.cpp:server-cuda 镜像（vLLM 全废时）

```bash
docker rm -f vllm
# 注意：你 SSD 里没有 GGUF（GGUF 下载步骤跳过了）。L3 需要：
# 方案 A：现场临时联网下一个 GGUF（如果有网）
#   hf download bartowski/NVIDIA-Nemotron-3-Nano-30B-A3B-GGUF \
#       --include "*Q4_K_M*" --local-dir $WORK/models/nemotron-30b-gguf
# 方案 B：用 llama.cpp 自带 convert_hf_to_gguf 把 30B FP8 转 GGUF（约 10 分钟）
#   docker run --rm -v $WORK/models/nemotron-3-nano-30b-fp8:/in \
#       -v $WORK/models/nemotron-30b-gguf:/out \
#       ghcr.io/ggml-org/llama.cpp:server-cuda \
#       /llama.cpp/convert_hf_to_gguf.py /in --outfile /out/model-q8.gguf

docker run -d --name llama --gpus all --network host \
  -v $WORK/models/nemotron-30b-gguf:/model \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  --host 0.0.0.0 --port 8000 --no-mmap -c 4096 -ngl 999 \
  -m /model/<gguf-filename>
docker logs -f llama
```

## L4：现场源码编译 llama.cpp（最稳的兜底）

```bash
cd $WORK/repos/llama.cpp
cmake -B build -DGGML_CUDA=ON
cmake --build build -j$(nproc)
./build/bin/llama-server \
  -m <gguf 路径> \
  --host 0.0.0.0 --port 8000 \
  --no-mmap -c 4096 -ngl 999
```

## L5：云端 build.nvidia.com（最后手段，确认规则允许）

```bash
# agent 改 base_url 即可：
#   from openai import OpenAI
#   client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key="<nv_api_key>")
#   推理用 nvidia/nemotron-... 模型 ID
# 这条路径仍然让 agent 代码不动，只换端点。
```

---

# Phase 6 — 接上 mock_data + 起 agent

`:8000` 通了之后再做。

## 6.1 起 OpenAPI mock server（让 agent 能调工具）

把 `mock_data/ops_agent/internal_tools_openapi.json` 起成一个本地 FastAPI server，听 `:8088`。

> 注意：你 SSD 里目前**只有 OpenAPI 规范文件，没有可跑的 server 实现**。出发前如果有时间在 Mac 上写一份；否则现场用以下 30 行骨架快速搭：

```python
# $WORK/mock_server.py
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import json, random

app = FastAPI(title="Meridian Internal Ops Tools")

# 假数据
EMPLOYEES = {
    "alice@meridian.com": {"employee_id": "E1001", "name": "Alice", "team": "IT"},
    "bob@meridian.com":   {"employee_id": "E1002", "name": "Bob",   "team": "Eng"},
}
TICKETS = {}

class TicketIn(BaseModel):
    title: str; description: str; priority: str = "P3"; category: str = "it"

@app.get("/employees/lookup")
def lookup_employee(email: str | None = None, employee_id: str | None = None):
    if email and email in EMPLOYEES: return EMPLOYEES[email]
    return {"error": "not_found"}

@app.post("/tickets")
def create_ticket(t: TicketIn):
    tid = f"T-{random.randint(10000,99999)}"
    TICKETS[tid] = {**t.dict(), "id": tid, "status": "open", "created": datetime.utcnow().isoformat()}
    return TICKETS[tid]

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    return TICKETS.get(ticket_id, {"error": "not_found"})

@app.post("/pto/request")
def request_pto(employee_id: str, start: str, end: str):
    return {"status": "submitted", "approver": "manager@meridian.com"}

@app.post("/password/reset")
def reset_password(employee_id: str):
    return {"status": "reset_email_sent"}

# uvicorn mock_server:app --host 0.0.0.0 --port 8088
```

启动：
```bash
cd $WORK
source .venv/bin/activate
uvicorn mock_server:app --host 0.0.0.0 --port 8088 &
curl http://localhost:8088/employees/lookup?email=alice@meridian.com
```

## 6.2 Agent 骨架（最小可演示版）

OpenAI 客户端 → `:8000` 本地 vLLM → 同时能 RAG / Text-to-SQL / tool calling。

```python
# $WORK/agent.py
import os, sqlite3, json, re
import requests
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="not-needed")
# 必须和 vLLM 启动时的 --served-model-name 对齐
# 不确定时跑：curl http://localhost:8000/v1/models | python3 -m json.tool
MODEL = "nemotron-super"   # L2 切 30B 时改成 "nemotron-nano"

# ---- Text-to-SQL ----
DB = sqlite3.connect("/mnt/ssd/Hackathon/mock_data/analytics_agent/company.db")

SCHEMA = """
Tables: regions, sales_reps, customers, products, orders, order_items, support_tickets.
Revenue = SUM(order_items.quantity * order_items.unit_price) for orders.status='completed'.
"""

def _extract_sql(text: str) -> str:
    """推理模型会吐 <think>...</think> 和 ```sql 围栏；用正则稳健提取。"""
    # 1) 优先抓 ```sql ... ``` 围栏
    m = re.search(r"```(?:sql)?\s*(.+?)```", text, re.S | re.I)
    if m:
        return m.group(1).strip().rstrip(";")
    # 2) 没围栏就从 SELECT/WITH 开始取
    m = re.search(r"\b(SELECT|WITH)\b.+", text, re.S | re.I)
    if m:
        return m.group(0).strip().rstrip(";")
    # 3) 兜底原文清理
    return text.strip().strip("`").rstrip(";")

def text_to_sql(question: str) -> str:
    msg = [
        {"role": "system", "content": f"You write SQLite SQL. Schema:\n{SCHEMA}\nOutput ONLY SQL, no prose."},
        {"role": "user", "content": question},
    ]
    r = client.chat.completions.create(model=MODEL, messages=msg, max_tokens=400)
    raw = r.choices[0].message.content or ""
    sql = _extract_sql(raw)
    cur = DB.execute(sql)
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    return json.dumps({"sql": sql, "columns": cols, "rows": rows[:20]}, indent=2)

# ---- Tool calling ----
TOOLS = [
    {"type": "function", "function": {
        "name": "lookup_employee",
        "description": "Look up an employee by email",
        "parameters": {"type": "object", "properties": {"email": {"type": "string"}}, "required": ["email"]}
    }},
    {"type": "function", "function": {
        "name": "create_ticket",
        "description": "Create an IT/HR ticket",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "description": {"type": "string"},
            "priority": {"type": "string"}, "category": {"type": "string"}
        }, "required": ["title", "description"]}
    }},
]

def call_tool(name: str, args: dict):
    if name == "lookup_employee":
        return requests.get("http://localhost:8088/employees/lookup", params=args).json()
    if name == "create_ticket":
        return requests.post("http://localhost:8088/tickets", json=args).json()
    return {"error": f"unknown tool {name}"}

def _try_parse_inline_tool(content: str):
    """ReAct 降落伞：vLLM 的 tool parser 不触发时，模型有时会把工具调用以 JSON
    形式写在 content 里。这里尝试解析 {'tool':..,'args':..} 或 {'name':..,'arguments':..}。"""
    if not content:
        return None
    m = re.search(r"\{[^{}]*(?:\"tool\"|\"name\")\s*:[^{}]*\}", content, re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        name = obj.get("tool") or obj.get("name")
        args = obj.get("args") or obj.get("arguments") or {}
        if isinstance(args, str):
            args = json.loads(args)
        return name, args
    except Exception:
        return None

def chat_with_tools(question: str):
    messages = [{"role": "user", "content": question}]
    for _ in range(5):  # max 5 tool rounds
        r = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, max_tokens=400)
        msg = r.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        # 原生路径：vLLM parser 正确解出 tool_calls
        if msg.tool_calls:
            for tc in msg.tool_calls:
                result = call_tool(tc.function.name, json.loads(tc.function.arguments))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
            continue

        # ReAct 降落伞：parser 没生效时，从 content 里抠 JSON
        inline = _try_parse_inline_tool(msg.content or "")
        if inline:
            name, args = inline
            result = call_tool(name, args)
            # 用 user role 把结果回传给模型继续
            messages.append({"role": "user", "content": f"Tool {name} result: {json.dumps(result)}"})
            continue

        # 真正没工具调用 → 返回最终答案
        return msg.content

    return "[exceeded tool rounds]"

# ---- 用法 ----
if __name__ == "__main__":
    print(text_to_sql("What was total completed revenue by product category in 2025?"))
    print(chat_with_tools("My VPN is broken, error VPN-503. My email is alice@meridian.com. Please file a P2 ticket."))
```

**关键点**：
- `MODEL` 必须和 vLLM `--served-model-name` 一致；切到 30B 时改成 `"nemotron-nano"`
- `_extract_sql` 处理推理模型的 `<think>` 和 ` ```sql ``` ` 围栏
- `_try_parse_inline_tool` 是降落伞——当 vLLM 的 `--tool-call-parser` 在 sm_121 上不触发时，从 `content` 里抠出工具调用 JSON，让 demo 不至于全废
- `requests` **已在 `wheels/app/`**（2.34.2），不用换 httpx

测试：
```bash
cd $WORK
source .venv/bin/activate
python agent.py
```

## 6.3 RAG（可选 / 加分项）

> ⚠️ **不要装 sentence-transformers**——它会把 torch 拉进来，跟 vLLM 镜像里的 CUDA 撞、且 arm64 torch 是大坑。
> 你的 SSD 里 `bge-large-en-v1.5/onnx/` 子目录有 ONNX 版本，`wheels/app/` 里有 `onnxruntime` 和 `chromadb`，**完整无 torch 路径**。

### 方案 A：chromadb 内置 ONNX 嵌入（最快）

```python
# $WORK/rag.py
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
import os

# chromadb 自带的 ONNX 嵌入函数（会用本地 onnxruntime；首次需要联网下小模型）
# 若现场无网或不想用默认，跳到方案 B
ef = embedding_functions.DefaultEmbeddingFunction()

client = chromadb.PersistentClient(path=f"{os.environ['HOME']}/hack/chroma_db")
coll = client.get_or_create_collection("ops_docs", embedding_function=ef)

docs_dir = Path("/mnt/ssd/Hackathon/mock_data/ops_agent")
for md in docs_dir.glob("*.md"):
    text = md.read_text()
    # 简单按段落切；要更细可用 langchain.text_splitter
    chunks = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 50]
    coll.add(
        documents=chunks,
        ids=[f"{md.stem}-{i}" for i in range(len(chunks))],
        metadatas=[{"source": md.name} for _ in chunks],
    )

results = coll.query(query_texts=["how do I reset my VPN if I get error VPN-503"], n_results=3)
for d, m in zip(results['documents'][0], results['metadatas'][0]):
    print(f"[{m['source']}]\n{d}\n---")
```

### 方案 B：直接用本地 bge ONNX（**完全无网**）

```python
# $WORK/rag_local.py
import onnxruntime as ort
import numpy as np
from tokenizers import Tokenizer
import faiss, json
from pathlib import Path

BGE = Path("/mnt/ssd/Hackathon/models/bge-large-en-v1.5")
# bge 目录有 onnx/ 子目录，里面有 model.onnx（或 model_quantized.onnx）
onnx_path = next((BGE / "onnx").glob("model*.onnx"))
tok = Tokenizer.from_file(str(BGE / "tokenizer.json"))
sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])

def embed(texts: list[str]) -> np.ndarray:
    encs = [tok.encode(t) for t in texts]
    max_len = max(len(e.ids) for e in encs)
    input_ids = np.zeros((len(encs), max_len), dtype=np.int64)
    attn_mask = np.zeros((len(encs), max_len), dtype=np.int64)
    for i, e in enumerate(encs):
        input_ids[i, :len(e.ids)] = e.ids
        attn_mask[i, :len(e.ids)] = 1
    out = sess.run(None, {"input_ids": input_ids, "attention_mask": attn_mask})
    # bge 的 sentence embedding = last hidden state 的 [CLS] token (index 0)
    cls = out[0][:, 0, :]
    # L2 归一化
    return cls / np.linalg.norm(cls, axis=1, keepdims=True)

# 建索引
docs_dir = Path("/mnt/ssd/Hackathon/mock_data/ops_agent")
chunks, meta = [], []
for md in docs_dir.glob("*.md"):
    for i, p in enumerate(md.read_text().split("\n\n")):
        if len(p.strip()) > 50:
            chunks.append(p.strip()); meta.append({"source": md.name, "chunk": i})

vecs = embed(chunks)  # shape (N, 1024)
index = faiss.IndexFlatIP(vecs.shape[1])
index.add(vecs.astype(np.float32))

def retrieve(query: str, k: int = 3):
    qv = embed([query]).astype(np.float32)
    D, I = index.search(qv, k)
    return [(chunks[i], meta[i], float(D[0][j])) for j, i in enumerate(I[0])]

if __name__ == "__main__":
    for txt, m, score in retrieve("VPN-503 connection refused"):
        print(f"[{m['source']} #{m['chunk']}] score={score:.3f}\n{txt[:200]}\n---")
```

### 加分版：赛前预建索引并 ship 到 SSD

在 Mac 上跑一次 `rag_local.py` 的"建索引"部分，把 `faiss` 索引文件存起来：

```python
faiss.write_index(index, "/Volumes/SSD-3/Hackathon/rag_index.faiss")
with open("/Volumes/SSD-3/Hackathon/rag_chunks.json", "w") as f:
    json.dump({"chunks": chunks, "meta": meta}, f)
```

现场只需 `faiss.read_index(...)` 就能立刻检索，**零嵌入计算**。

---

# Phase 7（可选）— NemoClaw + OpenShell 全栈

> **仅在 Phase 5+6 都跑通后再尝试。** 否则风险无回报。

```bash
cd $WORK/repos/NemoClaw

# 1. 读 air-gapped install 说明（必须）
cat README.md | less
ls docs/ 2>/dev/null
# 找 "offline" / "air-gapped" 章节

# 2. 离线 install（如果有 air-gapped 文档就按它来）
./install.sh
# 注意：它默认可能联网拉东西；监控这一步，遇到 PyPI/HF/npm 拉失败：
# - 改 inference provider 为 local（见步骤 3）
# - 网络策略改本地白名单（见步骤 4）

# 3. onboard 时
nemoclaw onboard
# - inference provider 选 "local / vLLM"
# - endpoint 填 http://localhost:8000/v1
# - 网络策略选最严档

# 4. 网络策略：只放行本地推理 + mock server（热加载）
openshell policy set --allow localhost:8000,localhost:8088

# 5. 健康检查
nemoclaw <name> status
openshell sandbox list
docker exec -it <sandbox> openclaw agent --agent main --local -m "hello" --session-id test
```

**如果 install.sh 在 air-gapped 下失败**：跳过全栈，回到 Phase 6 的 L1 路径——你的 agent 直连 `:8000`，依然是本地推理、依然能完整 demo。

---

# 内存 / OOM 管理（128 GB 统一内存）

| 信号 | 处理 |
|---|---|
| vLLM 启动到 "Loading KV cache" 突然 kill | OOM。降 `--max-model-len` 4096→2048 |
| `CUDA out of memory` 明确报错 | 降 `--gpu-memory-utilization` 0.85→0.75 |
| Embedding 想另起一个 torch 服务 | **别**。让 vLLM 自己 serve embedding（同一镜像，加 --task embedding 起第二个端口） |
| Agent 卡顿明显 | 后台 `watch -n1 nvidia-smi` 看是不是 GPU mem 满了 |

省内存优先级：
1. 降 `--max-model-len`（4096→2048）
2. 已经 `--kv-cache-dtype fp8`（默认开了）
3. 降 `--gpu-memory-utilization`（0.85→0.75）
4. 换 30B（L2）
5. 关掉同时跑的第二个模型 / embedding 服务

---

# 常见错误速查表

| 报错 | 根因 | 处理 |
|---|---|---|
| `exec format error` | 拉到 x86 镜像 | 确认是 `--platform linux/arm64`；换另一个镜像 |
| `no kernel image is available` | vLLM 不是 sm_121 build | L0→L1 换 avarok；都不行 → L3 llama.cpp |
| `CUDA out of memory` | KV cache / 模型放不下 | 见上面"内存/OOM" |
| `Address already in use :8000` | 上一个容器没清 | `docker rm -f vllm llama` 或 `lsof -i :8000` 杀 |
| 镜像 load 后 docker run 直接退出 | 启动参数错 | `docker logs vllm` 看具体行 |
| `pip install` 报 not a supported wheel | wheel 平台不匹配 | 你的 wheels 是 manylinux_2_39_aarch64；如果真碰到 → `--no-deps` 试 |
| HF 401/403 | gated 模型没在网页同意 | 这步出发前就做完了，不应该遇到 |
| Privacy Router 把请求发到云端 | NemoClaw inference 配错 | 改 local，endpoint=`http://localhost:8000/v1` |
| openclaw 沙盒连不上 `:8000` | OpenShell 网络策略没放行 | `openshell policy set --allow localhost:8000` |
| llama.cpp 加载极慢 | 用了 mmap 从慢盘读 | 加 `--no-mmap`，且模型放本机 NVMe 不要放 SSD |
| `message.tool_calls` 恒为 null / 模型把工具调用写到 `content` 里 | 没加 `--enable-auto-tool-choice` 或 `--tool-call-parser` 不对 | 确认两个 flag；换 parser 名（qwen3_coder / hermes / llama3_json）；最后退到 ReAct 自解析（见 §6.2 `_try_parse_inline_tool`） |
| 120B NVFP4 加载即崩 / 报 quantization 相关错 | vLLM 镜像内版本对 sm_121 不兼容 NVFP4 | `docker exec vllm vllm --version` 看版本；社区报 0.18.x 在 sm_121 上挂，可能需要 pin 0.17.2rc1，或换 avarok 镜像（L1） |
| SQL/答案里混进 `<think>...</think>` 或大段解释 | 没加 `--reasoning-parser nemotron_v3` / 该 parser 不存在 | 加 flag；起不来就去掉，在 agent 端用 `_extract_sql` 正则剥离 |

---

# 紧急恢复（断电 / 死机 / 全清重来）

```bash
# 1. 关掉所有跑的 docker
docker ps -q | xargs -r docker rm -f

# 2. 清掉占用 8000/8088 端口的进程
sudo lsof -i :8000 -i :8088 | awk 'NR>1 {print $2}' | xargs -r sudo kill -9

# 3. 重启 docker（如果需要）
sudo systemctl restart docker

# 4. 重新走 Phase 5 L0 / L1 / L2
```

---

# Demo 当天保命

1. **提前录视频**：手机录屏一遍完整 demo，万一现场炸了先放视频讲思路。
2. **3-5 张截图/图**：架构图、降级阶梯、内存占用、一次成功的 agent 调用日志。
3. **固定脚本**：用 `data_dictionary.md` 里的 8 个示例问题中的 2-3 个，不要现场即兴出题。
4. **冷启动一次**：开赛前完整跑一遍 Phase 1-6，记录每段耗时，避免上台慌。
5. **最小可演示版**：哪怕只有 Phase 6 的 L1 + Text-to-SQL + tool calling 跑通，就是一个完整故事。

---

# 命令速查卡（贴在屏幕边）

```bash
# 系统
uname -m ; nvidia-smi ; docker info ; free -h

# SSD
sudo mount -t exfat /dev/sda1 /mnt/ssd ; cd /mnt/ssd/Hackathon
shasum -a 256 -c SHA256SUMS.txt

# Docker
docker load < img.tar.gz                    # 或 gunzip -c img.tar.gz | docker load
docker images                                # 看名字
docker ps                                    # 看跑的
docker logs -f vllm
docker rm -f vllm

# Python
source $HOME/hack/.venv/bin/activate
pip install --no-index --find-links wheels/app -r requirements.app.txt

# vLLM 验证
curl http://localhost:8000/v1/models
curl http://localhost:8000/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"/model","messages":[{"role":"user","content":"hi"}],"max_tokens":16}'

# 监控
watch -n1 nvidia-smi
docker stats vllm
```

---

# 关键文件位置（**SSD 上**）

```
/mnt/ssd/Hackathon/
├── ON_SITE_PLAYBOOK.md         ← 本文件
├── RUNBOOK.md                  ← 原版 runbook（更详细的背景）
├── README.md                   ← 全局说明
├── SHA256SUMS.txt              ← Phase 2 校验用
├── MANIFEST.txt                ← 内容清单
├── bin/uv-aarch64-...tar.gz    ← uv binary
├── images/*.tar.gz             ← Phase 4 docker load 用
├── images/PINNED_DIGESTS.txt   ← 镜像 digest 对照
├── models/*                    ← Phase 3 拷到本机
├── repos.tar.gz                ← Phase 3 解到 $WORK/repos/
├── wheels/app/                 ← Phase 4 pip --no-index 用
├── wheels/openshell/           ← OpenShell 离线装
├── mock_data/ops_agent/        ← Phase 6 RAG + tool calling 数据
├── mock_data/analytics_agent/  ← Phase 6 Text-to-SQL 数据
└── download/                   ← 下载脚本（仅作参考，现场不用跑）
```

---

# 一句话总结

**先 `:8000` 通，再叠沙盒；带宽是瓶颈不是显存；一切对着 OpenAI 端点说话，后端随时可降级。**
