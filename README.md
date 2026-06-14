# GB10 黑客松离线准备包

为 Dell × NVIDIA "Local AI on Dell Pro Max with GB10" 黑客松准备。只有一台 Mac、机器现场才拿到的情况下,把所有依赖离线下到 SSD,现场直接落地。

## 目录结构
- `download/` — 在 Mac 上跑的离线下载脚本 + 图文流程
  - `00_DOWNLOAD_GUIDE.md` ← **先读这个**
  - `config.env`(只改这一个配置)
  - `01_clone_repos.sh` … `05_verify_and_manifest.sh`(按顺序跑)
  - `requirements.app.txt`(app 依赖,不含 torch/vllm)
- `mock_data/` — 两套可直接用的企业沙盒数据(RAG + Text-to-SQL + 工具调用)
  - `README_mockdata.md`、`ops_agent/`、`analytics_agent/`、`gen_mock_data.py`
- `RUNBOOK.md` — **现场 runbook 与应急降级阶梯**(离线必带)

## 三件套对应你的三个需求
1. 下载流程 → `download/`
2. 沙盒数据 → `mock_data/`
3. Runbook/应急 → `RUNBOOK.md`

## 最重要的三句话
1. GB10 是 **ARM(aarch64)+ sm_121**:wheel 和镜像必须 arm64,vLLM 必须是 DGX-Spark 专用镜像。
2. 128GB 是**统一内存、带宽 273GB/s 才是瓶颈**:只带量化模型(NVFP4/FP8/GGUF Q4),别带 FP16 大模型。
3. **agent 永远对着一个 OpenAI 兼容的 :8000 说话**,后端(120B/30B/vLLM/llama.cpp/云)可随时降级 —— 这是抗风险的核心设计。
