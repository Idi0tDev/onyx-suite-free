"""Verify Onyx Reviewer contains an exact generated Core runtime."""

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORE_ROOT = PROJECT_ROOT / "onyx_core"
REVIEWER_ROOT = PROJECT_ROOT / "onyx_reviewer"
RUNTIME_FILES = (
    "api.py",
    "assets.py",
    "embedded.py",
    "errors.py",
    "integration.py",
    "lifecycle.py",
    "readiness.py",
    "registry.py",
)


def main():
    runtime = REVIEWER_ROOT / "_onyx_core"
    assert runtime.is_dir(), "Run tools/sync_embedded_core.ps1"
    assert (runtime / "__init__.py").read_bytes() == (CORE_ROOT / "embedded_init.py").read_bytes()
    for filename in RUNTIME_FILES:
        assert (runtime / filename).read_bytes() == (CORE_ROOT / filename).read_bytes(), (
            f"Stale embedded Core file: {filename}"
        )

    tree = ast.parse((REVIEWER_ROOT / "__init__.py").read_text(encoding="utf-8"))
    core_imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module == "_onyx_core"
        for alias in node.names
    }
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert {"EmbeddedCore", "Lifecycle"} <= core_imports
    assert {"EmbeddedCore", "Lifecycle"} <= calls
    assert "includes the free Onyx Core runtime" in (REVIEWER_ROOT / "README.md").read_text(encoding="utf-8")
    print("ONYX_CORE_REVIEWER_EMBEDDING_OK")


if __name__ == "__main__":
    main()
