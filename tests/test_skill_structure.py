"""test_skill_structure.py — structural tests for Yoniso SKILL.md"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = REPO_ROOT / "SKILL.md"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from validate_skill import parse_frontmatter  # noqa: E402


def read_skill():
    if not SKILL_PATH.exists():
        pytest.fail(f"{SKILL_PATH} not found")
    return SKILL_PATH.read_text(encoding="utf-8")


def extract_frontmatter(content: str):
    """Return (raw_frontmatter_text, body_text) or raise."""
    assert content.startswith("---"), "Missing opening ---"
    end_idx = content.find("---", 3)
    assert end_idx != -1, "Missing closing ---"
    fm_text = content[3:end_idx].strip()
    body_text = content[end_idx + 3 :].strip()
    return fm_text, body_text


# ─── Tests ───────────────────────────────────────────────────


class TestFrontmatter:
    def test_has_valid_frontmatter(self):
        """SKILL.md must have parseable YAML frontmatter."""
        content = read_skill()
        data, error = parse_frontmatter(content)
        assert error is None, f"Frontmatter parse error: {error}"
        assert data, "Frontmatter must contain at least one key"
        assert "name" in data, "Frontmatter missing 'name'"
        assert "description" in data, "Frontmatter missing 'description'"

    def test_skill_name_is_yoniso(self):
        """name must be 'yoniso'."""
        content = read_skill()
        data, _ = parse_frontmatter(content)
        assert data.get("name") == "yoniso", f"Expected name='yoniso', got '{data.get('name')}'"

    def test_description_is_trigger_effective(self):
        """Description must contain key trigger terms."""
        content = read_skill()
        data, _ = parse_frontmatter(content)
        desc = data.get("description", "").lower()
        trigger_terms = ["fix", "review", "plan", "root cause", "severity"]
        missing = [t for t in trigger_terms if t not in desc]
        assert not missing, f"Description missing trigger terms: {missing}"

    def test_description_minimum_length(self):
        """Description must be at least 50 characters."""
        content = read_skill()
        data, _ = parse_frontmatter(content)
        desc = data.get("description", "")
        assert len(desc) >= 50, f"Description too short: {len(desc)} chars"


class TestBody:
    def test_body_contains_operating_loop(self):
        """Body must describe the operating loop."""
        content = read_skill()
        body = content.lower()
        assert "operating loop" in body or "1. classify" in body

    def test_body_contains_severity_matrix(self):
        """Body must include severity classification table."""
        content = read_skill()
        body = content.lower()
        has_critical = "critical" in body
        has_low = "low" in body and ("typo" in body or "formatting" in body)
        assert has_critical, "Body missing CRITICAL severity mention"
        assert has_low, "Body missing LOW severity examples"

    def test_body_contains_output_contract(self):
        """Body must describe required output format."""
        content = read_skill()
        body = content.lower()
        assert "output contract" in body or "yoniso assessment" in body

    def test_body_contains_layer_definitions(self):
        """Body must define L1-L4 layers."""
        content = read_skill()
        assert "L1" in content and "Proximate" in content
        assert "L2" in content and "Systemic" in content
        assert "L4" in content and "Meta" in content

    def test_body_mentions_deterministic_enforcement(self):
        """Body must acknowledge limits of prompt-level guidance."""
        content = read_skill().lower()
        assert "enforcement" in content, "Body missing deterministic enforcement section"


class TestReferencedFiles:
    def test_reference_files_exist(self):
        """All files referenced in SKILL.md references section must exist."""
        ref_files = [
            "references/severity-signals.md",
            "references/why-chain-quality.md",
            "references/templates.md",
            "references/examples.md",
            "references/deterministic-enforcement.md",
        ]
        missing = []
        for rf in ref_files:
            if not (REPO_ROOT / rf).exists():
                missing.append(rf)
        assert not missing, f"Missing referenced files: {missing}"


class TestRegression:
    def test_no_single_line_frontmatter(self):
        """Regression: frontmatter must not be on a single line."""
        content = read_skill()
        first_line = content.split("\n")[0]
        if first_line.startswith("---"):
            assert first_line.count("---") < 2, (
                "Single-line frontmatter regression: "
                "'--- ... ---' on one line. Use multi-line format."
            )

    def test_no_colon_space_in_unquoted_description(self):
        """Regression: description must use block scalar to avoid
        YAML colon-space mapping errors in unquoted scalars."""
        content = read_skill()
        fm_text, _ = extract_frontmatter(content)
        found_desc = False
        for line in fm_text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("description:"):
                found_desc = True
                remainder = stripped[len("description:"):].strip()
                assert remainder in (">-", ">", "|-", "|"), (
                    f"description must use YAML block scalar (e.g. '>-'), "
                    f"got inline value: '{remainder[:60]}...' — "
                    f"bare colon-space in unquoted scalar causes parse error"
                )
        assert found_desc, "description field not found in frontmatter"

    def test_no_tool_permissions_granted(self):
        """SKILL.md should not include allowed-tools unless strictly needed."""
        content = read_skill()
        fm_text, _ = extract_frontmatter(content)
        assert "allowed-tools" not in fm_text.lower(), (
            "SKILL.md should not grant tool permissions by default"
        )
