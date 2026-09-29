```yaml
id: domain.ecommerce
name: E-Commerce UI Engineering Pack
kind: domain
category: domain
applies_to:
  task_types: [checkout_improvement, product_listing, cart_ux]
when: "Project involves selling physical or digital goods, managing carts, catalogs, and checkouts."
avoid_when: "Do not apply e-commerce constraints to internal admin dashboards or SaaS settings."
goal: "Maximize conversion rate, build trust, and remove friction from the purchase flow."
principles:
  - "Trust is paramount (show secure badges, transparent pricing, clear return policies)."
  - "Frictionless checkout (minimize required fields, allow guest checkout)."
  - "Visual hierarchy focuses on Product Imagery and the Add to Cart CTA."
anatomy:
  - "Product Listing Page (PLP): Sidebar filters, sorting, product grid."
  - "Product Detail Page (PDP): Hero image gallery, variant selectors, sticky add-to-cart."
  - "Cart: Drawer or dedicated page, itemized breakdown, upsells."
  - "Checkout: Multi-step or accordion, localized payment methods, order summary."
variants:
  - "Luxury E-commerce: High whitespace, editorial imagery, minimal borders."
  - "Value E-commerce: Dense grids, high contrast discount badges, urgency indicators."
responsive:
  - "Mobile PLP: Sidebar filters MUST collapse into a bottom sheet or full-screen drawer."
  - "Mobile PDP: Add to Cart button MUST stick to the bottom of the viewport so it's always accessible."
accessibility:
  - "Variant selectors (color swatches, sizes) must use native radio buttons visually hidden, with proper aria-labels (e.g., Color: Red, Out of Stock)."
implementation:
  - "React/Next.js: Use optimistic UI updates when changing cart quantities."
anti_patterns:
  - "Hiding shipping costs until the final payment step (leading cause of cart abandonment)."
  - "Using dropdowns (<select>) for variants with < 5 options (use exposed radio chips instead)."
  - "Requiring account creation before checkout."
```

# E-Commerce UI Engineering Pack

E-commerce UI engineering is distinct because direct revenue depends on its usability. The primary engineering goals are reducing latency (optimistic UI), establishing trust (error handling, transparency), and ensuring cross-device ergonomics (thumb-friendly CTAs).

## Core UX Flows

### 1. Product Detail Page (PDP)
The PDP must convince the user and make selection effortless.
- **Variant Selection**: Always show available sizes/colors explicitly. If a size is out of stock, cross it out visually but keep it focusable with an `aria-label="Size M, Out of stock"`.
- **Sticky CTA**: On mobile, the "Add to Cart" button should become sticky at the bottom of the screen once the user scrolls past the initial button placement.

### 2. Cart & Checkout
- **Cart Drawer**: Prefer a slide-out cart drawer over redirecting to a cart page. It keeps the user in the shopping context.
- **Checkout Accordion**: Break checkout into logical chunks (Shipping, Payment, Review) rather than one massive form.
- **Form UX**: Use `autocomplete` attributes extensively (`shipping address-line1`, `cc-name`, `cc-number`).
