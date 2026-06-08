#!/usr/bin/env python3
"""validate_skill.py — structural validator for Yoniso SKILL.md.

Validates:
  - YAML frontmatter is present and valid
  - name = "yoniso"
  - description is trigger-effective (has key terms)
  - body contains required sections
  - referenced files exist

Exit 0 on success, nonzero on failure.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = REPO_ROOT / "SKILL.md"

REQUIRED_TRIGGER_TERMS = [
    "fix", "review", "plan", "architecture",
    "root cause", "severity", "regression",
]

REQUIRED_SECTIONS = [
    "what this skill does",
    "when this skill activates",
    "operating loop",
    "severity",
    "why-chain",
    "output contract",
]

REFERENCED_FILES = [
    "references/severity-signals.md",
    "references/why-chain-quality.md",
    "references/templates.md",
    "references/examples.md",
    "references/deterministic-enforcement.md",
]


def parse_frontmatter(content: str):
    """Extract and parse YAML frontmatter between --- markers."""
    if not content.startswith("---"):
        return None, "missing opening ---"

    end_idx = content.find("---", 3)
    if end_idx == -1:
        return None, "missing closing ---"

    fm_text = content[3:end_idx].strip()
    if not fm_text:
        return None, "empty frontmatter"

    # Parse simple YAML: key: value pairs (value can be folded scalar with >-)
    data = {}
    current_key = None
    current_value_lines = []
    in_block_scalar = False

    for line in fm_text.split("\n"):
        if in_block_scalar:
            # Check if this line starts a new top-level key
            if not line.startswith(" ") and not line.startswith("\t") and ":" in line:
                # Save previous block scalar
                if current_key:
                    data[current_key] = "\n".join(current_value_lines).strip()
                # New key
                key_part, _, val_part = line.partition(":")
                current_key = key_part.strip()
                val_stripped = val_part.strip()
                if not val_stripped:
                    in_block_scalar = True
                    current_value_lines = []
                else:
                    in_block_scalar = False
                    data[current_key] = val_stripped
                continue
            current_value_lines.append(line.strip())
            continue

        if ":" not in line:
            if current_key:
                current_value_lines.append(line.strip())
            continue

        key_part, _, val_part = line.partition(":")
        key = key_part.strip()
        val = val_part.strip()

        # Save previous key
        if current_key and current_key != key:
            if current_value_lines:
                data[current_key] = "\n".join(current_value_lines).strip()
                current_value_lines = []

        current_key = key

        if val == "" or val in (">-", ">", "|-", "|"):
            in_block_scalar = True
            continue
        else:
            in_block_scalar = False
            data[key] = val

    # Save last key
    if current_key:
        if current_value_lines:
            data[current_key] = "\n".join(current_value_lines).strip()

    return data, None


def check_body(content: str):
    """Check body for required sections (case-insensitive)."""
    body_lower = content.lower()
    missing = []
    for section in REQUIRED_SECTIONS:
        if section.lower() not in body_lower:
            missing.append(section)
    return missing


def main() -> int:
    errors = []
    warnings = []

    if not SKILL_PATH.exists():
        print(f"FAIL: {SKILL_PATH} not found")
        return 1

    content = SKILL_PATH.read_text(encoding="utf-8")
    lines = content.split("\n")

    # ── Frontmatter ──────────────────────────────────────────
    data, fm_error = parse_frontmatter(content)
    if fm_error:
        errors.append(f"YAML frontmatter: {fm_error}")
    else:
        # Check name
        name = data.get("name")
        if not name:
            errors.append("YAML frontmatter: missing 'name' field")
        elif name != "yoniso":
            errors.append(f"YAML frontmatter: name='{name}', expected 'yoniso'")

        # Check description
        desc = data.get("description")
        if not desc:
            errors.append("YAML frontmatter: missing 'description' field")
        elif len(desc) < 50:
            errors.append(
                f"YAML frontmatter: description too short ({len(desc)} chars, need >= 50)"
            )
        else:
            desc_lower = desc.lower()
            missing_terms = [
                t for t in REQUIRED_TRIGGER_TERMS if t not in desc_lower
            ]
            if missing_terms:
                errors.append(
                    f"YAML frontmatter: description missing trigger terms: {missing_terms}"
                )

    # ── Body sections ────────────────────────────────────────
    missing_sections = check_body(content)
    if missing_sections:
        errors.append(f"Body missing required sections: {missing_sections}")

    # ── Body length ──────────────────────────────────────────
    body_start = 0
    if content.startswith("---"):
        end_idx = content.find("---", 3)
        if end_idx != -1:
            body_start = end_idx + 3

    body_lines = content[body_start:].strip().split("\n")
    body_line_count = len([l for l in body_lines if l.strip()])

    if body_line_count > 300:
        warnings.append(f"Body is long ({body_line_count} lines). Consider moving content to references/.")
    elif body_line_count > 200:
        warnings.append(f"Body is moderately long ({body_line_count} lines).")

    # ── Referenced files ─────────────────────────────────────
    for ref_file in REFERENCED_FILES:
        ref_path = REPO_ROOT / ref_file
        if not ref_path.exists():
            errors.append(f"Referenced file missing: {ref_file}")

    # ── No single-line frontmatter regression ────────────────
    first_line = lines[0] if lines else ""
    if first_line.startswith("---") and first_line.count("---") >= 2:
        errors.append("Single-line frontmatter detected: '--- ... ---' on one line. Use multi-line format.")

    # ── Exact multiline frontmatter structure ─────────────────
    if not first_line.startswith("---"):
        errors.append("line 1 must be exactly '---'")

    closing_idx = None
    for i in range(1, min(len(lines), 10)):
        if lines[i].strip() == "---":
            closing_idx = i
            break
    if closing_idx is None:
        errors.append("closing '---' not found within first 10 lines")
    elif closing_idx < 4:
        errors.append(f"frontmatter too short: closing --- at line {closing_idx + 1}, expected >= 4 lines")

    if len(lines) < 2 or not lines[1].strip().startswith("name:"):
        errors.append("line 2 must start with 'name:'")

    if closing_idx:
        desc_found = False
        for i in range(2, closing_idx):
            stripped = lines[i].strip()
            if stripped.startswith("description:"):
                desc_found = True
                remainder = stripped[len("description:"):].strip()
                if remainder not in (">-", ">", "|-", "|"):
                    errors.append(
                        f"description must use block scalar (e.g. '>-'), "
                        f"got: '{remainder[:60]}'"
                    )
                break
        if not desc_found:
            errors.append("description field not found in frontmatter")

    # ── Report ───────────────────────────────────────────────
    if warnings:
        for w in warnings:
            print(f"WARN: {w}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        return 1

    print(f"PASS: SKILL.md is valid ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
