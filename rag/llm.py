import os
import re
import shutil
import subprocess

import httpx


class LLMError(Exception):
    pass


def _call_gemini(prompt, timeout):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise LLMError("GEMINI_API_KEY not set")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"thinkingConfig": {"thinkingBudget": 0}},
    }
    r = httpx.post(url, params={"key": key}, json=payload, timeout=timeout)
    if r.status_code != 200:
        raise LLMError(f"gemini failed: {r.status_code} {r.text[:200]}")
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        raise LLMError(f"gemini: unexpected response: {str(data)[:200]}")


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
    if engine == "gemini":
        return _call_gemini(prompt, timeout)
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
