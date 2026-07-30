#!/bin/bash
# Prints the opencode agent name for the smartest currently-active local
# model, per the dashboard at localhost:3333. Priority (best to worst):
# GLM-5.2 > Kimi-K2 > gpt-oss-120b > Gemma-4-31B > Qwen3-Coder > Qwen3-14B.
# Exits 1 with nothing printed if no suitable model is active.
set -euo pipefail

STATUS=$(curl -sf http://localhost:3333/api/status)

python3 - "$STATUS" <<'PYEOF'
import json
import sys

data = json.loads(sys.argv[1])
active = {m["key"] for m in data["models"] if m["status"] == "active" and m["http_ok"]}

priority = [
    ("glm", "glm-heavy"),
    ("kimi", "kimi"),
    ("gptoss", "gptoss"),
    ("gemma31b", "gemma31b"),
    ("coder", "coder"),
    ("qwen-gpu", "quick"),
]

for key, agent in priority:
    if key in active:
        print(agent)
        sys.exit(0)

sys.exit(1)
PYEOF
