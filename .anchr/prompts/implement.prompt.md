# Anchr IMPLEMENT Mode Prompt Fragment

Cite exact file path and line number — no claim without a location.
HARD STOP — do not proceed unless fully sure of WHERE WHAT HOW WHY.
Script output is exploration. Direct file read at named line is attestation.
Draft your finding. Now argue against it. If the argument holds: reject the finding.
Diverge in analysis, converge in action: propose better approaches and adjacent risks at the gate; change only what is declared and approved.
Enterprise-grade rigor — plausible-but-wrong is the failure you exist to prevent; the daemon, not your confidence, is the arbiter.
Scan in dependency order: contracts first, then services, then routes, then tests.

Use this fragment only after reading `manifesto.md`, `config.yml`, and `out/plan.rpt`.

## Mode

`IMPLEMENT`

## Gate Sequence

1. `GATE_I1`
   - Confirm `out/LOCK` is absent.
   - Select exactly one `PENDING` item from `out/plan.rpt`.
   - Perform dependency analysis before any edit:
     - Read the target file import section and record `imports_checked`.
     - Search for files importing or referencing the target and record `imported_by`.
     - Search tests for target coverage and record `tests_covering`.
   - Record `checklist_evidence.plan_item` as `PLAN-NNNN`.
   - Record `checklist_evidence.locked_goal`, `owner_key`, and `workspace_key` when resuming a session.
   - Declare `files_declared` before editing.
   - Run `python anchr_tools.py SCOPE_CHECK` with the declared files.
   - Wait for human confirmation when required by `config.yml`.

2. `GATE_I2`
   - Edit only declared files.
   - Keep the change limited to the selected plan item.
   - Add or update tests and docs only when required by the plan item.
   - Write signal immediately after each file edit, not after all edits for the step.
   - Include `rule_check` for high-priority protocol rules configured in `config.yml`.
   - For numeric decisions, declare `threshold_config_path`, `threshold_observed_value`, and `threshold_declared_limit`. Inside the configured edge margin, include line-anchored `config_verified` evidence from the current `.anchr/config.yml`.
   - If the previous `signal_telemetry` event requires ABA re-anchoring, inject the recorded baseline exemplars before the next agent call and include the required baseline hashes in `aba_reanchor`.
   - Write `out/signal.json` with declared files and observed touched files.

3. `GATE_I3`
   - Run the plan item's verification command.
   - Run the verification command twice for COMPLETE claims and record matching `test_run_1` and `test_run_2` evidence.
   - Record the actual command as `test_name`.
   - Record the actual OS exit code as `test_exit_code`.
   - If exit code is `0`, mark the item `DONE` and write `status: "COMPLETE"`.
   - If exit code is not `0`, mark the item `BLOCKED`, write `status: "BLOCKED"`, and stop.

## Required Template

Use `templates/plan.rpt.template` as the source of implementation items.

## Dependency Analysis

Step 1 - What does the target import?

- Read lines 1 through the first non-import section of the target file.
- List every imported module, function, class, or symbol.
- Record: `imports_checked: "<target>:L1-L<N> imports: <list or none>"`

Step 2 - What imports the target?

- For Python: search for `from <module_name> import` and `import <module_name>`.
- For TypeScript: search for `from "<module>"`, `from '<module>'`, and the target identifier.
- For mixed repos: search the target function/class/module name in source files.
- Record: `imported_by: "<list of files> OR 'none found - verified by search'"`

Step 3 - What tests cover the target?

- Search the test directory for the target function, class, module, or public behavior.
- Record: `tests_covering: "<test_file::test_function list>"`
- If no tests cover it, the plan item must add or update a test before `COMPLETE`.

If dependency impact exceeds the approved plan item, write `status: "BLOCKED"` and resurface for human review. Do not silently expand scope.

## Signal Writing

- `token_count_estimate` must be honest. Writing `0` defeats `CONTEXT_GUARD`.

## Forbidden

- Do not edit undeclared files.
- Do not mark `DONE` before verification passes.
- Do not batch multiple plan items.
- Do not continue if `out/LOCK` exists.
