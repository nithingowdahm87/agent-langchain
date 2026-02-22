from typing import List, Dict, Any
import logging

# Schemas
from src.schemas import ProjectContext, Decision, StageResult
from src.decision_engine.contracts.architecture_plan import ArchitecturePlan
from src.decision_engine.contracts.infra_spec import InfraSpec
from src.decision_engine.contracts.decision_result import DecisionResult

# Modules
from src.decision_engine.planner.architecture_planner import ArchitecturePlanner
from src.decision_engine.generator.llm_generator import LLMGenerator
from src.decision_engine.scoring.scorecard import weighted_score
from src.decision_engine.scoring.evaluator import Evaluator
from src.decision_engine.repair.repair_agent import RepairAgent
from src.decision_engine.confidence.confidence_score import compute_confidence
from src.decision_engine.confidence.action_router import decide_action
from src.utils.prompt_loader import load_prompt
from src.memory.long_term_memory import LongTermMemory

# Clients
from src.llm_clients.gemini_client import GeminiClient
from src.llm_clients.groq_client import GroqClient
from src.llm_clients.nvidia_client import NvidiaClient
from src.llm_clients.mock_client import MockClient

# Tools
from src.tools.file_ops import write_file

logger = logging.getLogger("devops-agent")

class V2Orchestrator:
    def __init__(self):
        self.planner = ArchitecturePlanner()
        self.evaluator = Evaluator()
        self.repair_agent = RepairAgent()
        self.memory = None # Init later with project_path
        
        # Initialize Generators (Safe Layout)
        self.generators = []
        self._init_generators()
        
    def _init_generators(self):
        """Try to init real clients, fallback to mock."""
        clients = [
            ("Gemini", GeminiClient),
            ("Groq", GroqClient),
            ("NVIDIA", NvidiaClient)
        ]
        
        for name, cls in clients:
            try:
                client = cls()
                self.generators.append(LLMGenerator(client, name))
            except Exception as e:
                logger.warning(f"Failed to init {name} client: {e}. Using Mock.")
                self.generators.append(LLMGenerator(MockClient(name=f"Mock-{name}"), f"Mock-{name}"))
        
    def run_pipeline(self, project_path: str, context: ProjectContext):
        """
        Main entry point for V2 Pipeline.
        """
        logger.info("🚀 Starting V2 Decision Engine Pipeline")
        self.memory = LongTermMemory(project_path)

        
        # 1. Plan Architecture
        plan = self.planner.create_plan(context)
        print(f"🏗️  Architecture Plan: {plan.service_type.upper()} | Scaling: {plan.scaling_strategy} | DB: {plan.requires_database}")
        
        # 2. Print rich analysis summary
        is_mono = "microservices" not in context.architecture
        num_dockerfiles = len(context.microservice_dirs) if not is_mono else 1

        dbs = context.databases if context.databases else {}

        # Normalise: old cache stores lists, new stores {name: [svcs]}
        def _norm(d):
            if isinstance(d, list): return {k: [] for k in d}
            if isinstance(d, dict): return d
            return {}
        rdbms_dict  = _norm(dbs.get("rdbms", {}))
        cache_dict  = _norm(dbs.get("cache", {}))
        nosql_dict  = _norm(dbs.get("nosql", {}))
        broker_dict = _norm(dbs.get("broker", {}))

        # Fallback legacy
        if not rdbms_dict and "postgres" in context.architecture: rdbms_dict = {"PostgreSQL": []}
        if not cache_dict  and "redis"    in context.architecture: cache_dict  = {"Redis": []}

        # Service numbering map {svc -> "#N"}
        svc_index = {svc: f"#{i+1}" for i, svc in enumerate(context.microservice_dirs)}

        # Global port chain across all services in order
        all_ports = []
        for svc in context.microservice_dirs:
            for p in context.microservice_details.get(svc, {}).get("ports", []):
                if p not in all_ports:
                    all_ports.append(p)

        def _db_tag(svcs: list) -> str:
            if not svcs: return ""
            parts = [f"{svc_index.get(s, s)} {s}" for s in svcs]
            return f"  ← {', '.join(parts)}"

        W = 64
        print("\n" + "=" * W)
        print("  📋  CODE ANALYSIS SUMMARY")
        print("=" * W)
        print(f"  📁  Project       : {context.project_name}")
        print(f"  🏛️   Architecture  : {'Microservices' if not is_mono else 'Monolith'}")
        print(f"  🐳  Dockerfiles   : {num_dockerfiles} file(s) will be generated")
        if all_ports:
            chain = "  →  ".join(f":{p}" for p in all_ports)
            print(f"  🔌  Port chain    : {chain}")
        print()

        # ── Per-service section ─────────────────────────────────────
        if not is_mono and context.microservice_dirs:
            print("  ── MICROSERVICES " + "─" * (W - 18))
            for idx, svc in enumerate(context.microservice_dirs, start=1):
                detail     = context.microservice_details.get(svc, {})
                lang       = detail.get("language", "Node.js")
                frameworks = detail.get("frameworks", [])
                version    = detail.get("node_version", "?")
                base_img   = detail.get("base_image", "node:20-alpine")
                ports      = detail.get("ports", [])
                key_deps   = detail.get("key_deps", [])
                role       = detail.get("role", "Microservice")
                svc_dbs    = detail.get("databases", [])

                fw_str     = f" · {', '.join(frameworks)}" if frameworks else ""
                port_chain = "  →  ".join([f":{p}" for p in ports]) if ports else "auto"

                print(f"  #{idx}  {svc}/  —  {role}")
                print(f"       Language    : {lang}{fw_str}")
                print(f"       Runtime     : {lang} {version}")
                print(f"       Base image  : {base_img}")
                print(f"       Port chain  : {port_chain}")
                if key_deps:
                    print(f"       Key deps    : {', '.join(key_deps)}")
                if svc_dbs:
                    print(f"       Uses DBs    : {', '.join(svc_dbs)}")
                print()

        # ── Databases section ───────────────────────────────────────
        has_db = rdbms_dict or cache_dict or nosql_dict or broker_dict
        if has_db:
            print("  ── DATABASES " + "─" * (W - 14))
            for db_name, svcs in rdbms_dict.items():
                print(f"  🗄️   RDBMS   {db_name:<22}{_db_tag(svcs)}")
            for db_name, svcs in cache_dict.items():
                print(f"  ⚡  Cache   {db_name:<22}{_db_tag(svcs)}")
            for db_name, svcs in nosql_dict.items():
                print(f"  🍃  NoSQL   {db_name:<22}{_db_tag(svcs)}")
            for db_name, svcs in broker_dict.items():
                print(f"  📨  Broker  {db_name:<22}{_db_tag(svcs)}")
            print()

        if context.env_vars:
            print("  ── CONFIGURATION " + "─" * (W - 18))
            shown = context.env_vars[:7]
            print(f"  🔐  Env vars      : {', '.join(shown)}{' ...' if len(context.env_vars) > 7 else ''}")
            print()

        print("=" * W + "\n")


        # 3. Execute Stages based on Plan

        # --- STAGE: Scan & Observability (NEW) ---
        # self._execute_stage("Scan & Observability", "scan", project_path, context, plan)


        # --- STAGE: Docker ---
        self._execute_stage("Dockerfile", "dockerfile", project_path, context, plan)

        # --- STAGE: Docker Compose ---
        self._execute_stage("Docker Compose", "docker_compose", project_path, context, plan)
        
        # --- STAGE: K8s ---
        # Only if applicable (e.g. not serverless, though we assume K8s for now)
        self._execute_stage("Kubernetes Manifests", "kubernetes", project_path, context, plan)
        
        # --- STAGE: CI Pipeline ---
        self._execute_stage("CI Pipeline", "cicd", project_path, context, plan)

        print("\n🎉 Pipeline Execution Completed Successfully!")
        import os
        for f in [".devops_context.json", ".devops_memory.json"]:
            fpath = os.path.join(project_path, f)
            if os.path.exists(fpath):
                try: os.remove(fpath)
                except Exception: pass
        import sys
        sys.exit(0)

        
    def _execute_stage(self, display_name: str, stage_key: str, project_path: str, context: ProjectContext, plan: ArchitecturePlan):
        print(f"\n--- Stage: {display_name} ---")
        
        # 1. Load Prompts
        # We need to select the right prompt based on the plan.
        # For simplicity, we stick to 'writer_a_generalist' for now, 
        # or switch to 'writer_b_security' if observability is strict.
        prompt_name = "writer_b_security" if plan.observability_level == "strict" else "writer_a_generalist"
        # Fallback for CI/CD which might only have one
        if stage_key == "cicd": prompt_name = "github_actions_unified"
        if stage_key == "scan": prompt_name = "scan_config"
        
        # Directory names might differ slightly from stage keys
        prompt_dir = stage_key
        if stage_key == "docker_compose": 
            prompt_dir = "compose"
            prompt_name = "writer"  # There's no writer_a_generalist for compose
            
        try:
            template = load_prompt(prompt_dir, prompt_name)
        except Exception:
            # Fallback logic if specific prompt missing
            template = load_prompt(stage_key, "writer_a_generalist")
            if stage_key == "scan": template = load_prompt("security", "scan_config")
            if stage_key == "docker_compose": template = load_prompt("compose", "writer")
            
        # Optional User Input for K8s & Dockerfile
        custom_instructions = ""
        if stage_key == "kubernetes" or stage_key == "dockerfile":
            if stage_key == "kubernetes":
                template += "\n\nCRITICAL: Output EACH Kubernetes resource (Deployment, Service, Ingress, Secrets, ConfigMap, Namespace etc.) in its OWN SEPARATE file using the FILENAME format: \nFILENAME: k8s/filename.yaml\n```yaml\n<content>\n```"
                print("\n" + "="*50)
                print("☸️   KUBERNETES MANIFEST CUSTOMIZATION")
                print("="*50)
            if stage_key == "dockerfile" and len(context.microservice_dirs) > 0:
                dirs = ", ".join(context.microservice_dirs)
                template += f"\n\nCRITICAL: Automatically output EACH Dockerfile in its respective directory using the FILENAME format (e.g., frontend/Dockerfile, backend/Dockerfile). These are the required directories to cover: {dirs}\nFILENAME: <dir>/Dockerfile\n```dockerfile\n<content>\n```"
            else:
                user_input = input(f"Would you like to provide custom instructions for {display_name}? [y/N]: ").strip().lower()
                if user_input in ['y', 'yes']:
                    print("Options for Custom Instructions:")
                    print("  1. Type instructions directly")
                    print("  2. Provide a path to a file with instructions")
                    choice = input("Choice (1/2): ").strip()
                    if choice == '1':
                        custom_instructions = input("Enter instructions: ").strip()
                    elif choice == '2':
                        filepath = input("Enter file path: ").strip()
                        try:
                            from src.tools.file_ops import read_file
                            custom_instructions = read_file(filepath)
                        except Exception as e:
                            print(f"Failed to read file: {e}")
                    
                    if custom_instructions:
                        template += f"\n\nUSER CUSTOM INSTRUCTIONS (MUST FOLLOW):\n{custom_instructions}"
            
        # 2. Generate Drafts (Parallel)
        prompt_context = {
            "context": context.raw_context_summary,  # Or structured data? format() needs string usually, or we pass dict unpacking
            "plan_summary": str(plan) # Pass plan details to the prompt!
        }
        # Add specific fields
        prompt_context.update(context.model_dump())
        
        candidates = []
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(g.generate, template, prompt_context) for g in self.generators]
            for f in concurrent.futures.as_completed(futures):
                try:
                    candidates.append(f.result())
                except Exception as e:
                    logger.error(f"Generator failed: {e}")

        # 3. Score & Select
        # We need to simulate scoring. Real scoring needs static analysis (hadolint, kubeconform).
        # For this prototype, we will simplistic random/heuristic scoring 
        # OR we just implement basic length/keyword checks in 'Scorecard' if possible.
        # WE haven't implemented REAL scoring in scorecard.py yet, it just takes the spec's self-reported score.
        # So we must "grade" them here or assume the Generator does it? Generator doesn't know.
        # Let's add a "Grader" step? 
        # For now, we will assign mock scores to test the flow.
        for c in candidates:
            content = c.file_content.lower()
            # --- Security heuristics (0-100) ---
            sec = 60  # base
            if "user " in content and ("adduser" in content or "useradd" in content or "nonroot" in content):
                sec += 15  # non-root user present
            if ":latest" not in content:
                sec += 10  # no latest tags
            if "no-cache" in content or "--no-cache-dir" in content or "rm -rf /var/lib" in content:
                sec += 10  # cache cleaned in layer
            if "copy .env" not in content and "env password" not in content:
                sec += 5   # no secrets in image
            c.security_score = min(100, sec)

            # --- Best-practice heuristics (0-100) ---
            bp = 60  # base
            if "as builder" in content:
                bp += 15  # multi-stage build
            if "workdir" in content:
                bp += 10  # WORKDIR used
            if 'cmd ["' in content or "cmd ['":
                bp += 10  # exec form CMD
            if "label org.opencontainers" in content or "label maintainer" in content:
                bp += 5   # OCI labels
            c.best_practice_score = min(100, bp)

        # Model agreement score: ratio of generators that returned useful content
        useful = sum(1 for c in candidates if len(c.file_content.strip()) > 100)
        model_agreement = useful / max(len(candidates), 1)

        if not candidates:
            print("❌ All generators failed.")
            return

        best_spec, best_score = self.evaluator.evaluate_candidates(candidates)
        print(f"🏆 Selected Draft from {best_spec.model_name} (Score: {best_score:.1f})")
        
        # 4. Repair Loop
        # Validator? We need specific validators for each stage.
        # For now, pass.
        final_content = best_spec.file_content
        
        # 5. Confidence & Decision
        confidence_val = compute_confidence(best_spec, repair_attempts=0, model_agreement_score=model_agreement)
        decision = decide_action(confidence_val)
        
        print(f"🤖 Confidence: {confidence_val:.1f}% -> Action: {decision.action.upper()}")
        print(f"   Reason: {decision.reason}")
        
        # 6. User Gate (if required)
        if decision.requires_human_gate:
            print("\n" + "="*50)
            print("📝  GENERATED DRAFTS PREVIEW")
            print("="*50)
            for idx, c in enumerate(candidates):
                print(f"\n--- Draft {idx+1} ({c.model_name}) ---")
                print(c.file_content)
            print("\n" + "="*50)
            print("🏆  FINAL SELECTED DRAFT")
            print("="*50)
            print(final_content)
            print("="*50 + "\n")
            
            user_input = input(f"Proceed with {display_name}? [y/n/edit]: ").lower()
            if user_input != 'y':
                print("Skipping write.")
                return
        
        # 7. Write Output
        # Determine filename based on stage
        filename = "Dockerfile"
        if stage_key == "dockerfile" or stage_key == "kubernetes":
            self._handle_multifile_output(final_content, project_path)
            return
        if stage_key == "docker_compose": filename = "docker-compose.yml"
        if stage_key == "cicd": filename = ".github/workflows/main.yml"
        if stage_key == "scan": 
            # Scan stage writes multiple files in executor/generator. 
            # We might need to skip this single write_file or handle it.
            # But wait, orchestrator calls write_file at the end.
            # The Generator returns 'InfraSpec'. file_content is the content.
            # For scan, file_content is likely multi-file block.
            # We should let the executor handle it, OR simple-parse it here.
            # Let's assume we skip single-file write for 'scan' and handle multi-file.
            self._handle_multifile_output(final_content, project_path)
            return
        
        write_file(f"{project_path}/{filename}", final_content)
        print(f"✅ Precomputed {filename}")
        
        # 8. Save to Memory
        self.memory.store_decision(
            stage=stage_key,
            content=final_content,
            reason=decision.reason,
            decision="APPROVED"
        )

    def _handle_multifile_output(self, content: str, project_path: str):
        """Helper to parse FILENAME: blocks and write them."""
        import re
        import os
        
        pattern = r"FILENAME: (.*?)\n```(?:\w+)?\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            print("📦 Writing Multiple Config Files:")
            for rel_path, file_content in matches:
                rel_path = rel_path.strip()
                full_path = os.path.join(project_path, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                write_file(full_path, file_content.strip())
                print(f"  - Created {rel_path}")
        else:
            print("⚠️ No referenced files found in content. Dumping raw to 'scan_configs.md'")
            write_file(os.path.join(project_path, "scan_configs.md"), content)


