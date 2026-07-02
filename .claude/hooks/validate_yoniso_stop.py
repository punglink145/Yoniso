#!/usr/bin/env python3
"""Claude Code Stop hook — enforce the Yoniso contract on the model's output.

Wire it up in .claude/settings.json (see .claude/settings.example.json):
  { "hooks": { "Stop": [{ "matcher": "", "hooks": [
      { "type": "command", "command": "python .claude/hooks/validate_yoniso_stop.py" }
  ]}] }}

stdin : Claude Code Stop-hook JSON:
  { "session_id", "transcript_path", "cwd", "hook_event_name", "stop_hook_active" }
exit  : 0 = pass / no-op, 2 = block (Claude Code feeds stderr back to the model)

Behavior:
  - Reads the transcript JSONL, finds the LAST assistant text message.
  - If it doesn't look like a Yoniso output (no "Yoniso Assessment" /
    "Root Cause Chain" marker), it is skipped (exit 0) — this hook only
    enforces turns that CLAIM to follow Yoniso.
  - Otherwise it pipes the text to scripts/validate_yoniso_output.py and,
    on failure, exits 2 with the failing rules on stderr so the model can
    re-emit a contract-conformant assessment.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

# Force UTF-8 on std streams — Windows defaults to cp1252, which corrupts
# non-ASCII detail pulled from a model's output (Thai/Unicode) and crashes
# the hook when Claude Code reads stderr as UTF-8.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def last_assistant_text(transcript_path: pathlib.Path) -> str:
    """Return the text of the last assistant message in a CC transcript JSONL."""
    last = ""
    for line in transcript_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = ev.get("message") if isinstance(ev, dict) else None
        if msg and msg.get("role") != "assistant":
            continue
        if not msg and ev.get("type") not in ("assistant", "message"):
            continue
        content = (msg or ev).get("content")
        if isinstance(content, list):
            text = "\n".join(
                b.get("text", "")
                for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            )
        elif isinstance(content, str):
            text = content
        else:
            continue
        if text.strip():
            last = text
    return last


def looks_like_yoniso(text: str) -> bool:
    t = text.lower()
    return "yoniso assessment" in t or "root cause chain" in t


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # not a real hook invocation (e.g. manual test)

    transcript = payload.get("transcript_path")
    if not transcript:
        return 0
    tp = pathlib.Path(transcript)
    if not tp.exists():
        return 0

    last = last_assistant_text(tp)
    if not last or not looks_like_yoniso(last):
        return 0  # not a Yoniso turn — do not block unrelated turns

    # .claude/hooks/x.py -> .claude/hooks -> .claude -> <repo root>
    script = pathlib.Path(__file__).resolve().parent.parent.parent / "scripts" / "validate_yoniso_output.py"
    r = subprocess.run(
        [sys.executable, str(script), "--json"],
        input=last, capture_output=True, text=True, encoding="utf-8",
    )
    if r.returncode == 0:
        return 0

    try:
        data = json.loads(r.stdout)
        fails = [f for f in data.get("findings", []) if not f.get("passed")]
        detail = "\n".join(f"  - {f['rule']}: {f['detail']}" for f in fails)
        sys.stderr.write(
            "Yoniso output failed the runtime contract. Re-emit an assessment "
            "that passes every rule below:\n" + detail + "\n"
        )
    except (json.JSONDecodeError, ValueError):
        sys.stderr.write(r.stdout or r.stderr or "Yoniso validation failed.\n")
    return 2  # exit 2 → Claude Code blocks and feeds stderr back to the model


if __name__ == "__main__":
    sys.exit(main())
