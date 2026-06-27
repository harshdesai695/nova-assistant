import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, Iterable


def _allowlist() -> set[str]:
    raw = os.getenv("NOVA_PARALLEL_SAFE_SKILLS", "get_weather,control_brightness,start_countdown_timer,capture_screenshot,manage_tasks")
    return {s.strip() for s in raw.split(",") if s.strip()}


def execute_functions_parallel(function_calls: Dict[str, tuple[Callable, dict]]) -> Dict[str, Any]:
    """Execute function map in parallel where safe; fallback to sequential for the rest."""
    safe = _allowlist()
    timeout = float(os.getenv("NOVA_PARALLEL_TIMEOUT_SECONDS", "8"))

    results: Dict[str, Any] = {}
    parallel_items = {k: v for k, v in function_calls.items() if k in safe}
    sequential_items = {k: v for k, v in function_calls.items() if k not in safe}

    if parallel_items:
        with ThreadPoolExecutor(max_workers=min(4, len(parallel_items))) as pool:
            future_map = {
                pool.submit(fn, **kwargs): name
                for name, (fn, kwargs) in parallel_items.items()
            }
            for fut in as_completed(future_map, timeout=timeout):
                name = future_map[fut]
                try:
                    results[name] = fut.result()
                except Exception as exc:
                    results[name] = f"Error executing {name}: {exc}"

    for name, (fn, kwargs) in sequential_items.items():
        try:
            results[name] = fn(**kwargs)
        except Exception as exc:
            results[name] = f"Error executing {name}: {exc}"

    return results
