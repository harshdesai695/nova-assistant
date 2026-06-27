import math
import re
from typing import Dict, Iterable, List, Optional, Tuple


class LocalIntentRouter:
    """Lightweight TF-IDF style intent router without external dependencies."""

    def __init__(self, threshold: float = 0.30):
        self.threshold = threshold
        self.skill_keywords: Dict[str, List[str]] = {
            "get_weather": ["weather", "forecast", "temperature", "rain", "humidity", "climate"],
            "control_brightness": ["brightness", "screen", "dim", "bright", "light"],
            "start_countdown_timer": ["timer", "countdown", "alarm", "remind", "minutes", "seconds"],
            "countdown_timer": ["timer", "countdown", "alarm", "remind", "minutes", "seconds"],
            "capture_screenshot": ["screenshot", "capture", "screen", "snapshot"],
            "enable_visual_system": ["camera", "webcam", "visual", "video"],
            "manage_tasks": ["task", "todo", "list", "reminder", "complete"],
            "get_system_info": ["system", "cpu", "memory", "disk", "uptime", "network"],
            "open_website": ["website", "open", "browser", "url", "web"],
            "launch_application": ["launch", "open app", "application", "start"],
        }
        self._idf = self._build_idf(self.skill_keywords.values())

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[a-z0-9_]+", text.lower())

    def _build_idf(self, docs: Iterable[Iterable[str]]) -> Dict[str, float]:
        doc_list = [set(d) for d in docs]
        n_docs = max(len(doc_list), 1)
        df: Dict[str, int] = {}
        for d in doc_list:
            for term in d:
                df[term] = df.get(term, 0) + 1
        return {t: math.log((1 + n_docs) / (1 + c)) + 1.0 for t, c in df.items()}

    def _vectorize(self, terms: List[str]) -> Dict[str, float]:
        tf: Dict[str, float] = {}
        for t in terms:
            tf[t] = tf.get(t, 0.0) + 1.0
        total = float(len(terms)) or 1.0
        return {t: (c / total) * self._idf.get(t, 1.0) for t, c in tf.items()}

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(v * b.get(k, 0.0) for k, v in a.items())
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)

    def route(self, user_text: str, available_tools: Optional[Iterable[str]] = None) -> Tuple[Optional[str], float]:
        tokens = self._tokenize(user_text)
        if not tokens:
            return None, 0.0

        qv = self._vectorize(tokens)
        allowed = set(available_tools) if available_tools else None

        best_skill = None
        best_score = 0.0
        for skill, kws in self.skill_keywords.items():
            if allowed is not None and skill not in allowed:
                continue
            sv = self._vectorize(kws)
            score = self._cosine(qv, sv)
            if score > best_score:
                best_skill = skill
                best_score = score

        if best_score < self.threshold:
            return None, best_score
        return best_skill, best_score
