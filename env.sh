# source ~/hack/env.sh  — hackathon shell setup
export SSD_ROOT="$HOME/hack"                 # NVMe copy (fast, survives SSD unplug). SSD: /media/dell/SSD-3/Hackathon
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=not-needed
export MODEL_ID=nemotron-super
export MOCK_BASE_URL=http://localhost:8088
export API_PORT=8100                         # frontend-facing API (api_server.py)
export PATH="$HOME/.local/bin:$PATH"
[ -f "$HOME/hack/.venv/bin/activate" ] && source "$HOME/hack/.venv/bin/activate"
