import os
import json
from typing import Any
from src.tools.file_ops import scan_directory, read_file, write_file
from src.tools.context_gatherer import ContextGatherer
from src.schemas import ProjectContext

class CodeAnalysisAgent:
    """
    Stage 1 Agent: Deeply analyzes the codebase and caches the results
    to .devops_context.json for all subsequent agents to use.
    """
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.cache_file = os.path.join(project_path, ".devops_context.json")
    
    def analyze(self) -> ProjectContext:
        print(f"🕵️  Code Analysis Agent: Scanning {self.project_path}...")
        
        # 1. Gather raw context using our existing tool
        gatherer = ContextGatherer(self.project_path)
        raw_context = gatherer.get_context()
        
        # 2. Extract structured data
        analysis = {
            "project_name": os.path.basename(os.path.abspath(self.project_path)),
            "language": "unknown",
            "frameworks": [],
            "dependencies": [],
            "ports": [],
            "env_vars": [],
            "file_structure": scan_directory(self.project_path),
            "raw_context_summary": raw_context
        }
        
        # 3. specific heuristics
        self._detect_node(analysis)
        self._detect_python(analysis)
        self._detect_ports(analysis)
        self._detect_env_vars(analysis)
        
        # 4. Create Pydantic model
        context = ProjectContext(**analysis)
        
        # 5. Save to Cache
        self._save_cache(context)
        print(f"✅ Analysis complete. Cached to {self.cache_file}")
        
        return context

    def _detect_node(self, analysis: dict):
        pkg_path = os.path.join(self.project_path, "package.json")
        if os.path.exists(pkg_path):
            analysis["language"] = "javascript/node"
            try:
                data = json.loads(read_file(pkg_path))
                analysis["dependencies"] = list(data.get("dependencies", {}).keys())
                analysis["scripts"] = data.get("scripts", {})
                if "express" in analysis["dependencies"]:
                    analysis["frameworks"].append("express")
                if "react" in analysis["dependencies"]:
                    analysis["frameworks"].append("react")
            except Exception: pass

    def _detect_python(self, analysis: dict):
        req_path = os.path.join(self.project_path, "requirements.txt")
        if os.path.exists(req_path):
            analysis["language"] = "python"
            content = read_file(req_path)
            analysis["dependencies"] = [line.split('==')[0] for line in content.splitlines() if line]
            if "flask" in content.lower(): analysis["frameworks"].append("flask")
            if "django" in content.lower(): analysis["frameworks"].append("django")
            if "fastapi" in content.lower(): analysis["frameworks"].append("fastapi")

    def _detect_ports(self, analysis: dict):
        # Naive scan for common port patterns
        import re
        full_text = analysis["raw_context_summary"] 
        likely_files = ["server.js", "app.py", "main.py", "index.js", "docker-compose.yml"]
        
        files_to_scan = []
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file in likely_files:
                    files_to_scan.append(os.path.join(root, file))
        
        found_ports = set()
        for fpath in files_to_scan: # Limit scanning
            content = read_file(fpath)
            # Look for 3000, 8000, 8080 or port=XXXX
            matches = re.findall(r'port\s*[:=]\s*(\d{4})', content, re.IGNORECASE)
            found_ports.update(matches)
            matches2 = re.findall(r'\.listen\(\s*(\d{4})', content)
            found_ports.update(matches2)
            
        if found_ports:
            analysis["ports"] = list(found_ports)
        # Default fallback if known framework
        elif "express" in analysis["frameworks"]:
            analysis["ports"].append("3000")
        elif "django" in analysis["frameworks"]:
            analysis["ports"].append("8000")

    def _detect_env_vars(self, analysis: dict):
        import re
        likely_files = ["server.js", "app.py", "main.py", "config.js", "settings.py"]
        files_to_scan = []
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file in likely_files:
                    files_to_scan.append(os.path.join(root, file))
        
        envs = set()
        for fpath in files_to_scan:
            content = read_file(fpath)
            # Node
            matches = re.findall(r'process\.env\.([A-Z_][A-Z0-9_]*)', content)
            envs.update(matches)
            # Python
            matches_py = re.findall(r'os\.environ\.get\([\'"]([A-Z_][A-Z0-9_]*)[\'"]\)', content)
            envs.update(matches_py)
            
        analysis["env_vars"] = list(envs)

    def _save_cache(self, context: ProjectContext):
        write_file(self.cache_file, context.model_dump_json(indent=2))

    def get_cached_analysis(self) -> ProjectContext:
        """Reads from cache if exists, otherwise analyzes"""
        if os.path.exists(self.cache_file):
            print(f"⚡ Loading cached analysis from {self.cache_file}")
            try:
                content = read_file(self.cache_file)
                return ProjectContext.model_validate_json(content)
            except Exception:
                print("⚠️  Cache invalid, re-analyzing...")
                return self.analyze()
        return self.analyze()
