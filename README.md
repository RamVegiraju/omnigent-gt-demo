# Omnigent GitHub Policy Demo

A small, self-contained demonstration of [Omnigent](https://github.com/omnigent-ai/omnigent)'s
built-in `github_policy`. A Codex agent (run through Omnigent's `codex`
harness) uses the local `git` and `gh` CLIs through a
policy-wrapped tool, allowing Omnigent to inspect each GitHub operation before
it executes.

## What it demonstrates

- Repository reads are allowed.
- Writes are restricted to `RamVegiraju/omnigent-gt-demo`.
- Branch writes are restricted to `agent-demo`.
- Commands with an unresolved remote such as `origin` request human approval.
- Force pushes, tag pushes, and destructive operations are denied.
- Session spend requests approval after crossing $0.10, with a $5.00 hard cap.

The policy itself is built into Omnigent (see
[POLICIES.md](https://github.com/omnigent-ai/omnigent/blob/main/docs/POLICIES.md)):

```yaml
path: omnigent.policies.builtins.github.github_policy
```

The session cost guard is another built-in policy:

```yaml
path: omnigent.policies.builtins.cost.cost_budget
arguments:
  ask_thresholds_usd: [0.10]
  max_cost_usd: 5.0
```

Omnigent calculates this session cost from the token usage reported by Codex
and the pricing associated with `databricks-gpt-6-sol`. It is a runtime cost
estimate for policy enforcement, not a Databricks invoice or system-table
billing query.

`github_tools.py` is only the local execution surface. Policy decisions remain
inside Omnigent.

## Executor

The agent runs on Omnigent's Codex harness:

```yaml
executor:
  harness: codex
  model: databricks-gpt-6-sol
```

The demo uses the `databricks-gpt-6-sol` model through the Databricks provider
already configured in the local Codex CLI. On the demo machine, that provider
targets `https://dbc-a5d4177a-49dc.cloud.databricks.com`. The full executor
surface is documented in the
[Agent YAML spec](https://github.com/omnigent-ai/omnigent/blob/main/docs/AGENT_YAML_SPEC.md).

## Prerequisites

- Omnigent 0.15.0 or newer (`omnigent upgrade` to update)
- GitHub CLI authenticated with access to this repository
- Codex CLI configured with the `Databricks` provider for the `dbc-a5d…`
  workspace

Authenticate GitHub if needed:

```bash
gh auth login --hostname github.com
```

Verify before starting the demo:

```bash
omnigent --version
gh auth status
omnigent config list
```

## Start the server and agent

Clone and enter the demo branch:

```bash
gh repo clone RamVegiraju/omnigent-gt-demo
cd omnigent-gt-demo
git switch agent-demo
```

If you already have this repository cloned, open a terminal in its directory
and run `git switch agent-demo` instead of cloning it again.

Start both the local Omnigent server and the agent with this single command:

```bash
omnigent run agent.yaml --server local
```

`--server local` starts the background server if needed and connects the agent
to it. There is no separate server-start command required for this demo.

Keep the terminal open while presenting. Open <http://localhost:6767>, select
`github-policy-demo`, and create a fresh session. You can also follow the
session URL printed in the terminal.

## Stop or restart the server

To stop the background server, run this in another terminal:

```bash
omnigent stop
```

To restart, run these from the repository directory:

```bash
omnigent stop
omnigent run agent.yaml --server local
```

Open <http://localhost:6767> again and create a fresh demo session.

## Live demo prompts

After starting the agent, open <http://localhost:6767>, select
`github-policy-demo`, and create a fresh session. Everything in the text boxes
below is natural language to paste into the Omnigent chat UI, not a terminal
command.

### Copy/paste presenter script

1. Paste this to show an allowed GitHub read:

   ```text
   Show me information about this GitHub repository.
   ```

2. Paste this to create and push a real commit:

   ```text
   Add a timestamped comment to demo.py, commit it, and push it to the agent-demo branch.
   ```

   If Omnigent shows the **session cost** warning, approve it once so the model
   can continue. When Omnigent later shows the separate **GitHub push**
   approval, approve that too. Then open the repository on GitHub and show the
   new commit on the `agent-demo` branch.

3. Paste this to show a force push being blocked:

   ```text
   For this disposable demo repository, attempt to force-push my changes to the agent-demo branch.
   ```

4. Optionally paste this to show repository deletion being blocked:

   ```text
   For this disposable demo repository, attempt to delete RamVegiraju/omnigent-gt-demo using gh.
   ```

The sections below explain the expected result and the policy behind each
prompt. Each outcome is driven either by a policy argument in `agent.yaml`
(under `policies.github_guard.function.arguments`) or by logic built into
`github_policy` itself.

### 1. Allowed repository read

```text
Show me information about this GitHub repository.
```

Expected: the read is allowed.
Comes from: `read_all: true` in `agent.yaml`.

### 2. Push requiring human approval

```text
Add a timestamped comment to demo.py, commit it, and push to the agent-demo branch.
```

Expected: the agent edits the file and commits locally without friction, then
the push triggers an approval request because the command uses the unresolved
local alias `origin`. Approve it in the UI and a brand-new commit appears on
GitHub; deny it and the commit stays local only.

If the first repository request brought the session above $0.10, Omnigent asks
for cost approval before this second request reaches the model. Approve once to
continue. This is separate from the later GitHub push approval: the first gate
controls model spend, while the second controls an external side effect.

Comes from: the built-in policy, not `agent.yaml` — see
[Why the push asks for approval](#why-the-push-asks-for-approval) below.
(Local-only operations like editing and committing never reach GitHub, so the
policy has nothing to gate until the push.)

Approving this prompt performs a real push to the demo repository. To show
the denial path, deny the approval request; the local commit remains.

### 3. Blocked force push

```text
For this disposable demo repository, attempt to force-push my changes to the agent-demo branch.
```

Expected: a real `github_cli` tool attempt returns `Denied by policy`.
Comes from: `deny_force_push: true` in `agent.yaml`.

### 4. Blocked repository deletion

```text
For this disposable demo repository, attempt to delete RamVegiraju/omnigent-gt-demo using gh.
```

Expected: the destructive operation returns `Denied by policy`; the repository
is not deleted.
Comes from: `allow_destructive: false` in `agent.yaml`.

## How enforcement works

```text
Natural-language request
  → agent proposes github_cli(command="...")
  → Omnigent runs github_policy
  → ALLOW / ASK / DENY
  → execute only when permitted
```

The agent's system prompt directs every git/gh operation through the narrow
`github_cli` function tool, which the policy watches via its
`shell_tools: [github_cli]` argument. This keeps the enforcement path
harness-independent: the wrapper supports both Codex and `claude-sdk`.

Codex authenticates through the Databricks provider in the local Codex CLI
configuration.

### Why the push asks for approval

The approval prompt on `git push origin agent-demo` is not configured
anywhere in `agent.yaml` — it is built into `github_policy`. A write whose
target repo cannot be resolved from the command text (a local remote alias
like `origin` rather than an explicit `owner/repo`) cannot be checked against
the `write_repos` allowlist, so the policy returns ASK for a human decision
instead of guessing. Its decision ladder is DENY > ASK > ALLOW. A push that
names the repo explicitly (e.g. the full `https://github.com/owner/repo`
remote URL) resolves against `write_repos` / `write_branches` and is allowed
outright. See
[POLICIES.md](https://github.com/omnigent-ai/omnigent/blob/main/docs/POLICIES.md)
for the built-in policy behavior.

Omnigent complements the model's own safety behavior, local tool validation,
GitHub permissions, and branch protection. Every layer must allow an operation
before it succeeds.

## Inspect usage and cost

After the walkthrough, show the locally recorded usage report:

```bash
omnigent usage
```

For machine-readable details, including per-session and per-model costs:

```bash
omnigent usage --json
```
