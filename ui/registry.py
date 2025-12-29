import pkgutil
import importlib
import inspect
from typing import Dict, Type, Optional
from PyQt6.QtWidgets import QWidget

UI_SKILL_REGISTRY: Dict[str, "UISkillMetadata"] = {}

class UISkillMetadata:
    def __init__(self, cls: Type[QWidget], title: str, icon: str, description: str, trigger_signal: Optional[str] = None):
        self.cls = cls
        self.title = title
        self.icon = icon
        self.description = description
        self.trigger_signal = trigger_signal 

def register_ui_skill(title: str, icon: str, description: str = "", trigger_signal: str = None):
    def decorator(cls):
        UI_SKILL_REGISTRY[cls.__name__] = UISkillMetadata(
            cls=cls,
            title=title,
            icon=icon,
            description=description,
            trigger_signal=trigger_signal
        )
        return cls
    return decorator

def load_ui_skills(package_path="ui.skills"):
    try:
        module = importlib.import_module(package_path)
        path = module.__path__
        for _, name, _ in pkgutil.iter_modules(path, package_path + "."):
            importlib.import_module(name)
    except Exception as e:
        print(f"Error loading UI skills: {e}")

def get_all_ui_skills() -> Dict[str, UISkillMetadata]:
    return UI_SKILL_REGISTRY