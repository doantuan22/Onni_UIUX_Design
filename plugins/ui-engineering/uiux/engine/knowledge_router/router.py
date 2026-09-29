"""Knowledge Router: Deterministic, context-efficient, framework-aware knowledge routing.

Maps:
Repo Profile + Existing UI Profile + Task Intent + Permissions
    -> Knowledge Load Plan
"""
from __future__ import annotations

from typing import Any

from uiux.engine.knowledge_router.budget import ContextBudgetManager
from uiux.engine.knowledge_router.domain_extension import (
    classify_domain,
    get_domain_pack,
    query_domain_subtopics,
    resolve_domain_pack,
)
from uiux.engine.knowledge_router.intent import (
    ACCESSIBILITY_FIX,
    AUDIT_ONLY,
    COMPONENT_REFACTOR,
    CONSISTENCY_FIX,
    CREATE_UI,
    DESIGN_SYSTEM_WORK,
    FORM_UX,
    FULL_REDESIGN,
    GENERAL_UI,
    IMPROVE_UI,
    MOTION,
    NAVIGATION_UX,
    PAGE_REDESIGN,
    RESPONSIVE_FIX,
    RUNTIME_VALIDATION,
    VISUAL_POLISH,
    classify_task_intent,
    classify_task_intents,
)
from uiux.engine.knowledge_router.metadata import (
    DESIGN_SKILLS,
    DOMAIN_PACKS,
    FRAMEWORK_PACKS,
    PRESERVATION_PACKS,
    RUNTIME_VALIDATION_PACKS,
    STYLING_PACKS,
    check_version_compatibility,
)
from uiux.engine.knowledge_router.resolver import KnowledgeResolver
from uiux.engine.preservation import L1, L2, L3


