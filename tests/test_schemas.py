"""Tests for src/schemas.py — Pydantic model validation."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.schemas import (
    ProjectContext,
    StageResult,
    PolicyViolation,
    AuditEntry,
    Decision,
    Severity,
)

import pytest
from pydantic import ValidationError


class TestProjectContext:
    """ProjectContext model validation."""

    def test_valid_context(self, mock_context):
        ctx = ProjectContext(**mock_context)
        assert ctx.project_name == "test-app"
        assert ctx.language == "javascript/node"
        assert "express" in ctx.frameworks

    def test_missing_project_name_raises(self):
        with pytest.raises(ValidationError):
            ProjectContext(language="python")

    def test_empty_project_name_raises(self):
        with pytest.raises(ValidationError):
            ProjectContext(project_name="")

    def test_defaults_filled(self):
        ctx = ProjectContext(project_name="minimal")
        assert ctx.language == "unknown"
        assert ctx.frameworks == []
        assert ctx.ports == []

    def test_ports_coerced_to_strings(self):
        ctx = ProjectContext(project_name="app", ports=[3000, 8080])
        assert ctx.ports == ["3000", "8080"]

    def test_none_language_normalized(self):
        ctx = ProjectContext(project_name="app", language=None)
        assert ctx.language == "unknown"

    def test_language_lowercased(self):
        ctx = ProjectContext(project_name="app", language="Python")
        assert ctx.language == "python"


class TestStageResult:
    """StageResult model validation."""

    def test_defaults(self):
        r = StageResult(stage_name="Docker", status=Decision.APPROVE)
        assert r.content == ""
        assert r.cycles == 1
        assert r.published_via is None
        assert r.policy_violations == []

    def test_with_violations(self):
        v = PolicyViolation(rule="docker-no-latest", message="Don't use :latest")
        r = StageResult(
            stage_name="Docker",
            status=Decision.APPROVE,
            content="FROM node:18",
            policy_violations=[v],
        )
        assert len(r.policy_violations) == 1
        assert r.policy_violations[0].severity == Severity.WARNING

    def test_invalid_cycles_raises(self):
        with pytest.raises(ValidationError):
            StageResult(stage_name="Docker", status=Decision.APPROVE, cycles=0)


class TestAuditEntry:
    """AuditEntry model validation."""

    def test_valid_entry(self):
        entry = AuditEntry(
            timestamp=time.time(),
            run_id="abc12345",
            stage="Docker",
            decision=Decision.APPROVE,
            reasoning="Looks good",
            cycle=1,
            drafts_count=3,
        )
        assert entry.stage == "Docker"
        assert entry.decision == Decision.APPROVE

    def test_decision_enum_from_string(self):
        entry = AuditEntry(
            timestamp=1.0,
            run_id="x",
            stage="K8s",
            decision="refine",
        )
        assert entry.decision == Decision.REFINE


class TestPolicyViolation:
    """PolicyViolation model validation."""

    def test_default_severity_is_warning(self):
        v = PolicyViolation(rule="test-rule", message="test msg")
        assert v.severity == Severity.WARNING

    def test_error_severity(self):
        v = PolicyViolation(rule="r", message="m", severity=Severity.ERROR)
        assert v.severity == Severity.ERROR
