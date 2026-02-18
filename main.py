import os
import sys
import json
import time

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
from src.agents.debugging_agent import DebugWriterA, DebugWriterB, DebugWriterC, DebugReviewer, DebugExecutor
from src.llm_clients.gemini_client import GeminiClient
from src.llm_clients.groq_client import GroqClient
from src.llm_clients.nvidia_client import NvidiaClient

# ================================================================
# SHARED UTILS
# ================================================================
def print_header(title):
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def load_or_run_analysis(project_path):
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

def human_decision():
    """Standard 3-option human decision gate. Returns 'approve', 'refine', or 'reject'."""
    choice = input("✅ Approve (y) / 🔄 Refine (r) / ❌ Reject (n): ").strip().lower()
    if choice == 'y':
        return 'approve'
    elif choice == 'r':
        return 'refine'
    else:
        return 'reject'


# ================================================================
# STAGE 2: Dockerfile
# ================================================================
def run_docker_stage(project_path, context_data):
    print_header("Stage 2: Docker Infrastructure Generation")
    context_str = json.dumps(context_data, indent=2)
    
    # Initialize
    try:
        wa, wb, wc = DockerWriterA(), DockerWriterB(), DockerWriterC()
        reviewer = DockerReviewer()
    except Exception as e:
        print(f"⚠️  API Keys missing ({e}). Using MOCK clients.")
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
    
    # Generate
    print("Drafting Dockerfiles (A-Gemini, B-Groq, C-NVIDIA)...")
    try: d_a = wa.generate(project_path, context=context_str)
    except: d_a = ""
    try: d_b = wb.generate(project_path, context=context_str)
    except: d_b = ""
    try: d_c = wc.generate(project_path, context=context_str)
    except: d_c = ""
    
    # Refine Loop (up to 3 cycles)
    user_feedback = ""
    for i in range(3):
        print(f"\n--- Review Cycle {i+1}/3 ---")
        
        # Deterministic Check
        report = "--- VALIDATION REPORT ---\n"
        if d_a: report += f"Draft A: {det_reviewer.review_dockerfile(d_a)[1]}\n"
        if d_b: report += f"Draft B: {det_reviewer.review_dockerfile(d_b)[1]}\n"
        if d_c: report += f"Draft C: {det_reviewer.review_dockerfile(d_c)[1]}\n"
        if user_feedback:
            report += f"\nUSER FEEDBACK (MUST ADDRESS): {user_feedback}\n"
        
        # AI Review
        final, reasoning = reviewer.review_and_merge(d_a, d_b, d_c, validation_report=report)
        
        print(f"\n🧠 AI Reasoning:\n{reasoning}\n")
        print(f"📄 Proposed Dockerfile:\n{final}\n")
        
        # Guidelines Update
        guidelines_check(reasoning, "configs/guidelines/docker-guidelines.md")
            
        decision = human_decision()
        if decision == 'approve':
            executor.run(final, project_path)
            return True
        elif decision == 'refine':
            user_feedback = input("💬 Your feedback: ")
            print("🔄 Re-running review with your feedback...")
        else:
            return False
            
    print("⚠️  Max refine cycles reached.")
    return False


