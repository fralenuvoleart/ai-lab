# ANCHR Protocol — Claude Code

This repository enforces the Anchr agent guard protocol.

@.anchr/manifesto.md

BEFORE ANY ACTION THIS SESSION (run from the repo root):
  Step 1: python .anchr/anchr_tools.py STATUS  (reports lock_exists + required files)
  Step 2: if lock_exists is true, STOP and tell the human — do not touch anything
  Step 3: python .anchr/anchr_tools.py GRAPH_STATUS
  Step 4: Read .anchr/start.md completely
  Step 5: Follow start.md steps 1-6 in order
  (On macOS/Linux use python3 if python is not Python 3.)

The HITL checkpoint in start.md Step 4 is mandatory.
You do not code before the human types YES.
If GRAPH_STATUS is fresh, use GRAPH_QUERY before GATE_A1 and GRAPH_CALLERS/GRAPH_CALLEES before GATE_I1.

Slash command available: /anchr-start (runs .anchr/start.md automatically)
