# GB10 黑客松 现场 RUNBOOK 与应急预案

> 离线携带版。出发前打印或存进 SSD。所有命令以单台 Dell Pro Max / DGX Spark(GB10,128GB 统一内存,ARM,sm_121,DGX OS 7 / Ubuntu 24.04)为准。
>
> **黄金原则:先用最稳的路径把"一个本地模型能回话"跑通,再往上叠 NemoClaw/OpenShell。不要一上来就全栈。**

---

## 目录
1. 抵达后 30 分钟开机清单
2. 把离线包落地(docker load / 装 wheel)
3. 推理路径:本地 vs 云端(必须先决定)
4. 启动 vLLM(主路径)
5. llama.cpp(兜底路径,最稳)
6. 接上 NemoClaw + OpenShell
7. 网络策略(离线必改)
8. 内存 / OOM 管理(128GB 统一内存)
9. 常见报错速查表
10. 应急"降级阶梯"(出问题时按这个顺序退)
11. Demo 当天保命预案
12. 命令速查卡

---

## 1. 抵达后 30 分钟开机清单
- [ ] 开机、建本地账户、登录。**先别急着联网**——先确认现场是否提供网络以及是否允许联网(这决定走离线还是在线)。
- [ ] `uname -m` → 应为 `aarch64`。`nvidia-smi` → 能看到 Blackwell GPU 和 128GB 显存。
- [ ] `docker info` → 确认 Docker 在运行;`docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi` 验证 **容器内能看到 GPU**(NVIDIA Container Toolkit 正常)。DGX OS 一般已自带。
- [ ] 插 SSD,挂载:`lsblk` 找到设备 → `sudo mount /dev/sdX1 /mnt/ssd`(exFAT 一般免驱;若不识别 `sudo apt-get install -y exfat-fuse exfatprogs`,但这需要网/本地包)。
- [ ] `df -h` 确认本机 NVMe 有空间。**把大文件从 SSD 拷到本机 NVMe** 再用(SSD 直接读会拖慢加载)。
- [ ] 校验:`cd /mnt/ssd/... && shasum -a 256 -c SHA256SUMS.txt`。

**如果现场有网**:最省事的是直接联网,让 DGX OS 自更新,然后正常 `./install.sh`;离线包当作"网慢/掉线"的保险。**如果现场无网/限网**:走下面的离线流程。

---

## 2. 把离线包落地
```bash
SSD=/mnt/ssd/gb10-offline
WORK=$HOME/hack         # 放本机 NVMe
mkdir -p $WORK && cd $WORK

# 模型拷到本机(加载更快)
cp -r $SSD/models .

# 载入所有镜像
for t in $SSD/images/*.tar.gz; do echo "load $t"; gunzip -c "$t" | docker load; done
docker images   # 记下真实 image 名:tag

# 解开仓库(若打过 tar)
tar -C $WORK -xzf $SSD/repos.tar.gz 2>/dev/null || cp -r $SSD/repos .

# 建虚拟环境 + 离线装 app 依赖
python3 -m venv .venv && source .venv/bin/activate
pip install --no-index --find-links $SSD/wheels/app -r $SSD/download/requirements.app.txt

# 装 uv(供 OpenShell)
tar -C /tmp -xzf $SSD/bin/uv-aarch64-unknown-linux-gnu.tar.gz
sudo install /tmp/uv*/uv /usr/local/bin/uv && uv --version
```

---

## 3. 推理路径:本地 vs 云端(必须先决定)
NemoClaw/OpenShell 有个 **Privacy Router**,决定推理调用走**本地 Nemotron(vLLM/llama.cpp)**还是 **NVIDIA 云端(build.nvidia.com,需 API key)**。

- **黑客松要求本地 → 必须强制走本地推理。** 把 OpenShell 的 inference provider 指向你本机起的 OpenAI 兼容端点(`http://localhost:8000/v1`),不要用默认云端路由。
- 如果现场**有网**,云端路由可作为"本地起不来时"的临时兜底,但别依赖它,且要确认评分规则是否允许。
- 不论哪条,**第一步永远是:先让一个本地模型在 `:8000` 上能 `curl` 通**,再谈 agent。

---

## 4. 启动 vLLM(主路径)

> 关键点:**单台 GB10 用 `--tensor-parallel-size 1`**(Nemotron 3 Super 是 LatentMoE,单卡不做专家并行);用 **NVFP4 量化 + FP8 KV cache** 压内存;`--max-model-len` 先开小(2048–4096),跑通再加。

