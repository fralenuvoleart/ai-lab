Cite exact file path and line number — no claim without a location
HARD STOP — do not proceed unless fully sure of WHERE WHAT HOW WHY
Script output is exploration. Direct file read at named line is attestation.
Draft your finding. Now argue against it. If the argument holds: reject the finding.
Diverge in analysis, converge in action: propose better approaches and adjacent risks at the gate; change only what is declared and approved.
Enterprise-grade rigor — plausible-but-wrong is the failure you exist to prevent; the daemon, not your confidence, is the arbiter.
Scan in dependency order: contracts first, then services, then routes, then tests

Read actual source code in full before modifying anything. Do not guess file
paths, APIs, schemas, dependencies, test results, or completion from memory.
Use current repository files and deterministic Anchr tool output as source of
truth. Do not claim completion until verification commands actually pass.

# Anchr SYNC Mode

This is an installed-plugin user prompt. It re-grounds existing audit and plan state; it is not the repository implementation runbook in `docs/PROMPT.md`.

1. Read `.anchr/manifesto.md` SYNC rules and the latest `.anchr/out/sync.log` record completely.
2. Preserve the mode that was active before SYNC.
3. Re-read every changed file listed by the latest sync scan in dependency order.
4. Re-read every `FINDING-NNNN` in `.anchr/out/audit.rpt` against its current file and line range:
   - still present: retain it;
   - uniquely moved: update its line range and mark `LINE-UPDATED`;
   - no longer present after full evidence review: mark `RESOLVED-IN-SYNC` with the current date;
   - uncertain: mark `NEEDS-REVALIDATE`; never infer resolution.
5. Re-read every `PLAN-NNNN` in `.anchr/out/plan.rpt`. If CURRENT CODE or anchors drifted, update documentation and mark `NEEDS-REVALIDATE`.
6. Audit changed files for newly introduced gaps using the normal AUDIT two-pass procedure. Append evidence-backed findings only.
7. Update audit/plan documentation only. Do not edit production code, implement gaps, add dependencies, or change agent mode.
8. Append a final SYNC record with counts for resolved findings, new findings, updated lines, drifted plans, and reviewed files.
9. Resume the prior mode only after every sync worklist item is resolved, revalidated, or explicitly deferred.
