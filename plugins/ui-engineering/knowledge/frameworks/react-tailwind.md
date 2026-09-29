```yaml
id: framework.react-tailwind
name: React + Tailwind CSS Engineering Pack
kind: framework
category: framework
applies_to:
  frameworks: [react, nextjs]
  styling: [tailwindcss]
when: "Repository uses React (or Next.js/Vite) paired with Tailwind CSS."
avoid_when: "Do not apply to vanilla HTML/CSS, Vue, or projects using CSS modules heavily."
goal: "Establish consistent component architecture, utility class discipline, and state-driven styling."
principles:
  - "Componentize repeating utility strings."
  - "Rely on cva (class-variance-authority) and clsx/tailwind-merge for variant management."
  - "Never fight the framework: use React state for interactivity, Tailwind for visual presentation."
implementation: "Always merge classes dynamically to avoid conflicts: cn('base classes', props.className)."
anti_patterns:
  - "Using string interpolation for class names (e.g., bg-red-500) which breaks Tailwind PurgeCSS/JIT."
  - "Massive 50+ class strings directly in JSX without breaking them into semantic variables or variants."
  - "Writing custom CSS in .css files when a utility class exists."
```

# React + Tailwind Implementation Guide

## 1. Dynamic Class Merging
Always use a utility like `cn` (combining `clsx` and `tailwind-merge`) when exposing a `className` prop on a custom React component. This ensures that overrides work as expected.

```tsx
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

## 2. Variant Management
When a component has distinct visual states (e.g., sizes, colors, intent), use `class-variance-authority` (cva) instead of complex ternaries.

```tsx
const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        secondary: "bg-secondary text-secondary-foreground",
        destructive: "bg-destructive text-destructive-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)
```
