```yaml
id: component.button
name: Button Component Engineering Guide
kind: component
category: foundation
applies_to:
  ui_states: [default, hover, focus, active, disabled, loading]
when: "Use buttons to trigger actions or events (e.g., submitting a form, opening a dialog)."
avoid_when: "Do not use buttons for navigation between pages; use links (a tags) instead."
responsive: "Mobile: Minimum touch target 48x48px. Span full width in mobile forms. Desktop: Hug content, inline-flex."
accessibility: "Must have type=button or type=submit. Requires aria-disabled=true instead of disabled if you want to allow focus to explain why it is disabled. Focus-visible outline is mandatory."
implementation: "React/Tailwind: Use forwardRef to pass refs. Manage isLoading state to render spinner and prevent double clicks."
anti_patterns:
  - "Two primary buttons side-by-side."
  - "Relying solely on color to indicate destructive state (e.g., red without clear label)."
  - "Removing focus outline for aesthetic reasons."
```

# Button Engineering Guide

The button is the most critical interaction primitive. It must clearly communicate its action, state, and priority.

## Anatomy
- **Label**: Clear, action-oriented verb (e.g., "Save changes", not "Submit").
- **Leading/Trailing Icon**: Optional, supports the label.
- **Container**: Defines the hit area and variant style.

## Variants & Selection Rules
| Variant | Visual Rule | Selection Rule (WHEN to use) |
|---------|-------------|------------------------------|
| **Primary** | High contrast (solid background). | The single most important action on the screen/form. |
| **Secondary**| Outline or subtle fill. | Alternate actions, cancel buttons, secondary filters. |
| **Ghost** | Transparent background, visible on hover. | Low emphasis actions (e.g., table row actions). |
| **Destructive**| Red/Warning colors. | Irreversible actions (Delete, Remove). Must include confirmation step. |

## Required States
Every button must explicitly style these states:
- **Default**: Baseline contrast.
- **Hover**: Cursor change, slight background/brightness shift.
- **Focus-visible**: 2px offset outline. NEVER remove this.
- **Active (Pressed)**: Slight scale down (e.g., `scale-95`) or inner shadow.
- **Disabled**: Reduced opacity (e.g., `opacity-50`), `cursor-not-allowed`.
- **Loading**: Maintain dimensions, hide label visually or show spinner alongside label. Disable pointer events.

## Responsive Transformation
- **Desktop**: Buttons inline with content, hug text.
- **Mobile (< 768px)**: Forms and modals should often use full-width (`w-full`) buttons to maximize touch target and ergonomics. Always ensure `min-h-[48px]` for touch targets.

## Implementation Details (React + Tailwind)
```tsx
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)
```
