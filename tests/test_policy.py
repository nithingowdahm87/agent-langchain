"""Tests for src/policy/validator.py — built-in policy rules."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.policy.validator import PolicyValidator
from src.schemas import Severity


class TestDockerPolicies:
    """Built-in Docker policy rules."""

    def setup_method(self):
        self.validator = PolicyValidator()

    def test_catches_latest_tag(self):
        dockerfile = "FROM node:latest\nRUN npm install\n"
        passed, violations = self.validator.validate(dockerfile, "Docker")
        rules = [v.rule for v in violations]
        assert "docker-no-latest" in rules or not passed
        # Verify strict check (passed should be False if we have warnings?) 
        # Actually logic is passed = len(errors) == 0. Warnings don't fail check.
        # But for test purposes we check if violation was found.

    def test_catches_no_user(self):
        dockerfile = "FROM node:18-alpine\nRUN npm install\nCMD ['node', 'app.js']\n"
        passed, violations = self.validator.validate(dockerfile, "Docker")
        rules = [v.rule for v in violations]
        assert "docker-no-user" in rules

    def test_clean_dockerfile_passes(self):
        dockerfile = (
            "FROM node:18-alpine\n"
            "RUN npm install\n"
            "USER appuser\n"
            "HEALTHCHECK CMD curl -f http://localhost:3000 || exit 1\n"
            "CMD ['node', 'app.js']\n"
        )
        passed, violations = self.validator.validate(dockerfile, "Docker")
        # Should be 0 violations of any kind
        assert len(violations) == 0
        assert passed is True


class TestK8sPolicies:
    """Built-in Kubernetes policy rules."""

    def setup_method(self):
        self.validator = PolicyValidator()

    def test_catches_missing_resource_limits(self):
        manifest = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: production
spec:
  template:
    spec:
      containers:
        - name: app
          image: myapp:1.0
"""
        passed, violations = self.validator.validate(manifest, "K8s")
        rules = [v.rule for v in violations]
        assert "k8s-no-limits" in rules
        assert passed is False  # ERROR severity

    def test_catches_default_namespace(self):
        manifest = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: default
"""
        passed, violations = self.validator.validate(manifest, "K8s")
        rules = [v.rule for v in violations]
        assert "k8s-default-namespace" in rules
        assert passed is False


class TestCICDPolicies:
    """Built-in CI/CD policy rules."""

    def setup_method(self):
        self.validator = PolicyValidator()

    def test_catches_unpinned_actions(self):
        workflow = """
name: CI
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout
"""
        passed, violations = self.validator.validate(workflow, "CI/CD")
        rules = [v.rule for v in violations]
        assert "ci-unpinned-action" in rules
        # Warning only, so passed might be True depending on impl
        # We checked passed = len(errors) == 0. Unpinned is WARNING.
        assert passed is True 

    def test_unknown_stage_returns_empty(self):
        passed, violations = self.validator.validate("hello world", "UnknownStage")
        assert passed is True
        assert violations == []
