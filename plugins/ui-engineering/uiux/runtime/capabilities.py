"""Read-only capability detector for browser execution contracts; standard library only.

Public entry: ``detect(project, url=None)`` (also exposed as ``uiux.api.detect_runtime``). Playwright readiness is
classified without importing or installing anything:

    NOT_DECLARED                       no Playwright package declared by the project
    DECLARED_NOT_INSTALLED             declared in package.json but not resolvable in node_modules
    PACKAGE_AVAILABLE_BROWSER_MISSING  package resolvable, no browser build in the Playwright browser cache
    READY                              package resolvable and a browser build is present
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import urllib.request
from pathlib import Path

PLAYWRIGHT_PACKAGES = ("playwright", "@playwright/test", "playwright-core")
NOT_DECLARED = "NOT_DECLARED"
DECLARED_NOT_INSTALLED = "DECLARED_NOT_INSTALLED"
PACKAGE_AVAILABLE_BROWSER_MISSING = "PACKAGE_AVAILABLE_BROWSER_MISSING"
READY = "READY"
RUNTIME_STATES = (NOT_DECLARED, DECLARED_NOT_INSTALLED, PACKAGE_AVAILABLE_BROWSER_MISSING, READY)


def command_version(command: str) -> dict[str, object]:
    location = shutil.which(command)
    if not location:
        return {"status": "NOT_AVAILABLE", "version": None, "confidence": "confirmed"}
    try:
        output = subprocess.run([command, "--version"], capture_output=True, text=True, timeout=3, check=False)
        version = (output.stdout or output.stderr).strip().splitlines()[0] if output.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        version = None
    return {"status": "AVAILABLE" if version else "AVAILABLE_WITH_LIMITATIONS", "version": version, "confidence": "confirmed"}


def package_data(root: Path) -> dict[str, object]:
    path = root / "package.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def has_dependency(data: dict[str, object], names: set[str]) -> bool:
    for field in ("dependencies", "devDependencies", "peerDependencies"):
        values = data.get(field, {})
        if isinstance(values, dict) and names.intersection(values):
            return True
    return False


def installed_package_dir(project: Path, names: tuple[str, ...] = PLAYWRIGHT_PACKAGES) -> Path | None:
    """Resolve a package the way Node does for the project: node_modules in the project or any ancestor."""
    for directory in (project, *project.parents):
        for name in names:
            candidate = directory / "node_modules" / name / "package.json"
            if candidate.is_file():
                return candidate.parent
    return None


def browser_cache_dirs(project: Path) -> list[Path]:
    """Default Playwright browser cache locations (read-only; honours PLAYWRIGHT_BROWSERS_PATH)."""
    env = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if env == "0":
        core = installed_package_dir(project, ("playwright-core",))
        return [core / ".local-browsers"] if core else []
    if env:
        return [Path(env)]
    home = Path.home()
    system = platform.system()
    if system == "Windows":
        return [Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local")) / "ms-playwright"]
    if system == "Darwin":
        return [home / "Library" / "Caches" / "ms-playwright"]
    return [Path(os.environ.get("XDG_CACHE_HOME", home / ".cache")) / "ms-playwright"]


def playwright_state(project: Path, data: dict[str, object] | None = None, browser: str = "chromium") -> dict[str, object]:
    """Classify Playwright readiness for ``project`` without importing, launching or installing anything."""
    data = package_data(project) if data is None else data
    declared = has_dependency(data, set(PLAYWRIGHT_PACKAGES))
    package_dir = installed_package_dir(project)
    caches = browser_cache_dirs(project)
    builds = sorted(p.name for c in caches if c.is_dir() for p in c.iterdir() if p.is_dir() and p.name.startswith(browser))
    if package_dir is None:
        state = DECLARED_NOT_INSTALLED if declared else NOT_DECLARED
    else:
        state = READY if builds else PACKAGE_AVAILABLE_BROWSER_MISSING
    return {"state": state, "declared": declared, "package_dir": str(package_dir) if package_dir else None,
            "browser": browser, "browser_builds": builds, "browser_cache": [str(c) for c in caches],
            "confidence": "confirmed" if state in (NOT_DECLARED, DECLARED_NOT_INSTALLED) else "inferred"}


def design_runtime(data: dict[str, object]) -> dict[str, object]:
    """Animation/graphics dependencies already present, mapped to technology-resolver ids (read-only)."""
    installed: set[str] = set()
    for field in ("dependencies", "devDependencies", "peerDependencies"):
        values = data.get(field, {})
        if isinstance(values, dict):
            installed.update(values)
    try:
        from uiux.knowledge import registry  # catalogs are the single source of package names
        catalog = {row["id"]: _packages(registry.get(row["id"])) for row in registry.query(collection="technologies")}
    except Exception:  # detector must never fail because of the knowledge base
        return {"packages": [], "technologies": [], "confidence": "unknown"}
    found = {tid: sorted(set(pkgs) & installed) for tid, pkgs in catalog.items() if set(pkgs) & installed}
    return {"packages": sorted({p for pkgs in found.values() for p in pkgs}), "technologies": sorted(found),
            "confidence": "confirmed"}


def framework(data: dict[str, object], root: Path) -> dict[str, str]:
    dependencies = set()
    for field in ("dependencies", "devDependencies"):
        values = data.get(field, {})
        if isinstance(values, dict):
            dependencies.update(values)
    signals = [
        ("Next.js", "next" in dependencies or (root / "next.config.js").exists() or (root / "next.config.mjs").exists()),
        ("Vite", "vite" in dependencies or (root / "vite.config.ts").exists() or (root / "vite.config.js").exists()),
        ("Angular", "@angular/core" in dependencies or (root / "angular.json").exists()),
        ("Vue", "vue" in dependencies),
        ("React", "react" in dependencies),
        ("Spring Boot", (root / "pom.xml").exists() or (root / "build.gradle").exists()),
        ("plain HTML", any(root.glob("*.html"))),
    ]
    for name, present in signals:
        if present:
            return {"value": name, "confidence": "confirmed"}
    return {"value": None, "confidence": "unknown"}


def running_url(url: str | None) -> dict[str, object]:
    if not url:
        return {"status": "UNKNOWN", "url": None, "confidence": "unknown"}
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return {"status": "AVAILABLE", "url": url, "http_status": response.status, "confidence": "confirmed"}
    except Exception as exc:  # Network shape is platform-dependent; report, never mutate.
        return {"status": "NOT_AVAILABLE", "url": url, "reason": type(exc).__name__, "confidence": "confirmed"}


def _packages(entry: dict) -> list[str]:
    value = entry.get("packages")
    return value if isinstance(value, list) else []


def detect(project: Path | str = ".", url: str | None = None, browser: str = "chromium") -> dict[str, object]:
    """Read-only capability report for ``project`` (the structure consumed by the runtime runner)."""
    root = Path(project).resolve()
    package = package_data(root)
    scripts = package.get("scripts", {}) if isinstance(package.get("scripts", {}), dict) else {}
    locks = [("pnpm", "pnpm-lock.yaml"), ("yarn", "yarn.lock"), ("npm", "package-lock.json"), ("bun", "bun.lockb")]
    manager = next(((name, filename) for name, filename in locks if (root / filename).exists()), (None, None))
    playwright = has_dependency(package, {"@playwright/test", "playwright", "playwright-core"})
    axe_playwright = has_dependency(package, {"@axe-core/playwright"})
    axe_core = has_dependency(package, {"axe-core"})
    compatible = has_dependency(package, {"puppeteer", "selenium-webdriver", "webdriverio", "cypress"})
    configs = [path.name for path in root.glob("playwright.config.*")]
    browser_commands = [name for name in ("chrome", "google-chrome", "chromium", "chromium-browser", "msedge") if shutil.which(name)]
    report = {
        "detector": {"mode": "read_only", "project": str(root)},
        "runtime": {"node": command_version("node"), "python": command_version("python")},
        "package_manager": {"detected": manager[0], "lockfile": manager[1], "command": manager[0],
                            "confidence": "confirmed" if manager[0] else "unknown"},
        "project": {"package_json": (root / "package.json").is_file(), "framework": framework(package, root),
                    "dev_command": scripts.get("dev") or scripts.get("start"), "build_command": scripts.get("build"),
                    "test_command": scripts.get("test"),
                    "validation_commands": [name for name in ("build", "typecheck", "lint", "test")
                        if manager[0] and isinstance(scripts.get(name), str) and scripts[name].strip()]},
        "playwright": {"package_present": {"status": "AVAILABLE" if playwright else "NOT_AVAILABLE", "confidence": "confirmed"},
                       "config_present": {"status": "AVAILABLE" if configs else "NOT_AVAILABLE", "files": configs, "confidence": "confirmed"},
                       "browser_ready": {"status": "UNKNOWN", "confidence": "unknown"},
                       "runtime_state": playwright_state(root, package, browser)},
        "browser": {"status": "AVAILABLE" if browser_commands else "UNKNOWN", "commands": browser_commands,
                    "headless": {"status": "UNKNOWN", "confidence": "unknown"}, "confidence": "confirmed" if browser_commands else "unknown"},
        "compatible_automation": {"status": "AVAILABLE" if compatible else "NOT_AVAILABLE", "confidence": "confirmed"},
        "accessibility": {"axe_playwright": {"status": "AVAILABLE" if axe_playwright else "NOT_AVAILABLE", "confidence": "confirmed"},
                          "axe_core": {"status": "AVAILABLE" if axe_core else "NOT_AVAILABLE", "confidence": "confirmed"},
                          "strategy": "axe-playwright" if axe_playwright else "axe-core-injection" if axe_core else "manual-fallback"},
        "design_runtime": design_runtime(package),
        "application": {"known_url": url, "already_running": running_url(url)},
        "limitations": ["No packages installed, configuration modified, browser downloaded, or process started."],
    }
    state = report["playwright"]["runtime_state"]["state"]
    if state == READY:
        report["playwright"]["browser_ready"] = {"status": "AVAILABLE", "confidence": "inferred"}
    elif state == PACKAGE_AVAILABLE_BROWSER_MISSING:
        report["playwright"]["browser_ready"] = {"status": "NOT_AVAILABLE", "confidence": "inferred"}
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only execution capability detector")
    parser.add_argument("project", nargs="?", default=".", help="project directory to inspect")
    parser.add_argument("--url", help="optional known application URL to probe read-only")
    args = parser.parse_args()
    print(json.dumps(detect(args.project, args.url), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
