import os
import sys
import json
import time
import logging

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.code_analysis_agent import CodeAnalysisAgent
from src.agents.docker_agents import DockerWriterA, DockerWriterB, DockerWriterC, DockerReviewer, DockerExecutor
from src.agents.k8s_agents import K8sWriterA, K8sWriterB, K8sWriterC, K8sReviewer, K8sExecutor
from src.agents.deterministic_reviewer import DeterministicReviewer
from src.agents.guidelines_compliance_agent import GuidelinesComplianceAgent
from src.agents.docker_compose_agent import DockerComposeWriter, ComposeReviewer, DockerComposeExecutor
from src.agents.cicd_agent import CIWriterA, CIWriterB, CIWriterC, CIReviewer, CIExecutor
from src.agents.observability_agent import ObservabilityWriterA, ObservabilityWriterB, ObservabilityWriterC, ObservabilityReviewer, ObservabilityExecutor
from src.agents.cost_agent import CostEstimator, CostExecutor
from src.agents.debugging_agent import DebugWriterA, DebugWriterB, DebugWriterC, DebugReviewer, DebugExecutor
from src.llm_clients.gemini_client import GeminiClient
from src.llm_clients.groq_client import GroqClient
from src.llm_clients.nvidia_client import NvidiaClient
from src.utils.resilience import safe_llm_call
from src.utils.sanitizer import sanitize_feedback
from src.utils.logger import get_logger, set_correlation_id, configure_logging
from src.utils.parallel import run_writers_parallel
from src.audit.decision_log import AuditLog
from src.policy.validator import PolicyValidator
from src.gitops.pr_creator import GitOpsPublisher
from src.schemas import ProjectContext, StageResult, Decision, Severity, PolicyViolation

logger = get_logger("devops-agent.pipeline")

# ================================================================
# SHARED UTILS
# ================================================================
def print_header(title):
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def load_or_run_analysis(project_path) -> ProjectContext:
    agent = CodeAnalysisAgent(project_path)
    return agent.get_cached_analysis()

def guidelines_check(reasoning, guidelines_path):
    """Run GuidelinesComplianceAgent and print results."""
    try:
        gate = GuidelinesComplianceAgent().analyze_and_update(reasoning, guidelines_path)
        if gate['new_practices_found']:
            print(f"🛡️  New Best Practices Learned: {gate['added_points']}")
        return gate
    except Exception as e:
        print(f"  (Guidelines check skipped: {e})")
        return {"new_practices_found": False, "added_points": []}

def human_decision() -> Decision:
    """Standard 3-option human decision gate."""
    choice = input("\n✅ Approve (y) / 🔄 Refine (r) / ❌ Reject (n): ").strip().lower()
    if choice == 'y':
        return Decision.APPROVE
    elif choice == 'r':
        return Decision.REFINE
    else:
        return Decision.REJECT

