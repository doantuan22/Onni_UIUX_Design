# Interaction and motion

Each interactive component supports its relevant default, hover, focus, active, loading, disabled, success, and error states. Use visible focus, predictable feedback, and interactions that preserve locked flows. Forms require a label, input, helper context when needed, required indication, focus, nearby error, success, and disabled handling; a placeholder never replaces a label.

Use modals for short, bounded work; use drawers for filters, secondary detail, or contextual configuration; do not put long or consequential workflows into either by default. Motion communicates change, hierarchy, or feedback and uses duration tokens. Respect `prefers-reduced-motion` whenever motion is present.

Durations, easing, spatial direction and reduced-motion equivalents follow the [Motion Engine](../../knowledge/motion/README.md) (see [spatial-motion](../../knowledge/motion/spatial-motion.md) and [microinteractions](../../knowledge/motion/microinteractions.md)).

Interaction patterns (drag, reorder, inline editing, optimistic update, undo, command palette, gestures) are catalogued in [knowledge/interactions](../../knowledge/domains/interactions/README.md) with input → feedback → state → motion → result models.
