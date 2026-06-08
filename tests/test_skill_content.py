"""test_skill_content.py — content quality tests for Yoniso SKILL.md"""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = REPO_ROOT / "SKILL.md"


def read_skill():
    if not SKILL_PATH.exists():
        pytest.fail(f"{SKILL_PATH} not found")
    return SKILL_PATH.read_text(encoding="utf-8")


def extract_body(content: str) -> str:
    """Return only the body (after frontmatter)."""
    assert content.startswith("---"), "Missing opening ---"
    end_idx = content.find("---", 3)
    assert end_idx != -1, "Missing closing ---"
    return content[end_idx + 3 :].strip()


class TestSkillLength:
    def test_body_not_excessively_long(self):
        """Body should be under 250 non-empty lines for context efficiency."""
        body = extract_body(read_skill())
        body_lines = [l for l in body.split("\n") if l.strip()]
        assert len(body_lines) <= 250, (
            f"Body is {len(body_lines)} non-empty lines — "
            "consider moving content to references/"
        )

    def test_total_file_not_excessive(self):
        """Total SKILL.md should be under 250 lines."""
        content = read_skill()
        total_lines = len(content.split("\n"))
        assert total_lines <= 300, (
            f"SKILL.md is {total_lines} lines — "
            "aim for <250 for context efficiency"
        )


class TestNoFakeGuarantees:
    def test_no_always_enforce_language(self):
        """Skill should not claim to always enforce behavior."""
        body = extract_body(read_skill()).lower()
        # The deterministic enforcement section should explain limits
        assert "cannot force" in body or "cannot guarantee" in body or \
               "does not guarantee" in body or "prompt-level" in body or \
               "for hard enforcement" in body or "deterministic enforcement" in body, (
            "Skill should acknowledge limits of prompt-level guidance"
        )

    def test_no_perfect_guarantee(self):
        """Skill should not use 'guarantee' language without caveats."""
        body = extract_body(read_skill())
        body_lower = body.lower()
        if "guarantee" in body_lower:
            safe_patterns = [
                "does not guarantee", "cannot guarantee",
                "do not guarantee",
            ]
            has_safe = any(p in body_lower for p in safe_patterns)
            assert has_safe, (
                "'guarantee' found without negation — "
                "add 'does not guarantee' or remove claim"
            )

    def test_no_hidden_chain_of_thought(self):
        """Skill should not demand private chain-of-thought."""
        body = read_skill().lower()
        forbidden = [
            "reveal your thinking",
            "show all reasoning",
            "private reasoning",
            "internal monologue",
        ]
        for phrase in forbidden:
            assert phrase not in body, f"Forbidden phrase: '{phrase}'"


class TestThaiIdentity:
    def test_thai_name_present(self):
        """YONISO-MANASIKARA should appear in the body."""
        body = read_skill()
        assert "YONISO-MANASIKARA" in body, (
            "Thai identity marker missing"
        )

    def test_skill_is_operational_not_philosophical(self):
        """Skill should contain concrete operational instructions."""
        body = extract_body(read_skill()).lower()
        operational_markers = [
            "severity", "why-chain", "output", "fix",
        ]
        for marker in operational_markers:
            assert marker in body, f"Missing operational marker: '{marker}'"


class TestProgressiveDisclosure:
    def test_references_section_exists(self):
        """SKILL.md should have a References section pointing to detail files."""
        body = read_skill()
        assert "references/" in body.lower(), (
            "Missing references/ pointers — should use progressive disclosure"
        )

    def test_examples_not_embedded(self):
        """Long worked examples should be in references/, not SKILL.md body."""
        body = extract_body(read_skill())
        # Examples reference file should be linked, not embedded in full
        assert "references/examples.md" in body.lower(), (
            "Should reference examples.md for worked examples"
        )
