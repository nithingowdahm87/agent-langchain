import os
import json

class ContextGatherer:
    """
    Scans a project directory to gather context about the technology stack.
    Detects languages, frameworks, and dependencies to inform AI generation.
    """
    def __init__(self, path: str):
        self.path = path

    def get_context(self) -> str:
        """Scans for facts to ground the AI."""
        context = []
        
        # 1. Detect Node.js
        package_json_path = os.path.join(self.path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    data = json.load(f)
                    context.append(f"Project Type: Node.js")
                    deps = list(data.get('dependencies', {}).keys())
                    dev_deps = list(data.get('devDependencies', {}).keys())
                    all_deps = deps + dev_deps
                    # Limit to top 20 dependencies to avoid token overflow
                    context.append(f"Dependencies: {', '.join(all_deps[:20])}")
                    if 'scripts' in data:
                        context.append(f"Available Scripts: {', '.join(data['scripts'].keys())}")
            except Exception as e:
                context.append(f"Error reading package.json: {e}")
        
        # 2. Detect Python
        requirements_txt_path = os.path.join(self.path, "requirements.txt")
        if os.path.exists(requirements_txt_path):
            try:
                with open(requirements_txt_path, "r") as f:
                    # Read first 50 lines / 500 chars
                    content = f.read()
                    context.append(f"Project Type: Python")
                    context.append(f"Requirements: {content[:1000]}") # Truncate
            except Exception as e:
                context.append(f"Error reading requirements.txt: {e}")

        # 3. Detect Go
        go_mod_path = os.path.join(self.path, "go.mod")
        if os.path.exists(go_mod_path):
            try:
                with open(go_mod_path, "r") as f:
                    first_line = f.readline().strip()
                    context.append(f"Project Type: Go ({first_line})")
            except Exception as e:
                context.append(f"Error reading go.mod: {e}")

        # 4. Detect Java (Maven/Gradle)
        pom_xml_path = os.path.join(self.path, "pom.xml")
        if os.path.exists(pom_xml_path):
             context.append("Project Type: Java (Maven)")
        
        build_gradle_path = os.path.join(self.path, "build.gradle")
        if os.path.exists(build_gradle_path):
             context.append("Project Type: Java/Kotlin (Gradle)")

        if not context:
            return "No specific project context detected. Treat as generic application."

        return "\n".join(context)