# ================================================================
# STAGE 3: Docker Compose
# ================================================================
def run_compose_stage(project_path, context_data):
    print_header("Stage 3: Docker Compose Generation")
    ctx_str = json.dumps(context_data, indent=2)
    
    # Initialize
    try:
        writers = [
            DockerComposeWriter(GeminiClient()),
            DockerComposeWriter(GroqClient()),
            DockerComposeWriter(NvidiaClient())
        ]
        reviewer = ComposeReviewer()
    except Exception as e:
        print(f"⚠️  API Keys missing ({e}). Using MOCK clients.")
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
    
    # Generate Drafts
    print("Drafting Compose Files (Gemini, Groq, NVIDIA)...")
    drafts = []
    for idx, w in enumerate(writers):
        try:
            print(f"  - Writer {idx+1} working...")
            drafts.append(w.generate(ctx_str))
        except Exception as e:
            print(f"  ⚠️ Writer {idx+1} failed: {e}")
            drafts.append("")
    while len(drafts) < 3:
        drafts.append("")
    
    # Refine Loop (up to 3 cycles)
    user_feedback = ""
    for i in range(3):
        print(f"\n--- Review Cycle {i+1}/3 ---")
        
        report = ""
        if user_feedback:
            report = f"USER FEEDBACK (MUST ADDRESS): {user_feedback}"
        
        # AI Review
        print("🧠 AI Architect Reviewing Drafts...")
        final_yaml, reasoning = reviewer.review_and_merge(drafts[0], drafts[1], drafts[2], validation_report=report)
        
        print(f"\nReasoning:\n{reasoning}\n")
        print(f"Proposed docker-compose.yml:\n{final_yaml}\n")
        
        # Guidelines Update
        guidelines_check(reasoning, "configs/guidelines/docker-guidelines.md")
        
        decision = human_decision()
        if decision == 'approve':
            executor.run(final_yaml, project_path)
            return True
        elif decision == 'refine':
            user_feedback = input("💬 Your feedback: ")
            print("🔄 Re-running review with your feedback...")
        else:
            return False
    
    print("⚠️  Max refine cycles reached.")
    return False


# ================================================================
# STAGE 4: Kubernetes Manifests
# ================================================================
def run_k8s_stage(project_path, context_data):
    print_header("Stage 4: Kubernetes Manifests")
    ctx_str = json.dumps(context_data, indent=2)
    service_name = context_data.get('project_name', 'myapp')
    
    # Initialize
    try:
        wa, wb, wc = K8sWriterA(), K8sWriterB(), K8sWriterC()
        reviewer = K8sReviewer()
    except Exception as e:
        print(f"⚠️  API Keys missing ({e}). Using MOCK clients.")
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
    
    # Generate Drafts
    print("Drafting Manifests (Gemini, Groq, NVIDIA)...")
    try: y_a = wa.generate(service_name, context=ctx_str)
    except: y_a = ""
    try: y_b = wb.generate(service_name, context=ctx_str)
    except: y_b = ""
    try: y_c = wc.generate(service_name, context=ctx_str)
    except: y_c = ""
    
    # Refine Loop (up to 3 cycles)
    user_feedback = ""
    for i in range(3):
        print(f"\n--- Review Cycle {i+1}/3 ---")
        
        # Deterministic Check
        report = "--- VALIDATION REPORT ---\n"
        if y_a: report += f"Draft A: {det_reviewer.review_k8s(y_a)[1]}\n"
        if y_b: report += f"Draft B: {det_reviewer.review_k8s(y_b)[1]}\n"
        if y_c: report += f"Draft C: {det_reviewer.review_k8s(y_c)[1]}\n"
        if user_feedback:
            report += f"\nUSER FEEDBACK (MUST ADDRESS): {user_feedback}\n"
        
        # AI Review
        print("🧠 AI Architect Reviewing Manifests...")
        final, reasoning = reviewer.review_and_merge(y_a, y_b, y_c, validation_report=report)
        
        print(f"\nReasoning:\n{reasoning}\n")
        print(f"Proposed manifest.yaml:\n{final}\n")
        
        # Guidelines Update
        guidelines_check(reasoning, "configs/guidelines/k8s-guidelines.md")
        
        decision = human_decision()
        if decision == 'approve':
            executor.run(final, os.path.join(project_path, "manifest.yaml"))
            return True
        elif decision == 'refine':
            user_feedback = input("💬 Your feedback: ")
            print("🔄 Re-running review with your feedback...")
        else:
            return False

    print("⚠️  Max refine cycles reached.")
    return False


