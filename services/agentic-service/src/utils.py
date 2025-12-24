from langgraph.graph import StateGraph
import yaml
from pathlib import Path
from typing import Any, Dict

def save_architecture(app: StateGraph, filename: str = "architecture.png"):
    """Safely persist a mermaid PNG of the graph.

    Writes to the repo-level assets directory. If that directory doesn't exist
    (e.g., in a constrained Lambda package), the function degrades gracefully
    by printing a warning instead of raising.
    """
    try:
        png_bytes = app.get_graph().draw_mermaid_png()
    except Exception:  # pragma: no cover - defensive
        # Skip silently in Lambda environment
        return

    # Repo root is 3 levels up from this file: src/utils.py -> src -> service root -> monorepo root
    repo_root = Path(__file__).resolve().parents[3]
    assets_dir = repo_root / "assets"
    try:
        assets_dir.mkdir(parents=True, exist_ok=True)
        out_path = assets_dir / filename
        with open(out_path, "wb") as f:
            f.write(png_bytes)
    except Exception:  # pragma: no cover - best-effort only
        # Skip silently in Lambda (read-only filesystem)
        pass

def read_yaml_file(file_path: str) -> Dict[str, Any]:
    """Read a YAML file and return its contents as a dict.

    Resolution rules for relative paths:
      1. Interpret relative to this utils.py file's directory (the service src root).
      2. If not found, fall back to current working directory.

    Raises:
        FileNotFoundError: If the file can't be located.
        ValueError: If the YAML content is invalid.
    """
    original_input = file_path
    path_obj = Path(file_path)

    search_paths = []
    if not path_obj.is_absolute():
        base_dir = Path(__file__).resolve().parent  # .../services/agentic-service/src
        # First try relative to src directory
        candidate = base_dir / path_obj
        search_paths.append(candidate)
        # Then try relative to current working directory (pytest / lambda)
        search_paths.append(Path.cwd() / path_obj)
    else:
        search_paths.append(path_obj)

    target_path = None
    for p in search_paths:
        if p.exists():
            target_path = p
            break

    if target_path is None:
        search_str = " | ".join(str(p) for p in search_paths)
        raise FileNotFoundError(
            f"YAML file '{original_input}' not found. Tried: {search_str}"
        )

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                # Allow lists, but wrap them for consistent return type if needed
                if isinstance(data, list):
                    return {"_list": data}
                raise ValueError(f"Unexpected YAML root type: {type(data)} in {target_path}")
            return data
    except yaml.YAMLError as e:
        raise ValueError(f"Failed parsing YAML file {target_path}: {e}") from e