class KnowledgeRouter:
    """Deterministic routing engine that produces machine-readable knowledge load plans."""

    def __init__(self, resolver: KnowledgeResolver | None = None, budget_limit_points: int = 35):
        self.resolver = resolver or KnowledgeResolver()
        self.budget_manager = ContextBudgetManager(budget_limit_points=budget_limit_points)

    def route(self, request: dict[str, Any]) -> dict[str, Any]:
        """Produce a complete, validated Knowledge Load Plan from a Knowledge Request."""
        user_request = (request.get("user_request") or "").strip()
        raw_intent = request.get("task_intent")
        workflow = request.get("workflow", "existing-ui")
        requested_scope = request.get("requested_scope", "global")
        repo_profile = request.get("repo_profile") or {}
        existing_ui_profile = request.get("existing_ui_profile") or {}
        preservation_profile = request.get("preservation_profile") or {}
        explicit_constraints = request.get("explicit_constraints") or {}

        diagnostics: dict[str, list[str]] = {
            "warnings": [],
            "conflicts": [],
            "unsupported": [],
        }
        rationale: list[str] = []

        # 1. Normalize Monorepo Scope
        active_repo_profile = repo_profile
        if "applications" in repo_profile and requested_scope in repo_profile["applications"]:
            active_repo_profile = repo_profile["applications"][requested_scope].get("repo_profile", repo_profile)
            rationale.append(f"Monorepo scope applied: resolved configuration for sub-app '{requested_scope}'.")
        elif "applications" in repo_profile:
            # Check if user prompt targets a specific app
            for app_name, app_data in repo_profile["applications"].items():
                if app_name.lower() in user_request.lower():
                    active_repo_profile = app_data.get("repo_profile", repo_profile)
                    rationale.append(f"Monorepo scope resolved from request context: '{app_name}'.")
                    break

        # 2. Classify Task Intent (Compound Intent Support - P1.1)
        intent_info = classify_task_intents(user_request, raw_intent)
        task_intent = intent_info["primary_intent"]
        secondary_intents = intent_info["secondary_intents"]
        all_intents = intent_info["all_intents"]
        if intent_info.get("compound"):
            rationale.append(f"Compound intent classified: primary '{task_intent}', secondary: {secondary_intents}.")
        else:
            rationale.append(f"Task intent classified as '{task_intent}'.")

        # 3. Resolve Framework Pack
        fw_data = active_repo_profile.get("framework") or {}
        fw_name = fw_data.get("name", "unknown")
        fw_version = fw_data.get("version")
        fw_conflicts = fw_data.get("conflicting_signals") or []

        if fw_conflicts:
            diagnostics["conflicts"].extend(fw_conflicts)
            diagnostics["warnings"].append(f"Conflicting framework signals detected for '{fw_name}'. Resolved using highest confidence evidence.")

        selected_framework_packs: list[dict[str, Any]] = []
        framework_pack_id = f"framework.{fw_name}"

        pack_entry: dict[str, Any] | None = None
        if framework_pack_id in FRAMEWORK_PACKS:
            pack_entry = dict(FRAMEWORK_PACKS[framework_pack_id])
        else:
            cat_entry = self.resolver.locate_catalog_entry(framework_pack_id)
            if cat_entry and cat_entry.get("kind") == "framework":
                pack_entry = cat_entry
                pack_entry["version_features"] = {}

        if pack_entry:
            v_check = check_version_compatibility(fw_version, pack_entry.get("version_features"))
            pack_entry["version_guidance"] = v_check["active_guidance_tier"]
            pack_entry["compatible_features"] = v_check["compatible_features"]
            pack_entry["suppressed_features"] = v_check["suppressed_features"]
            if fw_version:
                pack_entry["version"] = str(fw_version)
                pack_entry["reason"] = f"Detected {pack_entry['name']} (version {fw_version}, guidance: {v_check['active_guidance_tier']}) in repository profile."
            else:
                pack_entry["version"] = None
                pack_entry["reason"] = f"Detected {pack_entry['name']} (unspecified version, using generic safe guidance) in repository profile."
            selected_framework_packs.append(pack_entry)
            rationale.append(f"Selected framework pack '{framework_pack_id}' with guidance tier '{v_check['active_guidance_tier']}'.")
        else:
            fallback_pack = dict(FRAMEWORK_PACKS["framework.fallback"])
            fallback_pack["reason"] = f"Framework '{fw_name}' has no specific pack; loaded safe universal frontend fallback."
            selected_framework_packs.append(fallback_pack)
            diagnostics["warnings"].append(f"No specific framework pack for '{fw_name}'; fallback applied.")
            rationale.append("Applied generic frontend fallback pack.")

        # 4. Resolve Styling & UI Library Packs
        styling_data = active_repo_profile.get("styling_system") or {}
        primary_styling = styling_data.get("primary")
        secondary_styling = styling_data.get("secondary")
        detected_stylings = styling_data.get("detected") or []

        selected_styling_packs: list[dict[str, Any]] = []
        selected_ui_library_packs: list[dict[str, Any]] = []

        # Map styling names to pack IDs
        styling_name_map = {
            "tailwindcss": "styling.tailwindcss",
            "bootstrap": "styling.bootstrap",
            "plain_css": "styling.plain_css",
            "css_modules": "styling.css_modules",
            "sass_scss": "styling.sass_scss",
            "sass": "styling.sass_scss",
            "scss": "styling.sass_scss",
            "styled_components": "styling.styled_components",
            "emotion": "styling.emotion",
            "mui": "styling.mui",
            "shadcn_ui": "ui_library.shadcn_ui",
        }

        # Check primary styling
        if primary_styling and primary_styling in styling_name_map:
            pack_id = styling_name_map[primary_styling]
            entry = None
            if pack_id in STYLING_PACKS:
                entry = dict(STYLING_PACKS[pack_id])
            else:
                cat_entry = self.resolver.locate_catalog_entry(pack_id)
                if cat_entry and cat_entry.get("kind") == "styling":
                    entry = cat_entry
            
            if entry:
                entry["reason"] = f"Primary styling system '{primary_styling}' active in repository."
                selected_styling_packs.append(entry)
                rationale.append(f"Selected primary styling pack '{pack_id}'.")

        # Check secondary styling (supports multi-styling composition, e.g. Tailwind + CSS Modules)
        if secondary_styling and secondary_styling in styling_name_map and secondary_styling != primary_styling:
            pack_id = styling_name_map[secondary_styling]
            entry = None
            if pack_id in STYLING_PACKS:
                entry = dict(STYLING_PACKS[pack_id])
            else:
                cat_entry = self.resolver.locate_catalog_entry(pack_id)
                if cat_entry and cat_entry.get("kind") == "styling":
                    entry = cat_entry
            
            if entry:
                entry["priority"] = "medium"
                entry["reason"] = f"Secondary styling system '{secondary_styling}' detected in repository."
                selected_styling_packs.append(entry)
                rationale.append(f"Selected secondary styling pack '{pack_id}'.")

        # Check UI Library (e.g. shadcn/ui or mui)
        ui_lib_data = active_repo_profile.get("ui_library") or {}
        ui_lib_name = ui_lib_data.get("name")
        if ui_lib_name == "shadcn_ui" or "shadcn_ui" in detected_stylings:
            shadcn_pack = dict(STYLING_PACKS["ui_library.shadcn_ui"])
            shadcn_pack["reason"] = "shadcn/ui component library active in repository."
            selected_ui_library_packs.append(shadcn_pack)
            rationale.append("Selected UI library pack 'ui_library.shadcn_ui'.")
        elif ui_lib_name:
            lib_pack_id = f"styling.{ui_lib_name}"
            if lib_pack_id in STYLING_PACKS:
                lib_pack = dict(STYLING_PACKS[lib_pack_id])
            else:
                cat_entry = self.resolver.locate_catalog_entry(lib_pack_id)
                if cat_entry and cat_entry.get("kind") in ("styling", "ui_library"):
                    lib_pack = cat_entry
                else:
                    lib_pack = None
            if lib_pack:
                lib_pack["reason"] = f"UI library '{ui_lib_name}' active in repository."
                selected_ui_library_packs.append(lib_pack)

        # 5. Preservation Context & Invariants
        preservation_context: dict[str, Any] = {
            "preservation_required": workflow == "existing-ui",
            "palette": "locked" if workflow == "existing-ui" else "editable",
            "brand_identity": "locked" if workflow == "existing-ui" else "editable",
            "layout_identity": "protected" if workflow == "existing-ui" else "editable",
            "navigation": "protected" if workflow == "existing-ui" else "editable",
            "allowed_change_level": "L1",
            "scope": requested_scope,
            "precedence_rules": [
                "1. Explicit user instruction",
                "2. Existing brand identity",
                "3. Existing design system",
                "4. Existing UX / information architecture",
                "5. Repository / framework constraints",
                "6. Domain best practices",
                "7. Design inspiration",
                "8. AI preference",
            ],
        }

        # Override preservation context if explicit preservation_profile exists
        if preservation_profile:
            prot_design = preservation_profile.get("protected_design", {})
            if "color_palette" in prot_design:
                preservation_context["palette"] = "locked" if prot_design["color_palette"].get("policy") == "locked" else "editable"
            if "brand_identity" in prot_design:
                preservation_context["brand_identity"] = "locked" if prot_design["brand_identity"].get("policy") == "locked" else "editable"
            if "overall_layout_identity" in prot_design:
                preservation_context["layout_identity"] = "protected" if prot_design["overall_layout_identity"].get("policy") == "protected" else "editable"
            if "navigation_model" in prot_design:
                preservation_context["navigation"] = "protected" if prot_design["navigation_model"].get("policy") == "protected" else "editable"

            allowed_changes = preservation_profile.get("allowed_changes", {})
            max_level = allowed_changes.get("max_level", "L1")
            preservation_context["allowed_change_level"] = max_level

        # Selected Skills & Knowledge Candidates
        candidate_skills: list[dict[str, Any]] = []
        candidate_knowledge: list[dict[str, Any]] = []

        # Helper to query catalog and format entries according to Section 8 contract
        def _add_catalog_knowledge(
            entry_id: str,
            reason: str,
            priority: str = "medium",
            required: bool = False,
            relevance: float = 0.85,
        ) -> bool:
            entry = self.resolver.locate_catalog_entry(entry_id)
            if entry and not any(k["id"] == entry_id for k in candidate_knowledge):
                candidate_knowledge.append({
                    "id": entry["id"],
                    "category": entry.get("collection", "general"),
                    "name": entry.get("name", entry["id"]),
                    "reason": reason,
                    "priority": priority,
                    "source": entry.get("file", ""),
                    "reference": f"{entry.get('file', '')}:{entry.get('line', 1)}",
                    "relevance": relevance,
                    "required": required,
                    "summary": entry.get("summary", ""),
                    "weight": "small",
                })
                return True
            return False

        # Hard preservation knowledge for Existing UI
        if workflow == "existing-ui":
            pres_inv = dict(PRESERVATION_PACKS["preservation.existing_ui_invariants"])
            pres_inv["reason"] = "Existing UI workflow requires strict adherence to preservation invariants and change budgets."
            candidate_knowledge.append(pres_inv)

        # 6. Task Intent-Driven Routing
        is_existing_l1 = workflow == "existing-ui" and preservation_context.get("allowed_change_level") == L1
        req_lower = user_request.lower()

        # Skill selection based on primary & secondary intents
        if RESPONSIVE_FIX in all_intents:
            resp_skill = dict(DESIGN_SKILLS["skill.responsive_interaction"])
            resp_skill["reason"] = "Responsive layout refinement requested."
            candidate_skills.append(resp_skill)

        if ACCESSIBILITY_FIX in all_intents:
            qa_skill = dict(DESIGN_SKILLS["skill.visual_qa"])
            qa_skill["reason"] = "Accessibility compliance and contrast verification task."
            candidate_skills.append(qa_skill)

        if COMPONENT_REFACTOR in all_intents or DESIGN_SYSTEM_WORK in all_intents:
            comp_skill = dict(DESIGN_SKILLS["skill.component_realization"])
            comp_skill["reason"] = "Component realization and design token conventions task."
            candidate_skills.append(comp_skill)

        if NAVIGATION_UX in all_intents:
            nav_skill = dict(DESIGN_SKILLS["skill.ux_structure"])
            nav_skill["reason"] = "Navigation structure and user flow task."
            candidate_skills.append(nav_skill)

        if any(i in (PAGE_REDESIGN, FULL_REDESIGN) for i in all_intents):
            if is_existing_l1:
                diagnostics["warnings"].append("Major redesign requested but allowed change level is L1; suppressed full redesign knowledge.")
                qa_skill = dict(DESIGN_SKILLS["skill.visual_qa"])
                qa_skill["reason"] = "L1 change budget limits task to safe visual refinement."
                candidate_skills.append(qa_skill)
            else:
                ux_skill = dict(DESIGN_SKILLS["skill.ux_structure"])
                ux_skill["reason"] = "Page architecture redesign task."
                candidate_skills.append(ux_skill)
                if workflow == "greenfield" or preservation_context.get("allowed_change_level") == L3:
                    dir_skill = dict(DESIGN_SKILLS["skill.design_direction"])
                    dir_skill["reason"] = "Holistic design direction for page restructuring."
                    candidate_skills.append(dir_skill)

        if workflow == "greenfield" and not any(s["id"] == "skill.design_direction" for s in candidate_skills):
            dir_skill = dict(DESIGN_SKILLS["skill.design_direction"])
            dir_skill["reason"] = "Greenfield interface design direction."
            candidate_skills.append(dir_skill)

        if not any(s["id"] == "skill.visual_qa" for s in candidate_skills):
            qa_skill = dict(DESIGN_SKILLS["skill.visual_qa"])
            qa_skill["reason"] = "General visual quality verification."
            candidate_skills.append(qa_skill)

        gate_skill = dict(DESIGN_SKILLS["skill.final_quality_gate"])
        gate_skill["reason"] = "Pre-delivery quality gate and non-regression check."
        candidate_skills.append(gate_skill)

        # 6b. Domain Intelligence Classification (Phase 5 + P1.3)
        explicit_domain_input = request.get("domain") or repo_profile.get("domain") or repo_profile.get("detected_domain")
        domain_classification = classify_domain(
            user_request=user_request,
            repo_profile=repo_profile,
            explicit_domain=explicit_domain_input,
            requested_scope=requested_scope,
        )

        primary_domain_name = domain_classification.get("primary_domain", "general")
        secondary_domain_names = domain_classification.get("secondary_domains", [])
        domain_confidence = domain_classification.get("confidence", 0.0)
        domain_evidence = domain_classification.get("evidence", [])
        domain_conflicts = domain_classification.get("conflicts", [])
        domain_source = domain_classification.get("source", "inferred")

        for conf in domain_conflicts:
            diagnostics["warnings"].append(conf)

        # 6c. Actual Knowledge Catalog Routing (P0.5, P1.2, Hardening #4)
        # --- Screen Knowledge ---
        if primary_domain_name == "hospitality_travel" or any(w in req_lower for w in ("hotel", "travel", "rooms", "room", "booking", "destinations", "reservation", "resort")):
            _add_catalog_knowledge("recipe.travel-booking", "Travel and hotel booking flow recipe with search, room selection, and pricing clarity.", priority="high")
            _add_catalog_knowledge("screen.search", "Availability search and destination filter screen pattern.", priority="high")
            _add_catalog_knowledge("screen.checkout", "Booking summary, room pricing, and reservation checkout screen.", priority="high")
        elif primary_domain_name == "ecommerce" or any(w in req_lower for w in ("cart", "checkout", "ecommerce", "store", "shop")):
            _add_catalog_knowledge("recipe.consumer-app", "Consumer ecommerce and checkout UX flow recipe.", priority="high")
            _add_catalog_knowledge("screen.checkout", "Multi-step checkout and order summary screen pattern.", priority="high")
            _add_catalog_knowledge("component.dialogs-drawers", "Slide-over cart drawer and modal dialogs.", priority="high")
        elif any(w in req_lower for w in ("dashboard", "workload", "cluster", "deploy", "admin", "metrics", "analytics")):
            _add_catalog_knowledge("screen.dashboard", "Dashboard overview and workload monitoring screen pattern.", priority="high")
            _add_catalog_knowledge("screen.data-table", "Data table and status tracking screen pattern.", priority="medium")
        elif any(w in req_lower for w in ("landing", "hero", "showcase", "marketing", "home", "product")):
            _add_catalog_knowledge("screen.onboarding", "Public landing page and product showcase pattern.", priority="high")
            _add_catalog_knowledge("screen.pricing", "Feature tier and pricing matrix screen pattern.", priority="medium")
        elif any(w in req_lower for w in ("form", "auth", "login", "register", "signup", "contact")):
            _add_catalog_knowledge("screen.authentication", "Authentication and account form screen pattern.", priority="high")
            _add_catalog_knowledge("screen.settings", "Form controls and preference screen pattern.", priority="medium")
        else:
            if workflow == "greenfield":
                _add_catalog_knowledge("screen.onboarding", "Default interface screen architecture.", priority="medium")
            else:
                _add_catalog_knowledge("screen.dashboard", "Default application screen architecture.", priority="medium")

        # Intentional UI States
        if any(w in req_lower for w in ("state", "loading", "skeleton", "empty", "error", "fallback", "pending", "failed")):
            _add_catalog_knowledge("screen.loading-state", "Loading skeleton and shimmer feedback patterns.", priority="medium")
            _add_catalog_knowledge("screen.empty-state", "Empty state and filter reset patterns.", priority="medium")
            _add_catalog_knowledge("screen.error-state", "Error boundary and network failure recovery patterns.", priority="medium")

        # --- Layout Knowledge ---
        if any(w in req_lower for w in ("dashboard", "sidebar", "workspace", "drawer", "shell")) and primary_domain_name != "hospitality_travel":
            _add_catalog_knowledge("layout.app-dashboard-shell", "Application dashboard shell with sidebar and topbar.", priority="high")
            _add_catalog_knowledge("layout.grid-dense-data", "Dense metrics and status grid layout.", priority="medium")
        elif primary_domain_name == "hospitality_travel" or any(w in req_lower for w in ("hero", "landing", "card", "cards", "section", "sections")):
            _add_catalog_knowledge("layout.hero-centered", "Hero section composition pattern.", priority="high")
            _add_catalog_knowledge("layout.grid-card-matrix", "Card matrix and feature section layout pattern.", priority="medium")

        if RESPONSIVE_FIX in all_intents or any(w in req_lower for w in ("responsive", "mobile", "tablet")):
            _add_catalog_knowledge("layout.app-sidebar-workspace", "Responsive layout with collapsible sidebar drawer.", priority="high")
            _add_catalog_knowledge("layout.grid-card-matrix", "Responsive multi-column card layout.", priority="medium")

        if "bento" in req_lower:
            _add_catalog_knowledge("layout.grid-bento", "Bento grid layout composition.", priority="medium")

        # --- Interaction & Component Grammar Knowledge ---
        if NAVIGATION_UX in all_intents or any(w in req_lower for w in ("nav", "navbar", "sidebar", "drawer", "menu")):
            _add_catalog_knowledge("component.navigation", "Navigation bar and responsive sidebar component grammar.", priority="high")
            _add_catalog_knowledge("component.dialogs-drawers", "Modal dialog and slide-over drawer component grammar.", priority="high")
            _add_catalog_knowledge("interaction.keyboard-navigation", "Keyboard focus order and accessible tab navigation.", priority="medium")

        if any(w in req_lower for w in ("modal", "drawer", "dialog", "popup")):
            _add_catalog_knowledge("component.dialogs-drawers", "Modal and slide-over dialog component grammar.", priority="high")
            _add_catalog_knowledge("interaction.focus-management", "Focus trapping and keyboard dismissal.", priority="medium")

        if any(w in req_lower for w in ("search", "filter", "chip", "chips", "query")):
            _add_catalog_knowledge("component.command-search", "Command palette and search input component grammar.", priority="medium")
            _add_catalog_knowledge("interaction.command-palette", "Interactive quick-action command palette.", priority="medium")

        if any(w in req_lower for w in ("table", "list", "row", "rows", "column")):
            _add_catalog_knowledge("component.tables-lists", "Responsive data table and list component grammar.", priority="medium")
            _add_catalog_knowledge("interaction.progressive-disclosure", "Progressive disclosure for complex data rows.", priority="low")

        if FORM_UX in all_intents or any(w in req_lower for w in ("form", "input", "submit", "contact", "button")):
            _add_catalog_knowledge("component.form-controls", "Form control components with validation state styling.", priority="high")
            _add_catalog_knowledge("component.buttons", "Interactive buttons with loading and disabled states.", priority="medium")

        # --- Typography & Style Knowledge ---
        _add_catalog_knowledge("component.typography-headings", "Typography scale, line-height, and semantic headings.", priority="medium")

        # Style & Recipe (if greenfield or permitted)
        if not is_existing_l1:
            if primary_domain_name == "hospitality_travel":
                _add_catalog_knowledge("recipe.travel-booking", "End-to-end travel and hotel booking recipe.", priority="high")
            elif any(w in req_lower for w in ("saas", "cloud", "dashboard", "workload")):
                _add_catalog_knowledge("style.modern-saas", "Modern SaaS visual aesthetic and token palette.", priority="medium")
                _add_catalog_knowledge("recipe.premium-saas", "End-to-end premium SaaS product recipe.", priority="medium")
            elif any(w in req_lower for w in ("dev", "developer", "terminal", "code")):
                _add_catalog_knowledge("style.developer-tool", "Developer tool aesthetic with high contrast.", priority="medium")
            elif any(w in req_lower for w in ("minimal", "clean")):
                _add_catalog_knowledge("style.minimal", "Minimalist visual aesthetic and whitespace rhythm.", priority="medium")
            elif "bento" in req_lower:
                _add_catalog_knowledge("style.bento", "Bento grid visual aesthetic.", priority="medium")

        # --- Effects & Graphics Knowledge ---
        if any(w in req_lower for w in ("glass", "glassmorphism", "blur", "backdrop", "glow", "gradient", "modern", "visual", "polish")):
            _add_catalog_knowledge("effect.glass", "Glassmorphism, frosted backdrop blur and specular highlights.", priority="medium")
            _add_catalog_knowledge("effect.gradient", "Subtle multi-stop background gradient curves.", priority="low")

        if any(w in req_lower for w in ("illustration", "graphic", "canvas", "particle")):
            _add_catalog_knowledge("graphics.interactive-illustration", "Interactive illustration pattern.", priority="low")

        # --- Motion Knowledge & Framework-Specific Technology (P1.2) ---
        motion_requested = (
            MOTION in all_intents
            or any(w in req_lower for w in ("animate", "animated", "animation", "animations", "motion", "transition", "transitions", "drawer", "fade", "reveal", "stagger"))
        )
        if motion_requested:
            _add_catalog_knowledge("motion.fade-up", "Smooth entrance fade-up animation curve.", priority="medium")
            _add_catalog_knowledge("motion.stagger", "Staggered entrance animation for lists and cards.", priority="medium")
            _add_catalog_knowledge("motion.clip-reveal", "Reveal transition for drawers and cards.", priority="low")

            # Framework-aware motion library check (P1.2)
            has_framer = False
            deps = active_repo_profile.get("dependencies") or {}
            if isinstance(deps, dict):
                has_framer = any("framer-motion" in k or "motion" in k for k in deps)
            if active_repo_profile.get("motion_library") in ("framer_motion", "motion", "framer-motion"):
                has_framer = True

            if has_framer:
                _add_catalog_knowledge("tech.motion", "Framer Motion library reference from repository dependencies.", priority="high", relevance=0.95)
                rationale.append("Prioritized existing motion library 'Framer Motion' from repository dependencies.")
            else:
                _add_catalog_knowledge("tech.css", "Native CSS transitions and keyframes without third-party dependencies.", priority="high", relevance=0.95)
                _add_catalog_knowledge("tech.view-transitions", "Browser native View Transitions API guidance.", priority="medium", relevance=0.85)
                rationale.append("No third-party motion library declared; routed native CSS and View Transitions guidance to prevent unnecessary dependencies.")

        # 7. Runtime Validation Routing
        selected_runtime_packs: list[dict[str, Any]] = []
        if RESPONSIVE_FIX in all_intents:
            rt_entry = dict(RUNTIME_VALIDATION_PACKS["runtime.responsive_viewport"])
            rt_entry["reason"] = "Validates layout against mobile/tablet/desktop viewports."
            selected_runtime_packs.append(rt_entry)
        elif ACCESSIBILITY_FIX in all_intents:
            rt_entry = dict(RUNTIME_VALIDATION_PACKS["runtime.accessibility_audit"])
            rt_entry["reason"] = "Validates WCAG AA contrast, label associations, and keyboard focus."
            selected_runtime_packs.append(rt_entry)
        elif FORM_UX in all_intents:
            rt_entry = dict(RUNTIME_VALIDATION_PACKS["runtime.form_interaction"])
            rt_entry["reason"] = "Validates form blur validation, error messages, and submit states."
            selected_runtime_packs.append(rt_entry)
        else:
            rt_entry = dict(RUNTIME_VALIDATION_PACKS["runtime.smoke_test"])
            rt_entry["reason"] = "Validates clean page render without console errors."
            selected_runtime_packs.append(rt_entry)

        # 8. Domain Intelligence Integration (Phase 5 + P1.3)

        selected_domain_packs: list[dict[str, Any]] = []
        domain_context_primary: dict[str, Any] | None = None
        domain_context_secondary: dict[str, Any] | None = None
        all_domain_subtopics: list[str] = []
        all_applied_patterns: list[str] = []
        all_anti_patterns: list[str] = []
        all_required_states: list[str] = []

        if primary_domain_name and primary_domain_name != "general":
            primary_pack_meta = get_domain_pack(primary_domain_name)
            if primary_pack_meta:
                # Query subtopics relevant to task intent and user request
                subtopics = query_domain_subtopics(primary_domain_name, user_request, task_intent)
                all_domain_subtopics.extend(subtopics)

                # Determine if task is purely local/component without flow change
                is_local_task = task_intent in (COMPONENT_REFACTOR, VISUAL_POLISH, CONSISTENCY_FIX) and not subtopics
                domain_weight = "small" if is_local_task else primary_pack_meta.get("weight", "medium")

                reason_text = (
                    f"Domain design intelligence for {primary_pack_meta['name']} "
                    f"(subtopics: {', '.join(subtopics) if subtopics else 'general conventions'})."
                )

                domain_entry = {
                    "id": primary_pack_meta["id"],
                    "category": "domain",
                    "name": primary_pack_meta["name"],
                    "reason": reason_text,
                    "priority": "high",
                    "source": primary_pack_meta["source"],
                    "required": False,  # Non-mandatory so budget can prune if necessary
                    "weight": domain_weight,
                    "version": primary_pack_meta.get("version", "1.0.0"),
                }
                selected_domain_packs.append(domain_entry)

                domain_context_primary = {
                    "id": primary_pack_meta["id"],
                    "domain": primary_domain_name,
                    "confidence": domain_confidence,
                    "evidence": domain_evidence,
                    "selected_subtopics": subtopics,
                }
                all_applied_patterns.extend(primary_pack_meta.get("critical_flows", []))
                all_anti_patterns.extend(primary_pack_meta.get("anti_patterns", []))
                all_required_states.extend(primary_pack_meta.get("required_states", []))

                # Add recommended runtime validation if applicable and not already present
                rec_runtime = primary_pack_meta.get("recommended_runtime_validation", [])
                for rt_id in rec_runtime:
                    if rt_id in RUNTIME_VALIDATION_PACKS and not any(r["id"] == rt_id for r in selected_runtime_packs):
                        rt_cand = dict(RUNTIME_VALIDATION_PACKS[rt_id])
                        rt_cand["reason"] = f"Recommended by domain pack '{primary_domain_name}'."
                        selected_runtime_packs.append(rt_cand)

                # Rationale according to Precedence Hierarchy (Rule 19)
                if workflow == "existing-ui":
                    rationale.append(
                        f"Domain knowledge '{primary_domain_name}' applied at Level 6 (best practice); "
                        "cannot override existing brand palette, typography, or design tokens."
                    )
                else:
                    rationale.append(
                        f"Greenfield domain intelligence applied for '{primary_domain_name}' without violating explicit user constraints."
                    )

            # Secondary Domain (if detected with high confidence e.g. Beauty Ecommerce)
            if secondary_domain_names:
                sec_domain_name = secondary_domain_names[0]
                sec_pack_meta = get_domain_pack(sec_domain_name)
                if sec_pack_meta:
                    sec_subtopics = query_domain_subtopics(sec_domain_name, user_request, task_intent)
                    all_domain_subtopics.extend(sec_subtopics)

                    sec_entry = {
                        "id": sec_pack_meta["id"],
                        "category": "domain",
                        "name": sec_pack_meta["name"],
                        "reason": f"Secondary domain intelligence for {sec_pack_meta['name']}.",
                        "priority": "medium",
                        "source": sec_pack_meta["source"],
                        "required": False,
                        "weight": "small",
                        "version": sec_pack_meta.get("version", "1.0.0"),
                    }
                    selected_domain_packs.append(sec_entry)
                    domain_context_secondary = {
                        "id": sec_pack_meta["id"],
                        "domain": sec_domain_name,
                        "confidence": 0.50,
                        "evidence": [f"Secondary domain evidence for {sec_domain_name}."],
                        "selected_subtopics": sec_subtopics,
                    }
                    all_anti_patterns.extend(sec_pack_meta.get("anti_patterns", []))

        # Build Domain Context block adhering to knowledge-plan.schema.json
        domain_context = {
            "primary": domain_context_primary,
            "secondary": domain_context_secondary,
            "selected_subtopics": list(dict.fromkeys(all_domain_subtopics)),
            "applied_patterns": list(dict.fromkeys(all_applied_patterns)),
            "anti_patterns": list(dict.fromkeys(all_anti_patterns)),
            "required_states": list(dict.fromkeys(all_required_states)),
            "source": domain_source,
        }

        # Domain Subtopics -> Actual Knowledge Mapping (P1.4, Hardening #4)
        for subtopic in domain_context["selected_subtopics"]:
            sub_lower = subtopic.lower()
            if any(k in sub_lower for k in ("booking", "room", "date", "guest", "cancellation", "property", "hotel", "travel")):
                _add_catalog_knowledge("recipe.travel-booking", f"Travel booking architecture recipe for domain subtopic '{subtopic}'.", priority="high")
                _add_catalog_knowledge("screen.search", f"Destination and room search pattern for domain subtopic '{subtopic}'.", priority="high")
                _add_catalog_knowledge("screen.checkout", f"Reservation checkout and pricing pattern for domain subtopic '{subtopic}'.", priority="high")
                _add_catalog_knowledge("component.form-controls", f"Date and room selection form controls for domain subtopic '{subtopic}'.", priority="medium")
            if "dashboard" in sub_lower and primary_domain_name != "hospitality_travel":
                _add_catalog_knowledge("recipe.enterprise-dashboard", f"Enterprise dashboard architecture recipe for domain subtopic '{subtopic}'.", priority="high")
                _add_catalog_knowledge("screen.dashboard", f"Dashboard screen layout pattern for domain subtopic '{subtopic}'.", priority="high")
            if ("pricing" in sub_lower or "billing" in sub_lower or "public_surfaces" in sub_lower or "settings_billing" in sub_lower) and primary_domain_name != "hospitality_travel":
                _add_catalog_knowledge("screen.pricing", f"Pricing matrix screen pattern for domain subtopic '{subtopic}'.", priority="high")
            if "checkout" in sub_lower or "cart" in sub_lower:
                if primary_domain_name != "hospitality_travel":
                    _add_catalog_knowledge("recipe.consumer-app", f"Consumer checkout UX flow recipe for domain subtopic '{subtopic}'.", priority="high")
                _add_catalog_knowledge("screen.checkout", f"Checkout screen pattern for domain subtopic '{subtopic}'.", priority="high")
            if "terminal" in sub_lower or "cli" in sub_lower:
                _add_catalog_knowledge("style.developer-tool", f"Developer terminal styling recipe for domain subtopic '{subtopic}'.", priority="medium")
            if "analytics" in sub_lower or "metrics" in sub_lower:
                _add_catalog_knowledge("screen.analytics", f"Analytics and telemetry screen pattern for domain subtopic '{subtopic}'.", priority="medium")
            if "workspace" in sub_lower or "collaboration" in sub_lower:
                _add_catalog_knowledge("screen.workspace", f"Workspace collaboration screen pattern for domain subtopic '{subtopic}'.", priority="medium")

        # 9. Assemble All Candidates for Context Budgeting
        all_candidates: list[dict[str, Any]] = []
        all_candidates.extend(selected_framework_packs)
        all_candidates.extend(selected_styling_packs)
        all_candidates.extend(selected_ui_library_packs)
        all_candidates.extend(selected_domain_packs)
        all_candidates.extend(candidate_knowledge)
        all_candidates.extend(candidate_skills)
        all_candidates.extend(selected_runtime_packs)

        # Deduplicate candidates by ID while preserving order
        unique_candidates: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for cand in all_candidates:
            if cand["id"] not in seen_ids:
                seen_ids.add(cand["id"])
                unique_candidates.append(cand)

        # Apply Context Budgeting & Deterministic Pruning
        budgeted_items, excluded_items, budget_info = self.budget_manager.apply_budget(unique_candidates)

        # Re-partition into category buckets
        final_fw: list[dict[str, Any]] = []
        final_styling: list[dict[str, Any]] = []
        final_ui_lib: list[dict[str, Any]] = []
        final_domain: list[dict[str, Any]] = []
        final_skills: list[dict[str, Any]] = []
        final_knowledge: list[dict[str, Any]] = []
        final_runtime: list[dict[str, Any]] = []

        for it in budgeted_items:
            cat = it.get("category")
            if cat == "framework":
                final_fw.append(it)
            elif cat == "styling":
                final_styling.append(it)
            elif cat == "ui_library":
                final_ui_lib.append(it)
            elif cat == "domain":
                final_domain.append(it)
            elif cat == "skill":
                final_skills.append(it)
            elif cat == "runtime":
                final_runtime.append(it)
            else:
                final_knowledge.append(it)

        # Build Deterministic Load Order
        # 1. Hard constraints / preservation
        # 2. Framework pack
        # 3. Styling / UI Library packs
        # 4. Domain packs
        # 5. Skills
        # 6. Catalog Knowledge
        # 7. Runtime validation
        load_order: list[str] = []
        for it in final_knowledge:
            if it.get("category") == "preservation":
                load_order.append(it["id"])
        for it in final_fw:
            load_order.append(it["id"])
        for it in final_styling:
            load_order.append(it["id"])
        for it in final_ui_lib:
            load_order.append(it["id"])
        for it in final_domain:
            load_order.append(it["id"])
        for it in final_skills:
            load_order.append(it["id"])
        for it in final_knowledge:
            if it.get("category") != "preservation" and it["id"] not in load_order:
                load_order.append(it["id"])
        for it in final_runtime:
            load_order.append(it["id"])

        return {
            "schema_version": 1,
            "workflow": workflow,
            "requested_scope": requested_scope,
            "task_intent": task_intent,
            "secondary_intents": secondary_intents,
            "compound": intent_info.get("compound", False),
            "selected_packs": {
                "framework": final_fw,
                "styling": final_styling,
                "ui_library": final_ui_lib,
                "domain": final_domain,
                "runtime": final_runtime,
            },
            "selected_skills": final_skills,
            "selected_knowledge": final_knowledge,
            "preservation_context": preservation_context,
            "domain_context": domain_context,
            "excluded_knowledge": excluded_items,
            "load_order": load_order,
            "context_budget": budget_info,
            "rationale": rationale,
            "diagnostics": diagnostics,
        }
