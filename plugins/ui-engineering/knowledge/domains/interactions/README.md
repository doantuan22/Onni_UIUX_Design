# Interaction Intelligence

An **interaction** is how user input produces a result. Every pattern is modelled as:

```text
Input → Immediate Feedback → State Transition → Motion → Result
```

Feedback must arrive within ~100ms of input, even if the result takes longer (show pending state, then the result). Motion is the *carrier* of the transition and is chosen from the [motion catalog](../../motion/motion-vocabulary.md). Visual appearance comes from [effects](../effects/README.md) and component grammar.

| File | Patterns |
|---|---|
| [pointer.md](pointer.md) | hover intent, press feedback, magnetic, cursor follow, hover preview, smart tooltip, context menu |
| [direct-manipulation.md](direct-manipulation.md) | drag, drag resistance, spring snap, reorder, resize, drop zone, swipe action, long press, pull interaction |
| [productivity.md](productivity.md) | multi-select, inline editing, optimistic update, undo, command palette, keyboard navigation, selection toolbar, shortcut discovery, focus management, progressive disclosure |

## Universal rules

1. **Every pointer interaction has a keyboard path, and every hover has a non-hover path.** Gestures (drag, swipe, long press) always have a visible alternative control.
2. **Discoverability.** A hidden interaction (gesture, shortcut, hover-only) needs a visible cue or an alternative. See the E79 Interaction Discoverability eval.
3. **Budget.** Interactions with continuous pointer tracking (magnetic, cursor follow, spotlight) count toward the [interaction budget](../../../skills/frontend-implementation/performance-budget.md#interaction-budget).
4. **Errors are part of the pattern.** Each entry defines what happens when the action fails or is invalid.
5. `min_interaction_intensity` (1–5) is the lowest interaction intensity at which the resolver proposes the pattern. Core patterns (press feedback, focus management, keyboard navigation) are 1.

Schema: [schema.md](../schema.md#interaction).
