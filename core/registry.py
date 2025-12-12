# core/registry.py
import functools
from typing import Callable, Dict, List

SKILL_REGISTRY: Dict[str, Callable] = {}

def skill(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    SKILL_REGISTRY[func.__name__] = func
    return wrapper

def get_all_skills() -> List[Callable]:
    return list(SKILL_REGISTRY.values())