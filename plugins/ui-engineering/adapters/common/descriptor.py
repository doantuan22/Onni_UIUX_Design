"""Adapter metadata loader and validator."""
from __future__ import annotations

import json
from pathlib import Path


def load_and_validate(adapter_dir: Path, schema_dir: Path) -> dict:
    """Load adapter.json and validate against adapter.schema.json.
    
    Args:
        adapter_dir: Directory containing adapter.json
        schema_dir: Directory containing adapter.schema.json (usually plugins/ui-engineering/schemas)
        
    Returns:
        The validated metadata dict.
        
    Raises:
        RuntimeError: If validation fails or files are missing.
    """
    adapter_file = adapter_dir / "adapter.json"
    if not adapter_file.is_file():
        raise RuntimeError(f"Adapter metadata not found: {adapter_file}")
        
    schema_file = schema_dir / "adapter.schema.json"
    if not schema_file.is_file():
        raise RuntimeError(f"Adapter schema not found: {schema_file}")

    try:
        data = json.loads(adapter_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Cannot parse adapter.json: {exc}")

    try:
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Cannot parse adapter.schema.json: {exc}")

    # Use packaging artifact to validate schema
    # We find packaging directory relative to schema_dir (which is plugins/ui-engineering/schemas)
    packaging_dir = schema_dir.parent / "packaging"
    
    import sys
    if str(packaging_dir) not in sys.path:
        sys.path.insert(0, str(packaging_dir))
        
    import artifact
    
    problems = artifact.validate_schema(data, schema)
    if problems:
        raise RuntimeError(f"adapter.json schema errors: {'; '.join(problems)}")
        
    return data