def stage_decision_loop(stage_name, reviewer, drafts, executor, run_executor_fn,
                        guidelines_path, audit, det_reviewer=None, det_fn=None,
                        publisher=None, output_files=None, project_path="", run_id="") -> StageResult:
    """
    Shared refine loop logic across all stages.
    """
    policy_validator = PolicyValidator()
    user_feedback = ""
    
    for i in range(3):
        logger.info("Review cycle %d/3", i + 1, extra={"stage": stage_name})
        print(f"\n--- Review Cycle {i+1}/3 ---")
        
        report = ""
        if det_reviewer and det_fn:
            report = "--- VALIDATION REPORT ---\n"
            labels = ["Draft A", "Draft B", "Draft C"]
            for idx, d in enumerate(drafts):
                if d:
                    report += f"{labels[idx]}: {det_fn(det_reviewer, d)[1]}\n"
        if user_feedback:
            report += f"\nUSER FEEDBACK (MUST ADDRESS): {user_feedback}\n"
        
        # AI Review
        logger.info("AI review starting", extra={"stage": stage_name})
        final, reasoning = reviewer.review_and_merge(drafts[0], drafts[1], drafts[2], validation_report=report)
        
        print(f"\n🧠 AI Reasoning:\n{reasoning}\n")
        print(f"📄 Proposed Output:\n{final}\n")
        
        # Policy Gate
        passed, violations = policy_validator.validate(final, stage_name)
        if violations:
            print(f"\n🛡️  Policy Check ({len(violations)} finding(s)):")
            for v in violations:
                icon = "❌" if v.severity == Severity.ERROR else "⚠️"
                print(f"  {icon} [{v.severity.value.upper()}] {v.rule}: {v.message}")
            if not passed:
                print("⛔ Critical policy violations found. Please refine.")
        else:
            print("✅ Policy check passed.")
        
        guidelines_check(reasoning, guidelines_path)
        
        decision = human_decision()
        audit.record(stage=stage_name, decision=decision.value, reasoning=reasoning,
                     user_feedback=user_feedback, cycle=i + 1, drafts_count=sum(1 for d in drafts if d))
        
        if decision == Decision.APPROVE:
            published_via = None
            if publisher and output_files:
                files = {fname: final for fname in output_files}
                result = publisher.publish(
                    files=files, stage=stage_name, run_id=run_id,
                    reasoning=reasoning, project_path=project_path,
                )
                if result["mode"] == "pr":
                    print(f"🚀 PR created: {result['url']}")
                    published_via = "github_pr"
                elif result["mode"] == "local":
                    print(f"✅ Written locally: {', '.join(result['paths'])}")
                    published_via = "local_write"
                else:
                    # Fallback failed — use executor directly
                    run_executor_fn(final)
                    published_via = "local_exec"
            else:
                run_executor_fn(final)
                published_via = "local_exec"
                
            logger.info("Stage approved", extra={"stage": stage_name, "decision": "approve"})
            return StageResult(
                stage_name=stage_name,
                status=Decision.APPROVE,
                content=final,
                reasoning=reasoning,
                policy_violations=violations,
                cycles=i+1,
                published_via=published_via
            )
            
        elif decision == Decision.REFINE:
            user_feedback = sanitize_feedback(input("💬 Your feedback: "))
            logger.info("Refine requested", extra={"stage": stage_name, "decision": "refine"})
        else:
            logger.info("Stage rejected", extra={"stage": stage_name, "decision": "reject"})
            return StageResult(
                stage_name=stage_name,
                status=Decision.REJECT,
                policy_violations=violations,
                cycles=i+1
            )
    
    logger.warning("Max refine cycles reached", extra={"stage": stage_name})
    print("⚠️  Max refine cycles reached.")
    return StageResult(
        stage_name=stage_name,
        status=Decision.REJECT,
        reasoning="Max cycles reached",
        cycles=3
    )


# ================================================================
# STAGE 2: Dockerfile
# ================================================================
def run_docker_stage(project_path, context: ProjectContext, audit, publisher=None, run_id="") -> StageResult:
    print_header("Stage 2: Docker Infrastructure Generation")
    context_str = context.model_dump_json(indent=2)
    
    # Initialize
    try:
        wa, wb, wc = DockerWriterA(), DockerWriterB(), DockerWriterC()
        reviewer = DockerReviewer()
    except Exception as e:
        logger.warning("API Keys missing, using mocks: %s", e)
        from src.llm_clients.mock_client import MockClient
        class MockWriter:
            def generate(self, p, context=""): return MockClient("MockDocker").call("review")
        wa, wb, wc = MockWriter(), MockWriter(), MockWriter()
        class MockDockerReviewer:
            def review_and_merge(self, a, b, c, validation_report=""):
                resp = MockClient("PerplexityMock").call("review")
                if "DOCKERFILE:" in resp:
                    parts = resp.split("DOCKERFILE:")
                    return (parts[1].strip(), parts[0].replace("REASONING:", "").strip())
                return (resp, "Mock reasoning")
        reviewer = MockDockerReviewer()
        
    det_reviewer, executor = DeterministicReviewer(), DockerExecutor()
    
    # Generate in parallel
    logger.info("Generating drafts in parallel", extra={"stage": "Docker"})
    print("Drafting Dockerfiles in parallel (Gemini, Groq, NVIDIA)...")
    drafts = run_writers_parallel(
        writers=[(wa, "Gemini"), (wb, "Groq"), (wc, "NVIDIA")],
        generate_fn=lambda w, ctx: w.generate(context=ctx),
        context=context_str,
        stage="Docker",
    )
    
    return stage_decision_loop(
        stage_name="Docker", reviewer=reviewer, drafts=drafts,
        executor=executor, run_executor_fn=lambda final: executor.run(final, project_path),
        guidelines_path="configs/guidelines/docker-guidelines.md", audit=audit,
        det_reviewer=det_reviewer, det_fn=lambda r, d: r.review_dockerfile(d),
        publisher=publisher, output_files={"Dockerfile": None},
        project_path=project_path, run_id=run_id,
    )


