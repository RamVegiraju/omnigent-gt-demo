"""Local GitHub CLI tool exposed through Omnigent's policy engine."""

import shlex
import subprocess


def github_cli(command: str) -> str:
    """Run one local git or gh command without invoking a shell."""
    argv = shlex.split(command)
    if not argv or argv[0] not in {"git", "gh"}:
        return "Only git and gh commands are supported."

    completed = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    output = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
    return output or f"Command completed with exit code {completed.returncode}."
