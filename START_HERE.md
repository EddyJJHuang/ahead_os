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

1. **Executive Decision** — `POST /api/pm/analysis` (ship readiness + executive summary)
2. **Top 3 Actions** — `POST /api/pm/analysis` → `POST /api/pm/draft`
3. **Ask PM OS** — `POST /api/pm/ask/stream` when vLLM is ready; demo answers otherwise
4. **Evidence Drawer** — risk/criteria evidence from analysis + `GET /api/pm/sources`

See [`FRONTEND.md`](FRONTEND.md) for the full PM OS API contract.

## Scripts

| Script | Role |
|---|---|
| `serve.sh` | Backend API — mock tools (:8088) + api_server (:8100) |
| `web.sh` | Start React dashboard (`frontend/`) |
| `dashboard.sh` | Terminal ops monitor (not the web UI) |

Full hackathon deploy: upstream [`START_HERE.md`](https://github.com/EddyJJHuang/ahead_os/blob/main/START_HERE.md) and [`ON_SITE_PLAYBOOK.md`](https://github.com/EddyJJHuang/ahead_os/blob/main/ON_SITE_PLAYBOOK.md).