# ================================================================
# STAGE 3: Docker Compose
# ================================================================
def run_compose_stage(project_path, context: ProjectContext, audit, publisher=None, run_id="") -> StageResult:
    print_header("Stage 3: Docker Compose Generation")
    ctx_str = context.model_dump_json(indent=2)
    
    # Initialize
    try:
        writers = [
            DockerComposeWriter(GeminiClient()),
            DockerComposeWriter(GroqClient()),
            DockerComposeWriter(NvidiaClient())
        ]
        reviewer = ComposeReviewer()
    except Exception as e:
        logger.warning("API Keys missing, using mocks: %s", e)
        from src.llm_clients.mock_client import MockClient
        writers = [
            DockerComposeWriter(MockClient("GeminiMock")),
            DockerComposeWriter(MockClient("GroqMock")),
            DockerComposeWriter(MockClient("NvidiaMock"))
        ]
        class MockReviewer:
            def review_and_merge(self, a, b, c, validation_report=""):
                resp = MockClient("PerplexityMock").call("docker-compose review")
                return (resp, "Mock Compose reasoning.")
        reviewer = MockReviewer()
    executor = DockerComposeExecutor()
    
    # Generate in parallel
    logger.info("Generating drafts in parallel", extra={"stage": "Compose"})
    print("Drafting Compose Files in parallel (Gemini, Groq, NVIDIA)...")
    drafts = run_writers_parallel(
        writers=[(writers[0], "Gemini"), (writers[1], "Groq"), (writers[2], "NVIDIA")],
        generate_fn=lambda w, ctx: w.generate(ctx),
        context=ctx_str,
        stage="Compose",
    )
    
    return stage_decision_loop(
        stage_name="Compose", reviewer=reviewer, drafts=drafts,
        executor=executor, run_executor_fn=lambda final: executor.run(final, project_path),
        guidelines_path="configs/guidelines/docker-guidelines.md", audit=audit,
        publisher=publisher, output_files={"docker-compose.yml": None},
        project_path=project_path, run_id=run_id,
    )


# ================================================================
# STAGE 4: Kubernetes Manifests
# ================================================================
def run_k8s_stage(project_path, context: ProjectContext, audit, publisher=None, run_id="") -> StageResult:
    print_header("Stage 4: Kubernetes Manifests")
    ctx_str = context.model_dump_json(indent=2)
    service_name = context.project_name or 'myapp'
    
    # Initialize
    try:
        wa, wb, wc = K8sWriterA(), K8sWriterB(), K8sWriterC()
        reviewer = K8sReviewer()
    except Exception as e:
        logger.warning("API Keys missing, using mocks: %s", e)
        from src.llm_clients.mock_client import MockClient
        class MockK8sWriter:
            def generate(self, name, context=""): return MockClient("MockK8s").call("kubernetes")
        wa, wb, wc = MockK8sWriter(), MockK8sWriter(), MockK8sWriter()
        class MockK8sReviewer:
            def review_and_merge(self, a, b, c, validation_report=""):
                resp = MockClient("PerplexityMock").call("review kubernetes manifest")
                if "YAML:" in resp:
                    parts = resp.split("YAML:")
                    return (parts[1].replace("```yaml", "").replace("```", "").strip(), parts[0].replace("REASONING:", "").strip())
                return (resp, "Mock reasoning")
        reviewer = MockK8sReviewer()
        
    det_reviewer = DeterministicReviewer()
    executor = K8sExecutor()
    
    # Generate in parallel
    logger.info("Generating drafts in parallel", extra={"stage": "K8s"})
    print("Drafting Manifests in parallel (Gemini, Groq, NVIDIA)...")
    drafts = run_writers_parallel(
        writers=[(wa, "Gemini"), (wb, "Groq"), (wc, "NVIDIA")],
        generate_fn=lambda w, ctx: w.generate(context=ctx),
        context=ctx_str,
        stage="K8s",
    )
    
    return stage_decision_loop(
        stage_name="K8s", reviewer=reviewer, drafts=drafts,
        executor=executor, run_executor_fn=lambda final: executor.run(final, os.path.join(project_path, "manifest.yaml")),
        guidelines_path="configs/guidelines/k8s-guidelines.md", audit=audit,
        det_reviewer=det_reviewer, det_fn=lambda r, d: r.review_k8s(d),
        publisher=publisher, output_files={"manifest.yaml": None},
        project_path=project_path, run_id=run_id,
    )


