# ANCHR Protocol — GitHub Copilot

This repository uses Anchr. Before any task (run from the repo root):
1. Run: python .anchr/anchr_tools.py STATUS  (reports lock_exists). If lock_exists is true, stop and notify the user.
2. Run: python .anchr/anchr_tools.py GRAPH_STATUS
3. Read: .anchr/start.md
4. Follow start.md steps exactly, including Step 4 (human confirmation)
5. If GRAPH_STATUS is fresh, use GRAPH_QUERY before GATE_A1 and GRAPH_CALLERS/GRAPH_CALLEES before GATE_I1.
(On macOS/Linux use python3 if python is not Python 3.)

You must not make file changes before completing start.md Step 4.
Operating contract: .anchr/manifesto.md
