# Reference index

```yaml
references:
  phase_1_forms:
    file: skills/ux-structure/references/forms.md
    phase: 1
    triggers: [form, registration, input, validation]
    excludes: [dashboard-only, audit-without-form]
  phase_1_tables:
    file: skills/ux-structure/references/tables.md
    phase: 1
    triggers: [data-table, admin-list, sorting, bulk-action]
    excludes: [single-form, marketing-page]
  phase_1_dashboard:
    file: skills/ux-structure/references/dashboard.md
    phase: 1
    triggers: [dashboard, monitoring, status-overview]
    excludes: [single-registration, checkout-only]
  phase_1_navigation:
    file: skills/ux-structure/references/navigation.md
    phase: 1
    triggers: [multi-page, role-navigation, return-path]
    excludes: [isolated-static-page]
  phase_1_checkout:
    file: skills/ux-structure/references/checkout.md
    phase: 1
    triggers: [booking, payment, purchase, confirmation]
    excludes: [dashboard, registration-only]
  phase_2_system:
    file: skills/design-system/workflow.md
    phase: 2
    triggers: [new-build, visual-redesign, token-inconsistency]
    excludes: [targeted-polish-with-stable-system]
  phase_2_forms:
    file: knowledge/references/forms.md
    phase: 2
    triggers: [form, registration, input-state]
    excludes: [table-only, dashboard-only]
  phase_2_tables:
    file: knowledge/references/tables.md
    phase: 2
    triggers: [data-table, responsive-table, row-action]
    excludes: [single-form, marketing-page]
  phase_2_dashboard:
    file: knowledge/references/dashboard.md
    phase: 2
    triggers: [dashboard, operational-overview, monitoring]
    excludes: [registration-only, checkout-only]
  phase_2_accessibility:
    file: skills/final-quality-gate/accessibility.md
    phase: 2
    triggers: [interactive-control, final-quality, accessibility-issue]
    excludes: []
  phase_2_visual_language:
    file: knowledge/visual-language/visual-grammar.md
    phase: 2
    triggers: [rendered-ui, visual-redesign, visual-consistency, component-personality]
    excludes: [structure-only, api-only]
  phase_2_button_grammar:
    file: knowledge/visual-language/components/buttons.md
    phase: 2
    triggers: [button, cta, action-hierarchy, icon-button]
    excludes: [text-only, table-only]
  phase_2_feedback_grammar:
    file: knowledge/visual-language/components/feedback.md
    phase: 2
    triggers: [toast, notification, alert, banner, validation, empty-state, error-state]
    excludes: [static-content-only]
  phase_2_icon_grammar:
    file: knowledge/visual-language/components/iconography.md
    phase: 2
    triggers: [icon, icon-button, status-symbol, navigation-icon]
    excludes: [text-only]
  phase_2_craft_review:
    file: skills/visual-language/craft-review.md
    phase: 2
    triggers: [generic-ui, ai-slop, visual-polish, craft-review, rendered-redesign]
    excludes: [structure-only, backend-only]
  phase_2_full_visual_redesign:
    file: skills/visual-language/adversarial-review.md
    phase: 2
    triggers: [full-redesign, visual-system-replacement, ai-tell-density-high]
    excludes: [targeted-single-component]
  phase_2_design_inspiration:
    file: skills/design-inspiration/workflow.md
    phase: 2
    triggers: [landing-page, marketing, product-showcase, launch, make-it-premium, visual-redesign, looks-generic, marketplace-home, editorial]
    excludes: [dashboard-only, small-form, single-component-polish]
  phase_2_reference_extraction:
    file: skills/design-inspiration/reference-extraction.md
    phase: 2
    triggers: [screenshot, reference-url, reference-site-name, like-brand-x]
    excludes: [no-reference]
  phase_2_anti_copying:
    file: skills/design-inspiration/anti-copying.md
    phase: 2
    triggers: [any-reference, clone-request]
    excludes: [no-reference]
  phase_2_typography_intelligence:
    file: skills/typography/README.md
    phase: 2
    triggers: [font, typography, type-hierarchy, readability, new-build, make-it-premium, vietnamese-content]
    excludes: [motion-only, structure-only]
  phase_2_motion_engine:
    file: knowledge/motion/README.md
    phase: 2
    triggers: [animation, motion, transition, interaction, scroll-effect, reduced-motion]
    excludes: [static-content-only, structure-only]
  phase_2_scroll_motion:
    file: knowledge/motion/scroll-motion.md
    phase: 2
    triggers: [scroll-storytelling, parallax, sticky-section, landing-page-motion, scroll-effect]
    excludes: [dashboard, form, app-screen]
  phase_2_web_patterns:
    file: knowledge/web-patterns/README.md
    phase: 2
    triggers: [landing-page, marketing, product-showcase, editorial, marketplace-home, generic-template-composition]
    excludes: [dashboard-only, small-form, single-component]
  phase_2_pattern_selection:
    file: skills/design-inspiration/pattern-selection.md
    phase: 2
    triggers: [landing-page, marketing, product-showcase, section-composition, hero, storytelling, generic-template-composition]
    excludes: [dashboard-only, small-form]
  phase_2_capability_resolver:
    file: skills/capability-resolver/README.md
    phase: 2
    triggers: [new-build, visual-redesign, landing-page, product-site, make-it-premium, looks-generic, benchmark]
    excludes: [small-form, single-component-polish, audit-only]
  phase_2_design_knowledge:
    file: knowledge/domains/retrieval.md
    phase: 2
    triggers: [capability-plan-retrieval, style-selection, screen-pattern, effect, interaction-pattern]
    excludes: [structure-only]
  phase_2_style_catalog:
    file: knowledge/domains/styles/README.md
    phase: 2
    triggers: [style-selection, visual-language-choice, homogenized-design]
    excludes: [small-form, targeted-polish-with-stable-system]
  phase_2_screen_library:
    file: knowledge/domains/screens/README.md
    phase: 2
    triggers: [dashboard, settings, onboarding, authentication, ai-chat, ai-copilot, kanban, calendar, editor, file-browser]
    excludes: [marketing-only]
  phase_2_interaction_library:
    file: knowledge/domains/interactions/README.md
    phase: 2
    triggers: [drag, reorder, inline-edit, command-palette, gesture, undo, optimistic-update, keyboard-navigation]
    excludes: [static-content-only]
  phase_2_effect_library:
    file: knowledge/domains/effects/README.md
    phase: 2
    triggers: [glass, glow, gradient, noise, blur, shader, lighting, visual-effect]
    excludes: [dashboard-only, small-form]
  phase_2_composition:
    file: knowledge/domains/composition/README.md
    phase: 2
    triggers: [composition, recipe, premium, anti-homogenization]
    excludes: [single-component]
  phase_2_cinematic_motion:
    file: knowledge/motion/cinematic-motion.md
    phase: 2
    triggers: [webgl, three-js, 3d, cinematic-hero, particles, shader-motion]
    excludes: [dashboard, form, app-screen]
  phase_2_technology_resolver:
    file: skills/frontend-implementation/technology-resolver.md
    phase: 2
    triggers: [animation-library, gsap, framer-motion, rive, lottie, webgl, canvas, view-transitions, new-dependency]
    excludes: []
  phase_2_performance_budget:
    file: skills/frontend-implementation/performance-budget.md
    phase: 2
    triggers: [visual-effect, continuous-animation, scroll-effect, webgl, backdrop-filter]
    excludes: [static-content-only]
  phase_2_ambition_levels:
    file: workflows/ambition-levels.md
    phase: 2
    triggers: [modernize, upgrade, elevate, polish, premium, redesign, visual-upgrade, less-generic]
    excludes: [single-component, accessibility-only, structure-only]
  phase_2_signature_moves:
    file: skills/design-direction/signature-moves.md
    phase: 2
    triggers: [elevate, reimagine, visual-redesign, distinctive, anti-homogenization, premium]
    excludes: [targeted-polish-with-stable-system, structure-only]
  phase_2_default_banlist:
    file: knowledge/visual-language/anti-slop/default-banlist.md
    phase: 2
    triggers: [elevate, generic-ui, ai-look, anti-slop, premium-review, visual-redesign]
    excludes: [structure-only]
  phase_2_code_recipes:
    file: knowledge/code-recipes/README.md
    phase: 2
    triggers: [elevate, reimagine, react, nextjs, tailwind, hero, bento, pricing, faq, motion, framer-motion, gsap]
    excludes: [structure-only, accessibility-only]
  phase_2_design_quality_evals:
    file: evals/quality/README.md
    phase: 2
    triggers: [design-quality, motion-quality, benchmark, premium-review]
    excludes: [structure-only]
```

This is an index, not an exhaustive catalog. Add entries only when routers need a new deterministic selection rule.
