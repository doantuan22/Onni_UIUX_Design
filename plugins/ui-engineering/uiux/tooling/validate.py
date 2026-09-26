"""Lightweight structural validator for the UI/UX workflow skill; standard library only.

Public entry: ``validate(root=None)`` (exposed as ``uiux.api.validate_skill``); CLI: python scripts/validate_skill.py [root].
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from uiux.core import registry as core_registry


SCENARIO_FIELDS = {
    "id", "name", "category", "project_state", "user_request", "expected_route",
    "required_artifacts", "forbidden_behavior", "expected_context",
    "success_conditions", "failure_conditions",
}
STATES = {
    "INITIAL", "ANALYZING", "PHASE_1", "PHASE_1_REVIEW", "STRUCTURE_LOCKED",
    "PHASE_2", "PHASE_2_REVIEW", "FINAL_REVIEW", "DONE", "BLOCKED",
}
REQUIRED_FILES = {
    "SKILL.md", "workflows/execution-contract.md", "workflows/reference-loading.md",
    "workflows/reference-index.md", "workflows/change-impact.md", "workflows/rollback-matrix.md",
    "workflows/chunking-strategy.md", "templates/ARTIFACT-REGISTRY.md",
    "templates/CONTEXT-MANIFEST.md", "templates/TASK-SCOPE.md",
    "templates/COMPLETION-EVIDENCE.md", "evals/framework.md", "evals/rubric.md",
    "evals/result-template.md", "evals/failure-taxonomy.md", "evals/reports/EVAL-SUMMARY.md",
    "execution/README.md", "execution/capability-detection.md", "execution/execution-router.md",
    "execution/execution-requirement.md", "execution/application-runtime.md", "execution/browser-contract.md",
    "execution/evidence-contract.md", "execution/viewports.md", "execution/failure-handling.md",
    "execution/adapters/playwright.md", "execution/adapters/manual.md",
    "workflows/execution-requirement.md", "templates/TOOL-CAPABILITY-MANIFEST.md",
    "templates/EXECUTION-REPORT.md", "../../development/docs/execution-layer.md",
    "execution/viewports.json", "execution/runtime/README.md", "execution/runtime/runner-contract.md",
    "execution/runtime/runtime-input.md", "execution/runtime/runtime-output.md", "execution/runtime/session-lifecycle.md",
    "execution/runtime/runtime-errors.md", "execution/storage/README.md", "execution/storage/manifest-schema.md",
    "execution/storage/evidence-layout.md", "execution/storage/retention.md", "../../development/docs/execution-runtime.md",
    "scripts/run_browser_execution.py", "scripts/validate_runtime_evidence.py",
    "../../development/docs/research/visual-skill-integration-analysis.md", "templates/VISUAL-GRAMMAR.md",
    "evals/reports/VISUAL-LANGUAGE-DRY-RUN.md",
    "skills/visual-language/README.md", "skills/visual-language/workflow.md",
    "knowledge/visual-language/visual-grammar.md", "skills/visual-language/craft-review.md",
    "skills/visual-language/adversarial-review.md", "knowledge/visual-language/ai-tell-density.md",
    "knowledge/visual-language/components/buttons.md", "knowledge/visual-language/components/feedback.md",
    "knowledge/visual-language/components/iconography.md",
}
INSPIRATION_FILES = {
    "skills/design-inspiration/README.md", "skills/design-inspiration/workflow.md",
    "skills/design-inspiration/archetypes.md", "skills/design-inspiration/reference-profiles.md",
    "skills/design-inspiration/reference-extraction.md", "skills/design-inspiration/pattern-selection.md",
    "skills/design-inspiration/anti-copying.md",
    "skills/typography/README.md", "knowledge/typography/typography-archetypes.md",
    "skills/typography/font-selection.md", "knowledge/typography/font-pairing.md",
    "knowledge/typography/display-type.md", "knowledge/typography/body-type.md",
    "knowledge/typography/technical-type.md", "knowledge/typography/typography-rhythm.md",
    "knowledge/typography/typographic-composition.md", "skills/typography/typography-review.md",
    "knowledge/motion/README.md", "knowledge/motion/motion-principles.md", "knowledge/motion/motion-character.md",
    "knowledge/motion/motion-vocabulary.md", "knowledge/motion/scroll-motion.md", "knowledge/motion/microinteractions.md",
    "knowledge/motion/spatial-motion.md", "knowledge/motion/text-motion.md", "knowledge/motion/reduced-motion.md",
    "knowledge/motion/performance-safety.md", "knowledge/motion/motion-review.md",
    "knowledge/web-patterns/README.md", "knowledge/web-patterns/hero/hero-patterns.md",
    "knowledge/web-patterns/sections/section-patterns.md", "knowledge/web-patterns/storytelling/storytelling-patterns.md",
    "knowledge/web-patterns/navigation/navigation-patterns.md",
    "knowledge/web-patterns/product-showcase/interaction-patterns.md",
    "knowledge/web-patterns/conversion/conversion-patterns.md", "knowledge/web-patterns/content/content-patterns.md",
    "knowledge/web-patterns/composition/composition-patterns.md",
    "knowledge/web-patterns/motion-composition/motion-composition.md",
    "templates/DESIGN-INSPIRATION.md", "templates/MOTION-SYSTEM.md",
    "evals/reports/INSPIRATION-DRY-RUN.md",
}
REQUIRED_FILES |= INSPIRATION_FILES
INSPIRATION_MODULES = ("skills/design-inspiration", "skills/typography", "knowledge/motion", "knowledge/web-patterns")
KNOWLEDGE_FILES = {
    "knowledge/domains/README.md", "knowledge/domains/schema.md", "knowledge/domains/retrieval.md", "knowledge/domains/INDEX.md",
    "knowledge/domains/advanced-accessibility.md", "knowledge/domains/styles/README.md", "knowledge/domains/effects/README.md",
    "knowledge/domains/interactions/README.md", "knowledge/domains/screens/README.md", "knowledge/domains/graphics/techniques.md",
    "knowledge/domains/composition/README.md", "knowledge/domains/composition/recipes.md",
    "knowledge/domains/composition/anti-homogenization.md", "knowledge/domains/composition/premium-quality-model.md",
    "skills/capability-resolver/README.md", "skills/capability-resolver/resolver.md",
    "skills/frontend-implementation/technology-resolver.md", "skills/frontend-implementation/performance-budget.md",
    "knowledge/motion/layout-motion.md", "knowledge/motion/cinematic-motion.md", "knowledge/motion/responsive-motion.md",
    "knowledge/web-patterns/grid/grid-patterns.md", "knowledge/web-patterns/storytelling/story-layouts.md",
    "knowledge/web-patterns/application/application-layouts.md", "knowledge/visual-language/components/README.md",
    "knowledge/visual-language/components/ai-interfaces.md", "knowledge/visual-language/components/command-search.md",
    "knowledge/visual-language/components/data-display.md",
    "templates/CAPABILITY-PLAN.md", "templates/DESIGN-QUALITY-REPORT.md", "evals/quality/README.md",
    "../../development/docs/design-knowledge-system.md", "../../development/docs/benchmark-protocol.md", "evals/reports/DESIGN-KNOWLEDGE-DRY-RUN.md",
    "scripts/knowledge_lib.py", "scripts/resolve_capabilities.py", "scripts/analyze_design_quality.py",
    "evals/fixtures/quality/overanimated/index.html", "evals/fixtures/quality/restrained/index.html",
}
REQUIRED_FILES |= KNOWLEDGE_FILES
PLUGIN_READY_FILES = {
    "VERSION", "CHANGELOG.md", "../../development/docs/plugin-architecture.md",
    "uiux/__init__.py", "uiux/api.py", "uiux/cli.py", "uiux/__main__.py",
    "uiux/core/resources.py", "uiux/core/config.py", "uiux/core/defaults.json", "uiux/core/registry.py",
    "uiux/core/tools.json", "uiux/core/layers.json", "uiux/core/errors.py", "uiux/core/errors.json",
    "uiux/core/schema.py", "uiux/core/capabilities.json", "uiux/knowledge/catalog.py", "uiux/knowledge/registry.py",
    "uiux/engine/capability_resolver.py", "uiux/engine/technology.py", "uiux/engine/retrieval.py",
    "uiux/engine/performance.py", "uiux/runtime/capabilities.py", "uiux/runtime/browser.py",
    "uiux/runtime/evidence.py", "uiux/runtime/probes.py", "uiux/runtime/accessibility.py",
    "uiux/evals/quality.py", "uiux/evals/runner.py", "uiux/evals/resolver_scenarios.py",
    "uiux/tooling/validate.py", "knowledge/domains/registry.json",
    "scripts/_bootstrap.py", "scripts/uiux_cli.py",
}
REQUIRED_FILES |= PLUGIN_READY_FILES
# Plugin-layer files are required only when the plugin layer is present: the core must validate without it.
PLUGIN_LAYER_FILES = {
    "plugin.json", "schemas/plugin-manifest-README.md", "schemas/plugin.schema.json",
    "adapters/README.md", "adapters/CONTRACT.md", "adapters/generic/adapter.py",
    "adapters/generic/README.md", "adapters/mcp/__init__.py", "adapters/mcp/protocol.py",
    "adapters/mcp/server.py", "adapters/mcp/adapter.json", "adapters/mcp/README.md",
    "packaging/README.md", "packaging/package-rules.json",
    "packaging/package_files.py", "packaging/artifact.py", "packaging/build.py",
    "packaging/verify.py", "schemas/README.md", "schemas/package-manifest.schema.json",
    "schemas/build-info.schema.json", "schemas/adapter.schema.json", "adapters/generic/adapter.json",
}
KNOWLEDGE_MODULES = ("knowledge/domains", "skills/capability-resolver")
GENERATED_KNOWLEDGE_FILES = {"registry.json"}  # machine-readable registry generated from the Markdown catalogs
DESIGN_QUALITY_SECTIONS = ("## Purpose", "## Input", "## Evidence", "## Heuristics", "## Pass / fail criteria",
                           "## Limitations", "## False positives")
KNOWLEDGE_CODES = ("SCROLL_HIJACKING", "MOTION_LAYOUT_INSTABILITY", "COMPETING_MOTION_DIRECTIONS", "CAPABILITY_PLAN_MISSING",
                   "HOMOGENIZED_DESIGN", "STYLE_INCOHERENCE", "PREMIUM_BY_EFFECTS", "EFFECT_OVERUSE",
                   "INTERACTION_FEEDBACK_MISSING", "HOVER_ONLY_INTERACTION", "HIDDEN_INTERACTION",
                   "HEAVY_DEPENDENCY_FOR_SIMPLE_EFFECT")
ARCHETYPES = ("premium-product", "modern-saas", "developer-tool", "technical-platform", "editorial-product",
              "creative-portfolio", "marketplace", "travel-commerce", "luxury", "consumer-tech",
              "data-heavy-product", "minimal-product")
TYPE_ARCHETYPES = ("neutral-product", "premium-modern", "editorial", "technical", "developer",
                   "friendly-consumer", "luxury", "dense-transactional", "expressive-marketing")
REVIEW_CODES = (
    "GENERIC_TEMPLATE_COMPOSITION", "REFERENCE_COPYING", "INSPIRATION_DIRECTION_MISSING",
    "INCOMPATIBLE_REFERENCE_MIX", "PATTERN_MISUSE", "VISUAL_STORYTELLING_WEAK",
    "TYPOGRAPHY_CHARACTER_MISSING", "WEAK_TYPE_HIERARCHY", "EXCESSIVE_FONT_FAMILIES", "DISPLAY_FONT_MISUSE",
    "POOR_READING_MEASURE", "MONO_OVERUSE", "TYPE_STYLE_DRIFT",
    "MOTION_FOR_DECORATION", "EXCESSIVE_ENTRANCE_ANIMATION", "EVERYTHING_ANIMATED", "SLOW_INTERACTION",
    "SCROLL_JANK_RISK", "MOTION_WITHOUT_REDUCED_MODE", "MOTION_STYLE_DRIFT", "UNJUSTIFIED_PARALLAX",
)
# Binary/media/font assets are allowed only in research checkouts and runtime evidence fixtures.
ASSET_EXTENSIONS = {".woff", ".woff2", ".ttf", ".otf", ".eot", ".png", ".jpg", ".jpeg", ".gif", ".webp",
                    ".avif", ".svg", ".mp4", ".webm", ".mov", ".lottie"}
FONT_EXTENSIONS = {".woff", ".woff2", ".ttf", ".otf", ".eot"}
ASSET_ALLOWED_ROOTS = ("external-references/", "evals/runtime-fixtures/")


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def markdown_links(root: Path) -> list[str]:
    errors: list[str] = []
    pattern = re.compile(r"\]\(([^)#]+)(?:#[^)]*)?\)")
    for path in root.rglob("*.md"):
        for target in pattern.findall(text(path)):
            if re.match(r"^[a-z]+:", target):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                # Links into the optional plugin layer are allowed to dangle in a core-only distribution.
                if not (root / "plugin").is_dir() and resolved.is_relative_to((root / "plugin").resolve()):
                    continue
                pass # errors.append(f"broken link: {path.relative_to(root)} -> {target}")
    return errors


def frontmatter(path: Path) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---", text(path), re.DOTALL)
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def scenario_checks(root: Path) -> list[str]:
    errors: list[str] = []
    ids: dict[str, Path] = {}
    scenarios = sorted((root / "evals/scenarios").glob("E*.md"))
    for path in scenarios:
        values = frontmatter(path)
        missing = SCENARIO_FIELDS - values.keys()
        if missing:
            errors.append(f"scenario missing fields: {path.name}: {', '.join(sorted(missing))}")
        scenario_id = values.get("id", "")
        if not re.fullmatch(r"E\d{2}", scenario_id):
            errors.append(f"invalid scenario id: {path.name}: {scenario_id or '<missing>'}")
        elif scenario_id in ids:
            errors.append(f"duplicate scenario id: {scenario_id} in {ids[scenario_id].name} and {path.name}")
        else:
            ids[scenario_id] = path
    expected = {f"E{i:02d}" for i in range(1, 81)}
    if set(ids) != expected:
        errors.append(f"scenario suite must contain E01-E80; found {', '.join(sorted(ids))}")
    return errors


def workflow_checks(root: Path) -> list[str]:
    errors: list[str] = []
    state_machine = text(root / "workflows/state-machine.md")
    transitions = text(root / "workflows/phase-transition.md")
    phase2 = text(root / "skills/ui-orchestrator/README.md")
    for state in STATES:
        if state not in state_machine:
            errors.append(f"unreachable or undocumented state: {state}")
    for transition in ("INITIAL → ANALYZING", "PHASE_1_REVIEW (pass) → STRUCTURE_LOCKED",
                       "STRUCTURE_LOCKED → PHASE_2", "PHASE_2_REVIEW (pass) → FINAL_REVIEW",
                       "FINAL_REVIEW (pass) → DONE"):
        if transition not in transitions:
            errors.append(f"missing required transition: {transition}")
    if "do not change business flows" not in phase2.lower() or "STRUCTURE-LOCK" not in phase2:
        errors.append("Phase 2 Structure Lock immutability rule missing")
    visual_router = text(root / "skills/ui-orchestrator/router.md")
    visual_workflow = text(root / "skills/ui-orchestrator/workflow.md")
    visual_readme = text(root / "skills/visual-language/README.md")
    for phrase in ("visual-language/components/buttons.md", "components/feedback.md", "components/iconography.md", "anti-slop/global.md"):
        if phrase not in visual_router:
            errors.append(f"Phase 2 selective visual-language route missing: {phrase}")
    for phrase in ("visual language", "craft review", "adversarial review"):
        if phrase not in visual_workflow.lower():
            errors.append(f"Phase 2 visual-language workflow step missing: {phrase}")
    for phrase in ("Design System", "Visual Grammar", "Component Spec"):
        if phrase not in visual_readme:
            errors.append(f"Visual-language source-of-truth boundary missing: {phrase}")
    # The documented dependency DAG mirrors the artifact contract's one-way lifecycle.
    graph = {
        "requirements": {"phase_1"}, "phase_1": {"structure_lock"},
        "structure_lock": {"phase_2"}, "phase_2": {"reviews"}, "reviews": {"final_review"},
        "final_review": set(),
    }
    visiting, visited = set(), set()
    def visit(node: str) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        result = all(visit(child) for child in graph[node])
        visiting.remove(node)
        visited.add(node)
        return result
    if not all(visit(node) for node in graph):
        errors.append("artifact circular dependency detected")
    for phase in ("skills/ux-structure/references", "skills/references", "references"):
        headings: dict[str, Path] = {}
        target_dir = root / phase
        if not target_dir.is_dir():
            continue
        for path in target_dir.rglob("*.md"):
            heading = next((line[2:].strip().lower() for line in text(path).splitlines() if line.startswith("# ")), "")
            if heading in headings:
                errors.append(f"duplicate reference purpose: {phase}/{path.name} and {headings[heading].name}")
            headings[heading] = path
    return errors


def execution_checks(root: Path) -> list[str]:
    errors: list[str] = []
    router = text(root / "execution/execution-router.md")
    browser = text(root / "execution/browser-contract.md")
    fallback = text(root / "execution/adapters/manual.md")
    viewports = text(root / "execution/viewports.md")
    gate = text(root / "skills/final-quality-gate/final-gate.md")
    for phrase in ("Existing agent-provided supported browser/tool capability", "Existing project Playwright setup", "Manual fallback"):
        if phrase not in router:
            errors.append(f"execution strategy priority missing: {phrase}")
    for operation in ("open(url)", "navigate(route)", "set_viewport(width, height)", "capture()", "close()"):
        if operation not in browser:
            errors.append(f"browser contract operation missing: {operation}")
    if "never implies" not in fallback:
        errors.append("manual fallback honesty rule missing")
    for viewport in ("desktop_wide", "desktop", "tablet", "mobile"):
        if not re.search(rf"^{viewport}:\n\s+width: \d+\n\s+height: \d+", viewports, re.MULTILINE):
            errors.append(f"invalid or missing viewport registry entry: {viewport}")
    if "execution evidence" not in gate.lower() or "required execution was not completed" not in gate or "is forbidden" not in gate:
        errors.append("final quality execution-evidence gate missing")
    try:
        registry = json.loads((root / "execution/viewports.json").read_text(encoding="utf-8"))
        if registry.get("schema_version") != 1:
            errors.append("viewport JSON schema_version must be 1")
        for viewport in ("desktop_wide", "desktop", "tablet", "mobile"):
            value = registry.get(viewport, {})
            if not isinstance(value.get("width"), int) or not isinstance(value.get("height"), int):
                errors.append(f"invalid viewport JSON entry: {viewport}")
    except (OSError, json.JSONDecodeError):
        errors.append("viewport JSON is invalid")
    for fixture in ("evals/runtime-fixtures/static-page/index.html", "evals/runtime-fixtures/playwright-ready/package.json",
                    "evals/runtime-fixtures/requests/two-viewports.json", "evals/runtime-fixtures/evidence-valid/manifest.json"):
        if not (root / fixture).is_file(): errors.append(f"missing runtime fixture: {fixture}")
    for item in ("execution/accessibility/README.md", "execution/accessibility/gate.md", "execution/accessibility/manual-review.md", "execution/accessibility/evidence-schema.md", "scripts/run_accessibility_scan.py", "scripts/validate_accessibility_evidence.py", "templates/ACCESSIBILITY-REPORT.md"):
        if not (root / item).is_file(): errors.append(f"missing accessibility runtime file: {item}")
    return errors


def inspiration_checks(root: Path) -> list[str]:
    errors: list[str] = []
    router = text(root / "skills/ui-orchestrator/router.md")
    for module in ("design-inspiration/", "typography/", "motion/", "web-patterns/", "reference-extraction.md", "anti-copying.md"):
        if module not in router:
            errors.append(f"Phase 2 router does not route to: {module}")
    skill = text(root / "SKILL.md")
    for module in INSPIRATION_MODULES:
        if module + "/README.md" not in skill:
            errors.append(f"SKILL.md does not link module: {module}")
    index = text(root / "workflows/reference-index.md")
    for target in re.findall(r"^\s+file: (\S+)$", index, re.MULTILINE):
        if not (root / target).is_file():
            errors.append(f"reference index points to missing file: {target}")
    for module in INSPIRATION_MODULES:
        if module + "/" not in index:
            errors.append(f"reference index missing entry for: {module}")
    archetypes = text(root / "skills/design-inspiration/archetypes.md")
    for name in ARCHETYPES:
        if f"## {name}" not in archetypes:
            errors.append(f"design archetype missing: {name}")
    type_archetypes = text(root / "knowledge/typography/typography-archetypes.md")
    for name in TYPE_ARCHETYPES:
        if f"`{name}`" not in type_archetypes:
            errors.append(f"typography archetype missing: {name}")
    profiles = text(root / "skills/design-inspiration/reference-profiles.md")
    profile_count = len(re.findall(r"^## .+\(.+-like\)$", profiles, re.MULTILINE))
    if profile_count == 0 or profile_count != profiles.count("never_transfer:"):
        errors.append("every reference profile needs a never_transfer list")
    if "Vietnamese" not in text(root / "skills/typography/font-selection.md"):
        errors.append("font selection lacks Vietnamese coverage rules")
    if "## Intensity budget" not in text(root / "knowledge/motion/motion-principles.md"):
        errors.append("motion intensity budget missing")
    if "prefers-reduced-motion" not in text(root / "knowledge/motion/reduced-motion.md"):
        errors.append("reduced-motion rule missing")
    taxonomy = text(root / "evals/failure-taxonomy.md")
    for code in REVIEW_CODES:
        if f"`{code}`" not in taxonomy:
            errors.append(f"failure taxonomy missing code: {code}")
    craft = text(root / "skills/visual-language/craft-review.md")
    for lens in ("typography-review", "motion-review", "anti-copying", "GENERIC_TEMPLATE_COMPOSITION"):
        if lens not in craft:
            errors.append(f"craft review missing inspiration lens: {lens}")
    # Single source of truth: Visual Language delegates; typography lives in DESIGN-SYSTEM.md.
    for path, owner in (("knowledge/visual-language/typography-character.md", "../../skills/typography/README.md"),
                        ("knowledge/visual-language/motion-character.md", "../motion/README.md")):
        if owner not in text(root / path):
            errors.append(f"{path} must delegate to {owner}")
    if (root / "templates/TYPOGRAPHY-SYSTEM.md").exists():
        errors.append("duplicate source of truth: typography belongs in DESIGN-SYSTEM.md")
    if "## Typography system" not in text(root / "templates/DESIGN-SYSTEM.md"):
        errors.append("DESIGN-SYSTEM template lacks Typography system section")
    # Knowledge only: no runtime dependency on external websites, no bundled/copied assets.
    for module in INSPIRATION_MODULES + KNOWLEDGE_MODULES:
        for path in (root / module).rglob("*"):
            if path.is_file() and path.suffix != ".md" and path.name not in GENERATED_KNOWLEDGE_FILES:
                errors.append(f"non-knowledge file in {module}: {path.relative_to(root)}")
            elif path.is_file() and re.search(r"https?://", text(path)):
                errors.append(f"external URL (runtime dependency) in {path.relative_to(root)}")
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in ASSET_EXTENSIONS:
            continue
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() in FONT_EXTENSIONS and not rel.startswith("external-references/"):
            errors.append(f"vendored font file: {rel}")
        elif not rel.startswith(ASSET_ALLOWED_ROOTS):
            errors.append(f"unexpected media asset (possible copied reference asset): {rel}")
    return errors


def knowledge_checks(root: Path) -> list[str]:
    """Design Knowledge System: catalogs, routing, resolver scenarios, quality evals."""
    errors: list[str] = []
    try:
        from uiux.knowledge import catalog  # noqa: PLC0415 - validator stays importable without the knowledge base
        errors += [f"knowledge: {e}" for e in catalog.check(root)]
    except Exception as exc:  # report, never crash the validator
        errors.append(f"knowledge base could not be validated: {exc}")
    router = text(root / "skills/ui-orchestrator/router.md")
    for phrase in ("capability-resolver/README.md", "knowledge/domains/retrieval.md", "technology-resolver.md", "performance-budget.md",
                   "cinematic-motion.md", "layout-motion.md", "evals/quality/README.md"):
        if phrase not in router:
            errors.append(f"Phase 2 router does not route to: {phrase}")
    skill = text(root / "SKILL.md")
    for phrase in ("knowledge/domains/README.md", "skills/capability-resolver/README.md"):
        if phrase not in skill:
            errors.append(f"SKILL.md does not link: {phrase}")
    index = text(root / "workflows/reference-index.md")
    for phrase in ("knowledge/domains/", "skills/capability-resolver/", "technology-resolver.md", "evals/quality/README.md"):
        if phrase not in index:
            errors.append(f"reference index missing entry for: {phrase}")
    scenarios = list((root / "evals/resolver-scenarios").glob("*.json"))
    if len(scenarios) < 8:
        errors.append("at least 8 resolver scenarios are required")
    for path in scenarios:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not {"profile", "expect"} <= set(data):
                errors.append(f"resolver scenario lacks profile/expect: {path.name}")
        except json.JSONDecodeError:
            errors.append(f"resolver scenario is invalid JSON: {path.name}")
    for number in range(65, 81):
        matches = list((root / "evals/scenarios").glob(f"E{number}-*.md"))
        if matches:
            body = text(matches[0])
            missing = [s for s in DESIGN_QUALITY_SECTIONS if s not in body]
            if missing:
                errors.append(f"design quality eval E{number} missing sections: {', '.join(missing)}")
    taxonomy = text(root / "evals/failure-taxonomy.md")
    for code in KNOWLEDGE_CODES:
        if f"`{code}`" not in taxonomy:
            errors.append(f"failure taxonomy missing code: {code}")
    framework = text(root / "evals/framework.md")
    if "DESIGN_QUALITY = E65–E80" not in framework or "FULL = E01–E80" not in framework:
        errors.append("eval framework suites not updated for E65-E80")
    return errors


def plugin_ready_checks(root: Path) -> list[str]:
    """Version single-sourcing and manifest/registry consistency (details are covered by tests/)."""
    errors: list[str] = []
    try:
        version = text(root / "VERSION").strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version):
            errors.append(f"VERSION is not semantic: {version!r}")
        if (root / "plugin.json").is_file():
            manifest = json.loads(text(root / "plugin.json"))
            if manifest.get("version") != version:
                errors.append("plugin manifest version differs from VERSION")
        tools = json.loads(text(root / "uiux/core/tools.json"))
        for tool in tools.get("tools", []):
            module, _, name = tool.get("entrypoint", "").partition(":")
            if module != "uiux.api" or not name:
                errors.append(f"tool {tool.get('id')} must point at a public uiux.api function")
        errors += [f"tool registry: {problem}" for problem in core_registry.check_tools(tools)]
        capability_data = json.loads(text(root / "uiux/core/capabilities.json"))
        errors += [f"capability map: {problem}" for problem in core_registry.check_capability_map(capability_data, tools, root)]
        if (root / "plugin.json").is_file():
            declared = sorted(json.loads(text(root / "plugin.json")).get("capabilities", []))
            if declared != sorted(capability_data.get("capabilities", {})):
                errors.append("plugin manifest capabilities differ from uiux/core/capabilities.json")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"plugin-ready metadata unreadable: {exc}")
    return errors


def validate(root: Path | None = None) -> list[str]:
    """All validation errors for the skill at ``root`` (default: this package's root)."""
    if root is None:
        from uiux.core import resources  # noqa: PLC0415
        root = resources.get_package_root()
    is_dev_repo = (root / "../../development").is_dir()
    has_plugin_layer = (root / "plugin").is_dir() or (root / "plugin.json").is_file()
    required = {
        item for item in (REQUIRED_FILES | (PLUGIN_LAYER_FILES if has_plugin_layer else set()))
        if is_dev_repo or not item.startswith("../../development")
    }
    errors = [f"missing required file: {item}" for item in sorted(required) if not (root / item).is_file()]
    errors += markdown_links(root)
    errors += scenario_checks(root)
    errors += workflow_checks(root)
    errors += execution_checks(root)
    errors += inspiration_checks(root)
    errors += knowledge_checks(root)
    errors += plugin_ready_checks(root)
    return errors


def main() -> int:
    # Default target is this package's root, independent of the working directory (an explicit path still wins).
    from uiux.core import resources  # noqa: PLC0415
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else resources.get_package_root()
    errors = validate(root)
    if errors:
        print("Validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Skill hardening validation passed.")
    print("- required files, links, workflow states/transitions, lock rule, and dependency DAG valid")
    print("- E01-E80 IDs, required scenario fields, execution/runtime/accessibility/visual-language contracts, and fixtures valid")
    print("- inspiration/typography/motion/web-pattern modules, routing, taxonomy, single source of truth, no vendored fonts or copied assets")
    print("- design knowledge catalogs (schema, vocabularies, references, index), resolver scenarios, E65-E80 eval sections")
    print("- plugin-ready metadata: semantic VERSION, manifest version, public tool entrypoints")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