# ================================================================
# STAGE 5: CI/CD (GitHub Actions)
# ================================================================
def run_cicd_stage(project_path, context_data):
    print_header("Stage 5: CI/CD Generation (GitHub Actions)")
    ctx_str = json.dumps(context_data, indent=2)
    
    # Initialize
    try:
        wa, wb, wc = CIWriterA(), CIWriterB(), CIWriterC()
        reviewer = CIReviewer()
    except:
        print("⚠️  API Keys missing. Using MOCK clients.")
        from src.llm_clients.mock_client import MockClient
        class MockCIWriter:
            def generate(self, ctx): return MockClient("MockCI").call("github actions")
        wa, wb, wc = MockCIWriter(), MockCIWriter(), MockCIWriter()
        class MockCIReviewer:
            def review_and_merge(self, a, b, c, validation_report=""):
                return (a, "Mock CI Review: Combined security and speed steps.")
        reviewer = MockCIReviewer()
        
    executor = CIExecutor()
    
    # Generate
    print("Drafting Workflows (Gemini, Groq, NVIDIA)...")
    try: d_a = wa.generate(ctx_str)
    except: d_a = ""
    try: d_b = wb.generate(ctx_str)
    except: d_b = ""
    try: d_c = wc.generate(ctx_str)
    except: d_c = ""
    
    # Refine Loop (up to 3 cycles)
    user_feedback = ""
    for i in range(3):
        print(f"\n--- Review Cycle {i+1}/3 ---")
        
        report = ""
        if user_feedback:
            report = f"USER FEEDBACK (MUST ADDRESS): {user_feedback}"
        
        # AI Review
        print("🧠 AI Architect Merging Workflows...")
        final, reasoning = reviewer.review_and_merge(d_a, d_b, d_c, validation_report=report)
        
        print(f"\nReasoning:\n{reasoning}\n")
        print(f"Proposed .github/workflows/main.yml:\n{final}\n")
        
        # Guidelines Update
        guidelines_check(reasoning, "configs/guidelines/ci-guidelines.md")
        
        decision = human_decision()
        if decision == 'approve':
            executor.run(final, project_path)
            return True
        elif decision == 'refine':
            user_feedback = input("💬 Your feedback: ")
            print("🔄 Re-running review with your feedback...")
        else:
            return False

    print("⚠️  Max refine cycles reached.")
    return False


# ================================================================
# STAGE 6: Observability (Helm)
# ================================================================
def run_observability_stage(project_path, context_data):
    print_header("Stage 6: Observability (Helm Chart)")
    ctx_str = json.dumps(context_data, indent=2)
    
    # Initialize
    try:
        wa, wb, wc = ObservabilityWriterA(), ObservabilityWriterB(), ObservabilityWriterC()
        reviewer = ObservabilityReviewer()
    except:
        print("⚠️  API Keys missing. Using MOCK clients.")
        from src.llm_clients.mock_client import MockClient
        class MockObsWriter:
            def generate(self, ctx): return MockClient("MockObs").call("helm chart")
        wa, wb, wc = MockObsWriter(), MockObsWriter(), MockObsWriter()
        class MockObsReviewer:
            def review_and_merge(self, a, b, c, validation_report=""):
                a_clean = a.replace("```yaml", "").replace("```", "")
                return (a_clean, "Mock Review: Standard Prometheus/Loki stack selected.")
        reviewer = MockObsReviewer()
        
    executor = ObservabilityExecutor()
    
    # Generate
    print("Drafting Helm Charts (Gemini, Groq, NVIDIA)...")
    try: d_a = wa.generate(ctx_str)
    except: d_a = ""
    try: d_b = wb.generate(ctx_str)
    except: d_b = ""
    try: d_c = wc.generate(ctx_str)
    except: d_c = ""
    
    # Refine Loop (up to 3 cycles)
    user_feedback = ""
    for i in range(3):
        print(f"\n--- Review Cycle {i+1}/3 ---")
        
        report = ""
        if user_feedback:
            report = f"USER FEEDBACK (MUST ADDRESS): {user_feedback}"
        
        # AI Review
        print("🧠 AI Architect Merging Charts...")
        final, reasoning = reviewer.review_and_merge(d_a, d_b, d_c, validation_report=report)
        
        print(f"\nReasoning:\n{reasoning}\n")
        print(f"Proposed helm/monitoring/Chart.yaml:\n{final}\n")
        
        # Guidelines Update (no specific helm guidelines yet, uses k8s)
        guidelines_check(reasoning, "configs/guidelines/k8s-guidelines.md")
        
        decision = human_decision()
        if decision == 'approve':
            executor.run(final, project_path)
            return True
        elif decision == 'refine':
            user_feedback = input("💬 Your feedback: ")
            print("🔄 Re-running review with your feedback...")
        else:
            return False

    print("⚠️  Max refine cycles reached.")
    return False


