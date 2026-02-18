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
        
        # 2. Execute Stages based on Plan
        
        # --- STAGE: Scan & Observability (NEW) ---
        self._execute_stage("Scan & Observability", "scan", project_path, context, plan)

        # --- STAGE: Docker ---
        self._execute_stage("Dockerfile", "dockerfile", project_path, context, plan)
        
        # --- STAGE: K8s ---
        # Only if applicable (e.g. not serverless, though we assume K8s for now)
        self._execute_stage("Kubernetes Manifests", "kubernetes", project_path, context, plan)
        
        # --- STAGE: CI/CD ---
        self._execute_stage("CI/CD Pipeline", "cicd", project_path, context, plan)
        
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
            
        try:
            template = load_prompt(stage_key, prompt_name)
        except Exception:
            # Fallback logic if specific prompt missing
            template = load_prompt(stage_key, "writer_a_generalist")
            if stage_key == "scan": template = load_prompt("security", "scan_config")
            
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
            # Mock grading
            c.security_score = 80 + (len(c.file_content) % 20) 
            c.best_practice_score = 85
        
        if not candidates:
            print("❌ All generators failed.")
            return

        best_spec, best_score = self.evaluator.evaluate_candidates(candidates)
        print(f"🏆 Selected Draft from {best_spec.model_name} (Score: {best_score})")
        
        # 4. Repair Loop
        # Validator? We need specific validators for each stage.
        # For now, pass.
        final_content = best_spec.file_content
        
        # 5. Confidence & Decision
        confidence_val = compute_confidence(best_spec, repair_attempts=0)
        decision = decide_action(confidence_val)
        
        print(f"🤖 Confidence: {confidence_val:.1f}% -> Action: {decision.action.upper()}")
        print(f"   Reason: {decision.reason}")
        
        # 6. User Gate (if required)
        if decision.requires_human_gate:
            user_input = input(f"Proceed with {display_name}? [y/n/edit]: ").lower()
            if user_input != 'y':
                print("Skipping write.")
                return
        
        # 7. Write Output
        # Determine filename based on stage
        filename = "Dockerfile"
        if stage_key == "kubernetes": filename = "k8s/manifest.yaml"
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


