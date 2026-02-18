"""
Decision Audit Trail — Records every human/AI decision for compliance.

Usage:
    from src.audit.decision_log import AuditLog

    audit = AuditLog(run_id="abc123")
    audit.record(stage="Docker", decision="approve", reasoning="Clean build")
    audit.save()
"""

import json
import os
import time
import logging

logger = logging.getLogger("devops-agent.audit")

_AUDIT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "audit_logs")


class AuditLog:
    """
    Records all decisions made during a pipeline run.
    Writes to audit_logs/<run_id>.json at the end.
    """

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.entries: list[dict] = []

    def record(
        self,
        stage: str,
        decision: str,
        reasoning: str = "",
        user_feedback: str = "",
        cycle: int = 0,
        drafts_count: int = 0,
    ):
        """Record a single decision event."""
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "stage": stage,
            "decision": decision,
            "cycle": cycle,
        }
        if reasoning:
            entry["ai_reasoning"] = reasoning[:500]
        if user_feedback:
            entry["user_feedback"] = user_feedback[:500]
        if drafts_count:
            entry["drafts_received"] = drafts_count

        self.entries.append(entry)
        logger.info(
            "Audit | stage=%s | decision=%s | cycle=%d",
            stage, decision, cycle,
            extra={"stage": stage, "decision": decision},
        )

    def record_generation(
        self,
        stage: str,
        model: str,
        success: bool,
        latency: float = 0.0,
    ):
        """Record a writer generation attempt."""
        self.entries.append({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "stage": stage,
            "event": "generation",
            "model": model,
            "success": success,
            "latency_s": round(latency, 2),
        })

    def save(self):
        """Write the audit log to disk."""
        os.makedirs(_AUDIT_DIR, exist_ok=True)
        filepath = os.path.join(_AUDIT_DIR, f"{self.run_id}.json")
        record = {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_decisions": len([e for e in self.entries if "decision" in e]),
            "entries": self.entries,
        }
        with open(filepath, "w") as f:
            json.dump(record, f, indent=2)

        logger.info(
            "Audit log saved | run_id=%s | entries=%d | path=%s",
            self.run_id, len(self.entries), filepath,
        )
        return filepath

    def summary(self) -> str:
        """Return human-readable summary of decisions."""
        decisions = [e for e in self.entries if "decision" in e]
        approved = sum(1 for d in decisions if d["decision"] == "approve")
        rejected = sum(1 for d in decisions if d["decision"] == "reject")
        refined = sum(1 for d in decisions if d["decision"] == "refine")
        return (
            f"Pipeline Run: {self.run_id}\n"
            f"  Approved: {approved} | Rejected: {rejected} | Refined: {refined}"
        )
