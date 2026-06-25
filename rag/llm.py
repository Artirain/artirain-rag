import os
import re
import shutil
import subprocess


class LLMError(Exception):
    pass


_CLAUDE_RE = re.compile(r"^CLAUDE", re.IGNORECASE)


def _clean_env(env=None):
    env = dict(os.environ if env is None else env)
    for k in list(env.keys()):
        if _CLAUDE_RE.match(k):
            del env[k]
    return env


def _resolve(exe, args):
    path = shutil.which(exe) or exe
    if os.name == "nt" and path.lower().endswith((".cmd", ".bat")):
        return [os.environ.get("ComSpec", "cmd.exe"), "/c", path, *args]
    return [path, *args]


def _build_command(engine):
    if engine == "claude":
        return _resolve("claude", ["-p"])
    return _resolve("codex", ["exec", "--skip-git-repo-check", "-"])


def call_llm(prompt, engine="codex", timeout=180):
    cmd = _build_command(engine)
    proc = subprocess.run(
        cmd,
        input=prompt,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_clean_env(),
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
    )
    if proc.returncode != 0:
        raise LLMError(f"{engine} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()