# ================================================================
# STAGE 7: Debugging / Troubleshooting
# ================================================================
def run_debug_stage(project_path, context_data):
    print_header("Stage 7: Debugging & Troubleshooting")
    ctx_str = json.dumps(context_data, indent=2)
    
    # Get error input
    print("Provide the error/log to analyze.")
    print("Options:")
    print("  1. Paste error text directly")
    print("  2. Provide path to a log file")
    input_choice = input("Choice (1/2): ").strip()
    
    if input_choice == '2':
        log_path = input("Log file path: ").strip()
        try:
            from src.tools.file_ops import read_file
            error_input = read_file(log_path)
        except:
            print("❌ Could not read log file.")
            return False
    else:
        print("Paste error (type END on a new line when done):")
        lines = []
        while True:
            line = input()
            if line.strip() == 'END':
                break
            lines.append(line)
        error_input = '\n'.join(lines)
    
    if not error_input.strip():
        print("❌ No input provided.")
        return False
    
    # Initialize
    try:
        wa, wb, wc = DebugWriterA(), DebugWriterB(), DebugWriterC()
        reviewer = DebugReviewer()
    except:
        print("⚠️  API Keys missing. Using MOCK clients.")
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
    
    # Analyze
    print("\n🔍 Analyzing error with 3 specialists...")
    try: a_rca = wa.analyze(error_input, context=ctx_str)
    except: a_rca = "Analysis failed."
    try: a_sec = wb.analyze(error_input, context=ctx_str)
    except: a_sec = "Analysis failed."
    try: a_perf = wc.analyze(error_input, context=ctx_str)
    except: a_perf = "Analysis failed."
    
    # Refine Loop (up to 3 cycles)
    user_feedback = ""
    for i in range(3):
        print(f"\n--- Review Cycle {i+1}/3 ---")
        
        report = ""
        if user_feedback:
            report = f"USER FEEDBACK (MUST ADDRESS): {user_feedback}"
        
        # Lead SRE Review
        print("🧠 Lead SRE Synthesizing Incident Report...")
        incident_report, reasoning = reviewer.review_and_merge(a_rca, a_sec, a_perf, validation_report=report)
        
        print(f"\nKey Findings:\n{reasoning}\n")
        print(f"📋 Incident Report:\n{incident_report}\n")
        
        decision = human_decision()
        if decision == 'approve':
            executor.run(incident_report, project_path)
            return True
        elif decision == 'refine':
            user_feedback = input("💬 Your feedback (e.g. 'also check for memory leaks'): ")
            print("🔄 Re-running analysis with your feedback...")
        else:
            return False

    print("⚠️  Max refine cycles reached.")
    return False


# ================================================================
# MAIN WIZARD
# ================================================================
def main():
    print_header("DevOps AI Agent Pipeline v3.0")
    
    project_path = input("Enter project path: ").strip()
    if not os.path.exists(project_path):
        print("❌ Path does not exist")
        return

    # STEP 1: ANALYSIS
    print_header("Stage 1: Code Analysis & Caching")
    context = load_or_run_analysis(project_path)
    print(f"✅ Context Loaded: {context['language']} app, Ports: {context.get('ports')}")
    
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
        
        if choice == '2':
            run_docker_stage(project_path, context)
        elif choice == '3':
            run_compose_stage(project_path, context)
        elif choice == '4':
            run_k8s_stage(project_path, context)
        elif choice == '5':
            run_cicd_stage(project_path, context)
        elif choice == '6':
            run_observability_stage(project_path, context)
        elif choice == '7':
            run_debug_stage(project_path, context)
        elif choice == '0':
            break
        else:
            print("⏳ Not implemented yet.")

if __name__ == "__main__":
    main()
