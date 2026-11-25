from __future__ import annotations

import functools
import threading
import time
from typing import Any, Callable, Dict

import torch


class SingletonMeta(type):
    _instances: Dict[type, Any] = {}
    _lock = threading.Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class TorchInferenceContext:
    def __init__(self, device: str = "cuda") -> None:
        self.device = device
        self._ctx = torch.inference_mode()

    def __enter__(self) -> "TorchInferenceContext":
        self._ctx.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._ctx.__exit__(exc_type, exc_val, exc_tb)


def execution_timer(attach_result_key: str | None = None) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            t0 = time.perf_counter()
            res = fn(*args, **kwargs)
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            if attach_result_key and isinstance(res, dict):
                res[attach_result_key] = elapsed_ms
            return res

        return wrapper

    return decorator
