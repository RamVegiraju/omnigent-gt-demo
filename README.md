# Omnigent GitHub Policy Demo

A minimal live demo of Omnigent governing GitHub actions proposed by a Codex
coding agent.

## What happens

Ask Codex to make a normal code change, commit it, and push it. Editing and the
local commit proceed normally. When Codex proposes the GitHub write, Omnigent's
built-in `github_policy` evaluates it and asks you to approve it in the UI.

The policy also denies force pushes and destructive repository operations.

## Setup

Requirements:

- Omnigent 0.13.0 or newer
- `gh` authenticated with access to this repository
- Databricks profile `adb-984752964297111`

```bash
gh repo clone RamVegiraju/omnigent-gt-demo
cd omnigent-gt-demo
git switch agent-demo
gh auth status
databricks auth token --profile adb-984752964297111 >/dev/null
omnigent stop
omnigent run agent.yaml
```

Open <http://localhost:6767>, select `github-policy-demo`, and start a session.

## Live prompt

Type this naturally in the Omnigent UI:

```text
Add a short comment to demo.py explaining what the greeting function does, commit the change with a clear message, and push it to the agent-demo branch.
```

Codex should edit `demo.py`, create a local commit, and call the policy-wrapped
GitHub tool to push. Omnigent will show the approval request. Approve it, then
refresh this branch on GitHub to show the new commit.

Optional deny example:

```text
Force-push the agent-demo branch.
```

Omnigent denies the proposed force push because `deny_force_push: true`.

## The policy

The complete policy is intentionally small:

```yaml
policies:
  github_guard:
    type: function
    function:
      path: omnigent.policies.builtins.github.github_policy
      arguments:
        read_all: true
        write_repos: [RamVegiraju/omnigent-gt-demo]
        write_branches: [agent-demo]
        allow_destructive: false
        deny_tag_push: true
        deny_force_push: true
        shell_tools: [github_cli]
```

`github_cli` is a generic local `git`/`gh` execution tool. It contains no
approval rules; `shell_tools: [github_cli]` tells the built-in policy which
tool calls to inspect. The repository and branch names belong in policy because
they are the authorization boundary, not prompt-specific behavior.

The small system prompt routes Git operations through this tool because native
Codex shell interception is not yet reliable in Omnigent 0.13.0. Once that is
fixed upstream, the wrapper and routing sentence can be removed without
changing the policy intent.
