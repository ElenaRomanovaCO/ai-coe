#!/usr/bin/env python3
"""Validate every markdown file in the vault against its per-type frontmatter schema.

Walks ``vault/``, maps each ``.md`` file to a content type by its top-level folder,
parses the YAML frontmatter, and validates it against the matching Pydantic schema
(see ``agents/lib/schemas``). Also validates ``vault/modules.json`` against the
module registry. Exits non-zero on the first batch of failures so it can serve as a
pre-commit hook.

    uv run python scripts/validate_vault.py [--vault PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the repo root importable when run directly (scripts/ is not a package).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.lib.registry import load_registry  # noqa: E402
from agents.lib.schemas import (  # noqa: E402
    FrontmatterError,
    content_type_for_path,
    parse_frontmatter,
    validate_frontmatter,
)

# Files under vault/ that carry no frontmatter and are validated elsewhere.
_SKIP_NAMES = {"agents.md"}
_SKIP_DIRS = {"_schema"}


def validate_vault(vault: Path) -> list[str]:
    """Return a list of human-readable error strings (empty == all valid)."""
    errors: list[str] = []

    # 1. modules.json against the registry schema.
    modules_json = vault / "modules.json"
    if not modules_json.exists():
        errors.append("modules.json: missing")
    else:
        try:
            reg = load_registry(modules_json)
            ids = [m.id for m in reg.modules]
            if len(ids) != len(set(ids)):
                errors.append("modules.json: duplicate module ids")
        except Exception as exc:  # noqa: BLE001 — surface any validation error
            errors.append(f"modules.json: {exc}")

    # 2. Every markdown file against its folder's schema.
    for md in sorted(vault.rglob("*.md")):
        rel = md.relative_to(vault).as_posix()
        if md.name in _SKIP_NAMES or set(md.relative_to(vault).parts) & _SKIP_DIRS:
            continue
        mapping = content_type_for_path(rel)
        if mapping is None:
            errors.append(f"{rel}: not under a known content-type folder")
            continue
        _label, schema = mapping
        try:
            data = parse_frontmatter(md.read_text(encoding="utf-8"))
            validate_frontmatter(schema, data)
        except FrontmatterError as exc:
            errors.append(f"{rel}: {exc}")
        except Exception as exc:  # noqa: BLE001 — pydantic ValidationError et al.
            errors.append(f"{rel}: {exc}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_vault = Path(__file__).resolve().parents[1] / "vault"
    parser.add_argument("--vault", type=Path, default=default_vault)
    args = parser.parse_args()

    errors = validate_vault(args.vault)
    md_count = len(list(args.vault.rglob("*.md")))
    if errors:
        print(f"FAIL: vault validation failed ({len(errors)} issue(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"OK: vault valid: {md_count} markdown files + modules.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