```bash
docker run -d --name vllm --gpus all --shm-size=16gb --network host \
  -v $WORK/models/nemotron-3-super-120b-nvfp4:/model \
  -e VLLM_USE_FLASHINFER_MOE_FP4=1 \
  -e VLLM_FLASHINFER_MOE_BACKEND=latency \
  -e VLLM_MOE_PADDING_SIZE=512 \
  <载入后的vllm镜像名:tag> \
  vllm serve /model \
    --quantization nvfp4 \
    --tensor-parallel-size 1 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.85 \
    --kv-cache-dtype fp8 \
    --trust-remote-code

# 看日志,等 "Application startup complete"
docker logs -f vllm

# 验证(另开一个终端)
curl http://localhost:8000/v1/models
curl http://localhost:8000/v1/chat/completions -H 'Content-Type: application/json' -d '{
  "model":"/model","messages":[{"role":"user","content":"Say hi in 5 words."}],"max_tokens":32}'
```
- 起不来或太吃内存 → 先换 **30B FP8** 那个模型(`-v .../nemotron-3-nano-30b-fp8:/model`,去掉 `--quantization nvfp4`,改成它对应的量化标记)。
- `--gpu-memory-utilization` 别贪 0.95;统一内存还要留给系统、Docker、OpenShell。0.80–0.85 更稳。

---

## 5. llama.cpp(兜底路径,社区公认在 Spark 上最稳)
当 vLLM 因为 sm_121/镜像问题死活起不来时,用它。GGUF + llama.cpp 的 OpenAI 兼容 server 一样能喂给 agent。

```bash
cd $WORK/repos/llama.cpp
# 现场编译(带 CUDA);DGX OS 自带工具链
cmake -B build -DGGML_CUDA=ON && cmake --build build -j
# 起 server(--no-mmap 让加载更快;端口对齐 8000 方便切换)
./build/bin/llama-server \
  -m $WORK/models/nemotron-30b-gguf/*Q4_K_M*.gguf \
  --host 0.0.0.0 --port 8000 --no-mmap -c 4096 -ngl 999
# 同样的 /v1/chat/completions 接口
```
> 如果编译也出问题,带一个 `ghcr.io/ggml-org/llama.cpp:server-cuda` 的 arm64 镜像作为再兜底(出发前一并 `docker save`)。

---

## 6. 接上 NemoClaw + OpenShell
本地模型在 `:8000` 通了之后再做这步。
```bash
cd $WORK/repos/NemoClaw
# 若有 air-gapped 安装说明,优先按它来;否则:
./install.sh                 # 离线时它若尝试联网拉东西会失败 —— 见第10节降级
nemoclaw --help

# onboard 时:
#   - inference provider 选 "local / vLLM",endpoint 填 http://localhost:8000/v1
#   - 网络策略选最严档,然后手动放行本地(见第7节)
nemoclaw onboard

# 健康检查
nemoclaw <name> status
openshell sandbox list
docker exec -it <sandbox> openclaw agent --agent main --local -m "hello" --session-id test
```
排错分层:`nemoclaw <name> status` 看 NemoClaw 层,`openshell sandbox list` 看底层沙盒。

---

## 7. 网络策略(离线必改)
OpenShell 默认 "Balanced" 档放行 PyPI/HF/npm/GitHub/Brave 等出站。离线时这些全连不上,agent 会卡在"装包/搜索"。
- 把网络策略改成**只白名单本地推理端点**(`localhost:8000`)和你需要的本地工具端口(如 mock 工具的 `:8088`)。
- 网络/inference 段是**可热加载**的:`openshell policy set ...` 在运行中的沙盒上即可改,不用重建。
- 文件系统段在创建时锁定(默认只允许 `/sandbox` 和 `/tmp`)——确保你的 mock 数据挂进了允许的路径。

---

## 8. 内存 / OOM 管理(128GB 统一内存)
- 真正瓶颈是 **~273 GB/s 带宽**,所以模型越小、量化越狠,decode 越快。MoE(如 Nemotron Super,激活约 12B)是甜点。
- 省内存优先级:① 降 `--max-model-len`(4096→2048);② `--kv-cache-dtype fp8`;③ 降 `--gpu-memory-utilization`;④ 换 30B;⑤ 关掉同时跑的第二个模型/Embedding 服务。
- **Embedding 不要再单独装 torch**(arm 上的 torch+CUDA 是大坑)。让 Embedding 走同一个 vLLM 镜像(vLLM 能 serve embedding 模型),或用 llama.cpp 跑 GGUF embedding。
- 监控:`watch -n1 nvidia-smi`;OOM 通常表现为 vLLM 启动到加载 KV cache 时被 kill,日志里有 `CUDA out of memory` 或进程直接消失。

---

## 9. 常见报错速查表

