"""Test rules repository normalization in harness-pin rendering."""

import pytest
from pathlib import Path

# Import the normalization helper from apply_harness
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "launchpad" / "commands"))
from apply_harness import _normalize_rules_repo


class TestNormalizeRulesRepo:
    """Test _normalize_rules_repo preserves org-qualified repos and prefixes bare repos."""

    def test_bare_repo_is_qualified(self):
        """Bare repo 'python-services-rules' should become 'drivestream-lab/python-services-rules'."""
        result = _normalize_rules_repo("python-services-rules", "drivestream-lab")
        assert result == "drivestream-lab/python-services-rules"

    def test_qualified_repo_unchanged(self):
        """Qualified repo 'drivestream-lab/python-services-rules' should remain unchanged."""
        result = _normalize_rules_repo("drivestream-lab/python-services-rules", "drivestream-lab")
        assert result == "drivestream-lab/python-services-rules"

    def test_qualified_repo_different_org(self):
        """Qualified repo should remain unchanged even with different org prefix."""
        result = _normalize_rules_repo("acme-corp/python-services-rules", "drivestream-lab")
        assert result == "acme-corp/python-services-rules"

    def test_bare_repo_no_org(self):
        """Bare repo with no org should remain unchanged."""
        result = _normalize_rules_repo("python-services-rules", None)
        assert result == "python-services-rules"

    def test_all_known_rules_repos(self):
        """All known rules repos should normalize correctly."""
        rules_repos = [
            "drivestream-lab/python-services-rules",
            "drivestream-lab/nextjs-bff-rules",
            "drivestream-lab/terraform-infra-rules",
            "drivestream-lab/data-platform-rules",
        ]
        for bare_repo in rules_repos:
            # Extract org from qualified repo
            org = bare_repo.split("/")[0]
            # Test that qualified stays qualified
            result = _normalize_rules_repo(bare_repo, org)
            assert result == bare_repo, f"Expected {bare_repo!r}, got {result!r}"

    def test_no_duplicate_org_prefix(self):
        """Ensure qualified input never generates duplicate org prefix."""
        qualified = "drivestream-lab/python-services-rules"
        result = _normalize_rules_repo(qualified, "drivestream-lab")
        # Should not contain double org prefix
        assert "drivestream-lab/drivestream-lab" not in result
        assert result == qualified
