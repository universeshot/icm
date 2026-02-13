from __future__ import annotations

import importlib
import importlib.util
import sys
import uuid
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable

from .features import FeatureTechnique


def _is_technique(obj: Any) -> bool:
    return (
        hasattr(obj, "id")
        and hasattr(obj, "namespace")
        and hasattr(obj, "feature_name")
        and callable(getattr(obj, "calculate", None))
    )


def _as_techniques(value: Any) -> list[FeatureTechnique]:
    if isinstance(value, dict):
        items: Iterable[Any] = value.values()
    elif isinstance(value, (list, tuple, set)):
        items = value
    else:
        raise ValueError("Feature plugin payload must be a list/tuple/set or dict of techniques.")

    techniques: list[FeatureTechnique] = []
    for item in items:
        obj = item
        if isinstance(item, type):
            obj = item()
        if not _is_technique(obj):
            raise ValueError(
                "Invalid feature technique object. Expected id/namespace/feature_name/calculate."
            )
        techniques.append(obj)
    return techniques


def import_plugin_module(module_name_or_path: str) -> ModuleType:
    path = Path(module_name_or_path)
    if path.exists() and path.is_file():
        module_name = f"icm_plugin_{path.stem}_{uuid.uuid4().hex}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load plugin module from path: {module_name_or_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(module_name_or_path)


def load_feature_techniques(module_name_or_path: str) -> list[FeatureTechnique]:
    module = import_plugin_module(module_name_or_path)
    if hasattr(module, "register_feature_techniques"):
        payload = module.register_feature_techniques()
        return _as_techniques(payload)
    if hasattr(module, "FEATURE_TECHNIQUES"):
        payload = module.FEATURE_TECHNIQUES
        return _as_techniques(payload)
    raise ValueError(
        f"Plugin '{module_name_or_path}' must expose register_feature_techniques() or FEATURE_TECHNIQUES."
    )