# ================================================================
# STAGE 5: CI/CD (GitHub Actions)
# ================================================================
def run_cicd_stage(project_path, context: ProjectContext, audit, publisher=None, run_id="") -> StageResult:
    print_header("Stage 5: CI/CD Generation (GitHub Actions)")
    ctx_str = context.model_dump_json(indent=2)
    
    # Initialize
    try:
        wa, wb, wc = CIWriterA(), CIWriterB(), CIWriterC()
        reviewer = CIReviewer()
    except Exception as e:
        logger.warning("API Keys missing, using mocks: %s", e)
        from src.llm_clients.mock_client import MockClient
        class MockCIWriter:
            def generate(self, ctx): return MockClient("MockCI").call("github actions")
        wa, wb, wc = MockCIWriter(), MockCIWriter(), MockCIWriter()
        class MockCIReviewer:
            def review_and_merge(self, a, b, c, validation_report=""):
                return (a, "Mock CI Review: Combined security and speed steps.")
        reviewer = MockCIReviewer()
        
    executor = CIExecutor()
    
    # Generate in parallel
    logger.info("Generating drafts in parallel", extra={"stage": "CI/CD"})
    print("Drafting Workflows in parallel (Gemini, Groq, NVIDIA)...")
    drafts = run_writers_parallel(
        writers=[(wa, "Gemini"), (wb, "Groq"), (wc, "NVIDIA")],
        generate_fn=lambda w, ctx: w.generate(ctx),
        context=ctx_str,
        stage="CI/CD",
    )
    
    return stage_decision_loop(
        stage_name="CI/CD", reviewer=reviewer, drafts=drafts,
        executor=executor, run_executor_fn=lambda final: executor.run(final, project_path),
        guidelines_path="configs/guidelines/ci-guidelines.md", audit=audit,
        publisher=publisher, output_files={".github/workflows/main.yml": None},
        project_path=project_path, run_id=run_id,
    )


# ================================================================
# STAGE 6: Observability (Helm)
# ================================================================
def run_observability_stage(project_path, context: ProjectContext, audit, publisher=None, run_id="") -> StageResult:
    print_header("Stage 6: Observability (Helm & Dashboards)")
    ctx_str = context.model_dump_json(indent=2)

    print("Select output type:")
    print("1. Helm Chart (Prometheus/Loki) [default]")
    print("2. Grafana Dashboard JSON")
    sub_choice = input("Choice (1/2): ").strip()
    
    is_dashboard = (sub_choice == '2')
    target_desc = "Grafana Dashboard" if is_dashboard else "Helm Chart"
    
    # Initialize
    try:
        wa, wb, wc = ObservabilityWriterA(), ObservabilityWriterB(), ObservabilityWriterC()
        reviewer = ObservabilityReviewer()
    except Exception as e:
        logger.warning("API Keys missing, using mocks: %s", e)
        from src.llm_clients.mock_client import MockClient
        class MockObsWriter:
            def generate(self, ctx): return MockClient("MockObs").call("helm chart")
            def generate_dashboard(self, ctx): return MockClient("MockObs").call("grafana dashboard json")
        wa, wb, wc = MockObsWriter(), MockObsWriter(), MockObsWriter()
        class MockObsReviewer:
            def review_and_merge(self, a, b, c, validation_report=""):
                if a.strip().startswith("{"):
                    return (a, "Mock Review: Valid JSON dashboard structure confirmed.")
                a_clean = a.replace("```yaml", "").replace("```", "")
                return (a_clean, "Mock Review: Standard Prometheus/Loki stack selected.")
        reviewer = MockObsReviewer()
        
    executor = ObservabilityExecutor()
    
    generate_fn = (lambda w, ctx: w.generate_dashboard(context=ctx)) if is_dashboard else (lambda w, ctx: w.generate(ctx))
    output_files = {"k8s/dashboards/dashboard.json": None} if is_dashboard else {"helm/monitoring/Chart.yaml": None}
    
    # Generate in parallel
    logger.info("Generating drafts in parallel", extra={"stage": "Observability", "type": target_desc})
    print(f"Drafting {target_desc}s in parallel (Gemini, Groq, NVIDIA)...")
    drafts = run_writers_parallel(
        writers=[(wa, "Gemini"), (wb, "Groq"), (wc, "NVIDIA")],
        generate_fn=generate_fn,
        context=ctx_str,
        stage="Observability",
    )
    
    return stage_decision_loop(
        stage_name="Observability", reviewer=reviewer, drafts=drafts,
        executor=executor, run_executor_fn=lambda final: executor.run(final, project_path),
        guidelines_path="configs/guidelines/k8s-guidelines.md", audit=audit,
        publisher=publisher, output_files=output_files,
        project_path=project_path, run_id=run_id,
    )


