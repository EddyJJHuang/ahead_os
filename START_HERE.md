# Local PM OS — Start Here

Web dashboard for the [ahead_os](https://github.com/EddyJJHuang/ahead_os) agent stack.

## Run the demo

```bash
# 1. Backend (GB10 or local dev)
bash serve.sh
curl http://localhost:8100/health

# 2. Web UI (React dashboard in this repo)
./web.sh
# Open http://localhost:5173
```

Remote GB10:

```bash
VITE_API_URL=http://<GB10_LAN_IP>:8100 ./web.sh
```

## 4 panels

1. **Executive Decision** — demo verdict + optional KB enrichment via `/api/rag`
2. **Top 3 Actions** — demo actions + client-side drafts
3. **Ask PM OS** — live chat via `/api/chat/stream` (:8100), with offline mock fallback
4. **Evidence Drawer** — live RAG hits + demo source cards

See [`FRONTEND.md`](FRONTEND.md) for the full PM OS API contract (`/api/pm/*`). Panel wiring to those endpoints is tracked as follow-up work.

## Scripts

| Script | Role |
|---|---|
| `serve.sh` | Backend API — mock tools (:8088) + api_server (:8100) |
| `web.sh` | Start React dashboard (`frontend/`) |
| `dashboard.sh` | Terminal ops monitor (not the web UI) |

Full hackathon deploy: upstream [`START_HERE.md`](https://github.com/EddyJJHuang/ahead_os/blob/main/START_HERE.md) and [`ON_SITE_PLAYBOOK.md`](https://github.com/EddyJJHuang/ahead_os/blob/main/ON_SITE_PLAYBOOK.md).