| 现象 / 报错 | 根因 | 处理 |
|---|---|---|
| 镜像 `docker load` 后跑起来报 `no kernel image is available` / 直接退出 | vLLM 镜像不是 sm_121 build | 换另一个你带的 vLLM 镜像;再不行切 llama.cpp(第5节) |
| `exec format error` | 装了 x86 镜像/二进制 | 必须 arm64;重拉 `--platform linux/arm64` |
| `pip install` 报 `not a supported wheel on this platform` | 带成了 macOS / x86 wheel | 用第04脚本(arm64 容器)重下;`--no-index` 装 |
| HF 下载 401 / 403 | gated 模型没在网页同意 / token 无效 | 网页点 Access;`hf auth login` 换 token |
| `docker pull nvcr.io/...` 401 | 没登录 NGC | `docker login nvcr.io`,用户名 `$oauthtoken`,密码=NGC key |
| 容器里 `nvidia-smi` 没有 GPU | 漏了 `--gpus all` 或 Container Toolkit 没配 | 加 `--gpus all`;`sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker` |
| vLLM 加载到一半被 kill | KV cache OOM | 降 max-model-len / fp8 KV / 降 util / 换 30B(第8节) |
| `Address already in use :8000` | 端口被占 | `docker rm -f vllm` 或换端口,记得 agent 端点同步改 |
| `nemoclaw onboard` 卡在拉镜像/装包 | 离线但走了默认在线路径 | 见第10节;指向本地镜像/端点,网络策略改本地白名单 |
| Privacy Router 把请求发去云端 | inference provider 配成 cloud | 改成 local,endpoint=`http://localhost:8000/v1` |
| `openclaw` 在沙盒里连不上 `:8000` | 网络策略没放行本地 | `openshell policy set` 放行 localhost:8000(第7节) |
| llama.cpp 加载极慢 | 用了 mmap 从慢盘读 | 加 `--no-mmap`,且模型放本机 NVMe 不要放 SSD |

---

## 10. 应急"降级阶梯"(出问题就往下退一级,别在一级上死磕)

```
L0  全栈:NemoClaw + OpenShell 沙盒 + 本地 Nemotron 120B(vLLM)        ← 理想
 │   onboard 失败 / 沙盒起不来
L1  去掉沙盒:你的 agent 代码直接连本地 vLLM 的 OpenAI 端点(:8000)    ← 仍是本地、仍能 demo
 │   120B 起不来 / OOM
L2  换 30B FP8 在 vLLM 上                                              ← 更省内存
 │   vLLM 因 sm_121/镜像问题起不来
L3  llama.cpp + 30B GGUF(--no-mmap)                                  ← 社区最稳
 │   llama.cpp 也编译失败
L4  llama.cpp 的 arm64 server 镜像(docker load)                      ← 不依赖现场编译
 │   GPU 路径全废
L5  现场若有网:走 build.nvidia.com 云端 Nemotron(确认规则允许)      ← 最后手段
```
**核心思想:agent 永远是对着一个 OpenAI 兼容的 `:8000` 说话。** 后端是 120B/30B/vLLM/llama.cpp/云端都无所谓,换后端不用改 agent 代码——这是你最大的抗风险设计,务必这么搭。

---

## 11. Demo 当天保命预案
- **提前录一段能跑通的 demo 视频**(手机录屏即可)。评审时万一现场炸了,先放视频讲思路,再现场补。
- **准备 3–5 张截图/架构图**:数据流(RAG/Tool calling)、降级阶梯、内存占用、一次成功的 agent 调用日志。
- **把"问题→工具调用→结果"的脚本固定下来**:用 mock_data 里的固定问题(见 data_dictionary 的 8 个示例问题、OpenAPI 的固定工具),保证可复现,不要临场即兴。
- **Live Agent Gauntlet 这类要求"赛前就把 agent 准备好"**:确认你的 agent 能在断网下从冷启动跑完一条完整链路,计时一遍。
- 留一个"最小可演示版":哪怕只有 L1(agent 直连本地模型 + 一次 Text-to-SQL + 一次工具调用),也是完整故事。

---

## 12. 命令速查卡
```bash
uname -m                        # aarch64?
nvidia-smi                      # GPU + 128GB?
docker images                   # 载入后的真实镜像名
docker load < img.tar.gz        # 载入镜像(或 gunzip -c img.tar.gz | docker load)
shasum -a 256 -c SHA256SUMS.txt # 校验
# 起本地模型(主)
docker logs -f vllm
curl localhost:8000/v1/models
# 起本地模型(兜底)
./build/bin/llama-server -m model.gguf --port 8000 --no-mmap -c 4096 -ngl 999
# NemoClaw / OpenShell
nemoclaw <name> status ; openshell sandbox list ; openshell policy set ...
# 离线装 python 依赖
pip install --no-index --find-links wheels/app -r requirements.app.txt
# 监控
watch -n1 nvidia-smi
```

> 一句话总结:**先 `:8000` 通,再叠沙盒;带宽是瓶颈不是显存;一切对着 OpenAI 端点说话,后端随时可降级。**
