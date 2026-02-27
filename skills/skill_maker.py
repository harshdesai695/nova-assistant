import os
import json
import subprocess
import core.llm
from core.registry import skill, get_all_skills
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.exceptions import HttpResponseError

@skill
def create_new_skill(skill_description: str) -> str:
    if not core.llm.NOVA_CLIENT or not core.llm.NOVA_MODEL:
        return "AI Client not initialized."
        
    rules_path = "core\skill_creation_rules.txt"
    rules_text = ""
    if os.path.exists(rules_path):
        with open(rules_path, "r", encoding="utf-8") as f:
            rules_text = f.read()
            
    existing_skills = [f.__name__ for f in get_all_skills()]
    
    sys_prompt = f"""
You are an expert Python developer for the N.O.V.A assistant.
Generate a new skill based on the user's description.
You must format your entire response as a raw JSON object with this exact structure:
{{
    "backend_filename": "name_ops.py",
    "backend_code": "code string or null",
    "ui_filename": "name_ui.py",
    "ui_code": "code string or null",
    "dependencies": ["lib1", "lib2"]
}}
Existing skills available: {existing_skills}
Rules:
{rules_text}
"""
    
    try:
        response = core.llm.NOVA_CLIENT.complete(
            messages=[
                SystemMessage(content=sys_prompt),
                UserMessage(content=skill_description)
            ],
            model=core.llm.NOVA_MODEL
        )
        content = response.choices[0].message.content
        
        content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        deps = data.get("dependencies", [])
        if deps:
            for dep in deps:
                subprocess.run(["pip", "install", dep], check=False)
            with open("requirements.txt", "a", encoding="utf-8") as req_file:
                for dep in deps:
                    req_file.write(f"\n{dep}")
                    
        backend_file = data.get("backend_filename")
        backend_code = data.get("backend_code")
        if backend_file and backend_code:
            os.makedirs("skills", exist_ok=True)
            with open(f"skills/{backend_file}", "w", encoding="utf-8") as f:
                f.write(backend_code)
                
        ui_file = data.get("ui_filename")
        ui_code = data.get("ui_code")
        if ui_file and ui_code:
            os.makedirs("ui/skills", exist_ok=True)
            with open(f"ui/skills/{ui_file}", "w", encoding="utf-8") as f:
                f.write(ui_code)
                
        return f"Successfully created skill. Files: {backend_file}, {ui_file}. Dependencies: {deps}"

    except HttpResponseError as e:
        return f"Azure API Error: {e.message}"
    except Exception as e:
        return f"Failed to parse or create skill: {str(e)}"