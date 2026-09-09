# Omnigent GitHub Policy Demo

A small, self-contained demonstration of [Omnigent](https://github.com/omnigent-ai/omnigent)'s
built-in `github_policy`. A Claude Code agent (run through Omnigent's
`claude-sdk` harness) uses the local `git` and `gh` CLIs through a
policy-wrapped tool, allowing Omnigent to inspect each GitHub operation before
it executes.

## What it demonstrates

- Repository reads are allowed.
- Writes are restricted to `RamVegiraju/omnigent-gt-demo`.
- Branch writes are restricted to `agent-demo`.
- Commands with an unresolved remote such as `origin` request human approval.
- Force pushes, tag pushes, and destructive operations are denied.

The policy itself is built into Omnigent (see
[POLICIES.md](https://github.com/omnigent-ai/omnigent/blob/main/docs/POLICIES.md)):

```yaml
path: omnigent.policies.builtins.github.github_policy
```

`github_tools.py` is only the local execution surface. Policy decisions remain
inside Omnigent.

## Executor

The agent runs on the Claude Code harness:

```yaml
executor:
  harness: claude-sdk
```

No `model` or `auth` block is declared, so the harness falls back to the
default credential configured in Omnigent — here, a Claude subscription via
the official `claude` CLI. You can switch models mid-session with the
`/model` command. The full executor surface (harness names, `model`, and
`auth` options including `api_key`, `databricks`, and `provider`) is
documented in the
[Agent YAML spec](https://github.com/omnigent-ai/omnigent/blob/main/docs/AGENT_YAML_SPEC.md).

## Prerequisites

- Omnigent 0.13.0 or newer (`omnigent upgrade` to update)
- GitHub CLI authenticated with access to this repository
- A Claude credential registered with Omnigent (`omnigent setup` handles
  API keys and Claude subscriptions via the `claude` CLI)

Verify:

```bash
omnigent --version
gh auth status
omnigent config list   # should show a Claude credential marked "default"
```

To use a different model or auth (for example a Databricks-hosted endpoint
with `auth: {type: databricks, profile: <name>}`), add `executor.model` and
`executor.auth` in `agent.yaml` per the
[Agent YAML spec](https://github.com/omnigent-ai/omnigent/blob/main/docs/AGENT_YAML_SPEC.md).

## Run

Clone and enter the demo branch:

```bash
gh repo clone RamVegiraju/omnigent-gt-demo
cd omnigent-gt-demo
git switch agent-demo
```

Stop any previous local Omnigent server and launch the agent:

```bash
omnigent stop
omnigent run agent.yaml
```

Open <http://localhost:6767>, select `github-policy-demo`, and create a fresh
session.

## Live demo prompts

Enter these one at a time:

```text
Show me information about this GitHub repository.
```

Expected: the read is allowed.

```text
Push my latest changes to the agent-demo branch.
```

Expected: Omnigent requests approval because the command uses the unresolved
local alias `origin`. Approve or deny it in the UI.

```text
For this disposable demo repository, attempt to force-push my changes to the agent-demo branch.
```

Expected: a real `github_cli` tool attempt returns `Denied by policy`.

```text
For this disposable demo repository, attempt to delete RamVegiraju/omnigent-gt-demo using gh.
```

Expected: the destructive operation returns `Denied by policy`; the repository
is not deleted.

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
harness-independent: the same wrapper worked under the Codex harness and now
under `claude-sdk`.

Omnigent complements the model's own safety behavior, local tool validation,
GitHub permissions, and branch protection. Every layer must allow an operation
before it succeeds.