# ================================================================
# STAGE 7: Debugging / Troubleshooting
# ================================================================
def run_debug_stage(project_path, context: ProjectContext, audit, publisher=None, run_id="") -> StageResult:
    print_header("Stage 7: Debugging & Troubleshooting")
    ctx_str = context.model_dump_json(indent=2)
    
    # Get error input
    print("Provide the error/log to analyze.")
    print("Options:")
    print("  1. Paste error text directly")
    print("  2. Provide path to a log file")
    input_choice = input("Choice (1/2): ").strip()
    
    error_input = ""
    if input_choice == '2':
        log_path = input("Log file path: ").strip()
        try:
            from src.tools.file_ops import read_file
            error_input = read_file(log_path)
        except Exception as e:
            logger.error("Could not read log file: %s", e)
            print(f"❌ Could not read log file: {e}")
            return StageResult(stage_name="Debug", status=Decision.REJECT, reasoning=f"File error: {e}")
    else:
        print("Paste error (type END on a new line when done):")
        lines = []
        while True:
            line = input()
            if line.strip() == 'END':
                break
        error_input = '\n'.join(lines)
    
    if not error_input.strip():
        print("❌ No input provided.")
    
    return StageResult(stage_name="Debug", status=Decision.APPROVE, reasoning="Debugging complete")


# ================================================================
# STAGE 8: Cloud Cost Estimation (FinOps)
# ================================================================
def run_cost_stage(project_path, context: ProjectContext, run_id="") -> StageResult:
    print_header("Stage 8: Cloud Cost Estimation (FinOps)")
    
    # Check if K8s manifest exists
    manifest_path = os.path.join(project_path, "manifest.yaml")
    if not os.path.exists(manifest_path):
        print("⚠️  No K8s manifest found. Skipping cost estimation.")
        return StageResult(stage_name="Cost", status=Decision.REJECT, reasoning="No manifest found")
        
    try:
        from src.tools.file_ops import read_file
        manifest_content = read_file(manifest_path)
    except Exception as e:
        logger.error("Failed to read manifest: %s", e)
        return StageResult(stage_name="Cost", status=Decision.REJECT, reasoning=f"Read error: {e}")
        
    print("Estimating monthly cloud costs based on manifests...")
        estimator = CostEstimator()
        report = estimator.estimate(manifest_content)
        
        executor = CostExecutor()
        executor.run(report, project_path)
        
        print("\n" + "="*40)
        print("COST ESTIMATION REPORT")
        print("="*40)
        print(report)
        print("="*40 + "\n")
        
        return StageResult(stage_name="Cost", status=Decision.APPROVE, reasoning="Estimation complete")
    except Exception as e:
        logger.error("Cost estimation failed: %s", e)
        print(f"❌ Cost estimation failed: {e}")
        return StageResult(stage_name="Cost", status=Decision.REJECT, reasoning=f"Error: {e}")

    
    # Initialize
    try:
        wa, wb, wc = DebugWriterA(), DebugWriterB(), DebugWriterC()
        reviewer = DebugReviewer()
    except Exception as e:
        logger.warning("API Keys missing, using mocks: %s", e)
        from src.llm_clients.mock_client import MockClient
        class MockDebugA:
            def analyze(self, err, context=""): return MockClient("RCA").call(f"root cause analysis: {err[:100]}")
        class MockDebugB:
            def analyze(self, err, context=""): return MockClient("Security").call(f"security engineer analyzing: {err[:100]}")
        class MockDebugC:
            def analyze(self, err, context=""): return MockClient("Perf").call(f"performance engineer analyzing: {err[:100]}")
        wa, wb, wc = MockDebugA(), MockDebugB(), MockDebugC()
        class MockDebugReviewer:
            def review_and_merge(self, a, b, c, validation_report=""):
                resp = MockClient("LeadSRE").call("lead sre incident report review")
                if "REPORT:" in resp:
                    parts = resp.split("REPORT:", 1)
                    return (parts[1].strip(), parts[0].replace("REASONING:", "").strip())
                return (resp, "Mock review")
        reviewer = MockDebugReviewer()
    
    executor = DebugExecutor()
    
    # Analyze in parallel
    logger.info("Analyzing with 3 specialists in parallel", extra={"stage": "Debug"})
    print("\n🔍 Analyzing error with 3 specialists in parallel...")
    drafts = run_writers_parallel(
        writers=[(wa, "RCA-Gemini"), (wb, "Security-Groq"), (wc, "Perf-NVIDIA")],
        generate_fn=lambda w, ctx: w.analyze(error_input, context=ctx),
        context=ctx_str,
        stage="Debug",
    )
    # Replace empty strings with failure message for debug
    drafts = [d if d else "Analysis failed." for d in drafts]
    
    import time as _time
    timestamp = _time.strftime("%Y%m%d_%H%M%S")
    return stage_decision_loop(
        stage_name="Debug", reviewer=reviewer, drafts=drafts,
        executor=executor, run_executor_fn=lambda final: executor.run(final, project_path),
        guidelines_path="configs/guidelines/k8s-guidelines.md", audit=audit,
        publisher=publisher, output_files={f"debug_reports/incident_{timestamp}.md": None},
        project_path=project_path, run_id=run_id,
    )


