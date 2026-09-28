"""Technology resolver: choose the simplest technology for each selected capability.

Order: installed option -> native preferred -> authorized preferred library -> native alternative -> degrade.
The skill never installs anything; ``allow_new_dependencies`` only records an authorized new dependency.
``allow_motion_library`` (ELEVATE / REIMAGINE work) sanctions exactly one motion library
(``tech.motion`` = motion/framer-motion, or ``tech.gsap``) when no native option is preferred;
it is recorded in ``new_dependencies`` and must be reported to the user.
Rules: skills/frontend-implementation/technology-resolver.md.
"""
from __future__ import annotations

from uiux.core import config
from uiux.core.errors import RegistryError
from uiux.knowledge import catalog as K


def _list(value: object) -> list[str]:
    return K._as_list(value)


def _of_kind(entries: dict[str, dict], kind: str) -> list[dict]:
    return [e for i, e in sorted(entries.items()) if e["kind"] == kind]


MOTION_LIBRARIES = ("tech.motion", "tech.gsap")


def resolve_technology(entries: dict[str, dict], p: dict, capabilities: list[str]) -> dict:
    installed = set(p["existing_dependencies"])
    techs = {t["id"]: t for t in _of_kind(entries, "technology")}
    present = {tid for tid, t in techs.items() if set(_list(t["packages"])) & installed}
    assignments, degraded, new_deps = {}, [], set()
    motion_lib = next((t for t in MOTION_LIBRARIES if t in present), None)
    for cid in capabilities:
        spec = entries[cid].get("technology")
        if not isinstance(spec, dict):
            continue
        preferred, alternatives = _list(spec["preferred"]), _list(spec["alternatives"])
        options = preferred + [t for t in alternatives if t not in preferred]
        # 1 installed option -> 2 native preferred -> 3 authorized preferred library -> 4 native alternative -> 5 degrade
        native = lambda tid: techs[tid]["requires_dependency"] == "false"
        choice, reason = next((t for t in options if t in present), None), "reuses an existing project dependency"
        if not choice:
            choice, reason = next((t for t in preferred if native(t)), None), "native platform capability"
        if not choice and p["allow_new_dependencies"]:
            choice = next((t for t in preferred if not native(t)), None)
            if choice:
                new_deps.add(choice); reason = "new dependency (authorized by profile)"
        if not choice and p.get("allow_motion_library"):
            # One sanctioned motion library per project: reuse the one already chosen or installed
            libs = [t for t in preferred if t in MOTION_LIBRARIES and t in techs]
            if motion_lib and motion_lib in options:
                choice = motion_lib
            elif not motion_lib and libs:
                choice = libs[0]
            if choice:
                motion_lib = choice
                if choice not in present:
                    new_deps.add(choice)
                reason = "sanctioned motion library (ambition ELEVATE/REIMAGINE); report it to the user"
        if not choice:
            choice = next((t for t in alternatives if native(t)), None)
            reason = f"native fallback; preferred {', '.join(preferred)} not installed or authorized"
        if not choice:
            degraded.append({"id": cid, "reason": f"needs {options[0] if options else 'unknown'}; dependency not present or authorized"})
            continue
        assignments[cid] = {"technology": choice, "reason": reason}
    used = sorted({a["technology"] for a in assignments.values()})
    return {"assignments": assignments, "technologies": used, "existing_reused": sorted(present & set(used)),
            "new_dependencies": sorted(new_deps), "degraded": degraded}


def resolve(capabilities: list[str], existing_dependencies: list[str] | tuple[str, ...] = (),
            allow_new_dependencies: bool | None = None, entries: dict[str, dict] | None = None,
            allow_motion_library: bool = False) -> dict:
    """Standalone technology resolution for capability ids (motion, effect or interaction entries)."""
    if entries is None:
        entries, errors = K.load()
        if errors:
            raise RegistryError("knowledge base failed to load: " + "; ".join(errors[:3]))
    unknown = [c for c in capabilities if c not in entries]
    if unknown:
        raise ValueError(f"unknown capability ids: {', '.join(unknown)}")
    if allow_new_dependencies is None:
        allow_new_dependencies = bool(config.get()["dependency_policy"]["allow_new_dependencies"])
    profile = {"existing_dependencies": list(existing_dependencies), "allow_new_dependencies": bool(allow_new_dependencies),
               "allow_motion_library": bool(allow_motion_library)}
    return resolve_technology(entries, profile, list(capabilities))