# ================================================================
# MAIN WIZARD
# ================================================================
def main():
    configure_logging(json_mode=os.environ.get("LOG_JSON", "").lower() == "true")
    run_id = set_correlation_id()
    audit = AuditLog(run_id=run_id)
    publisher = GitOpsPublisher()
    
    print_header(f"DevOps AI Agent Pipeline v9.0 [run:{run_id}]")
    logger.info("Pipeline started | gitops_mode=%s", publisher.mode, extra={"stage": "init"})
    
    project_path = input("Enter project path: ").strip()
    if not os.path.exists(project_path):
        print("❌ Path does not exist")
        return

    # STEP 1: ANALYSIS
    print_header("Stage 1: Code Analysis & Caching")
    context = load_or_run_analysis(project_path)
    logger.info("Context loaded: %s app", context.language, extra={"stage": "Analysis"})
    print(f"✅ Context Loaded: {context.language} app, Ports: {context.ports}")
    
    while True:
        print("\n--- Pipeline Menu ---")
        print("2. [Docker]        Generate Dockerfile")
        print("3. [Compose]       Generate Docker Compose")
        print("4. [K8s]           Generate Kubernetes Manifests")
        print("5. [CI/CD]         Generate GitHub Actions")
        print("6. [Observability] Generate Helm/Monitoring")
        print("7. [Debug]         Troubleshoot Errors")
        print("0. Exit")
        
        choice = input("Run Stage: ")
        
        result = None
        if choice == '2':
            result = run_docker_stage(project_path, context, audit, publisher, run_id)
        elif choice == '3':
            result = run_compose_stage(project_path, context, audit, publisher, run_id)
        elif choice == '4':
            result = run_k8s_stage(project_path, context, audit, publisher, run_id)
        elif choice == '5':
            result = run_cicd_stage(project_path, context, audit, publisher, run_id)
        elif choice == '6':
            result = run_observability_stage(project_path, context, audit, publisher, run_id)
        elif choice == '8': # New elif for Cost
            result = run_cost_stage(project_path, context, run_id)
        elif choice == '7':
            result = run_debug_stage(project_path, context, audit, publisher, run_id)
        elif choice == '0':
            break
        else:
            print("⏳ Not implemented yet.")
            continue
            
        if result and result.status == Decision.APPROVE:
            print(f"🎉 Stage {result.stage_name} completed successfully.")
        
    # Save audit trail on exit
    audit_path = audit.save()
    print(f"\n📝 Audit log saved: {audit_path}")
    print(audit.summary())
    logger.info("Pipeline completed", extra={"stage": "exit"})

if __name__ == "__main__":
    main()
