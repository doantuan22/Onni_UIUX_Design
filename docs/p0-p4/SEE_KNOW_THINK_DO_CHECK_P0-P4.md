# ROADMAP TÁI CẤU TRÚC PLUGIN UI/UX THEO TRIẾT LÝ SEE → KNOW → THINK → DO → CHECK

## 0. Mục tiêu chung

Plugin không chỉ đóng vai trò là một bộ **rule/constraint** kiểm soát AI coding, mà phải trở thành một **UI Engineering Intelligence Layer** giúp AI:

1. **SEE** — hiểu chính xác repository, cấu trúc frontend và UI/UX hiện tại.
2. **KNOW** — có đủ tri thức thiết kế và hướng dẫn implementation để không phải tự suy diễn mọi thứ từ đầu.
3. **THINK** — reasoning dựa trên yêu cầu người dùng + UI context + knowledge + constraints để quyết định nên thay đổi gì.
4. **DO** — thực thi code có kiểm soát, đúng framework, đúng phạm vi và hạn chế blast radius.
5. **CHECK** — kiểm chứng bằng runtime evidence, visual analysis, regression, accessibility và repair loop.

Nguyên tắc kiến trúc mới:

> **AI không được thiết kế khi chưa hiểu. AI không được tự do suy diễn khi plugin đã có knowledge phù hợp. AI không được sửa trực tiếp khi chưa có design decision và modification plan. AI không được kết thúc task khi chưa có evidence kiểm chứng.**

---

# P0 — SEE: UI PERCEPTION & CONTEXT INTELLIGENCE

## 1. Vai trò

P0 là tầng giúp AI **nhìn thấy và hiểu hệ thống hiện tại trước khi thiết kế hoặc chỉnh sửa giao diện**.

Đây là tầng ưu tiên cao nhất vì nếu AI hiểu sai repository, framework, layout, component, màu sắc, design system hoặc UX flow thì toàn bộ các bước phía sau đều có thể sai.

P0 phải giải quyết bài toán:

> **“Hệ thống hiện tại đang là gì?”**

Không chỉ dừng ở việc đọc source code, P0 phải kết hợp:

- Repository analysis.
- Static frontend analysis.
- Runtime analysis.
- Visual analysis.
- Design-system extraction.
- UX-flow extraction.
- Dependency và blast-radius analysis.

---

## 2. Mục đích

- Loại bỏ tình trạng AI sửa UI trong trạng thái “làm mù”.
- Giúp AI hiểu đúng technology stack trước khi chọn cách implementation.
- Hiểu cấu trúc UI hiện tại trước khi quyết định giữ, chỉnh hay tái cấu trúc.
- Nhận diện visual identity hiện tại để tránh tự ý recolor hoặc redesign.
- Xây được machine-readable context cho các tầng KNOW, THINK, DO và CHECK.
- Tạo cơ sở cho Existing UI Preservation.
- Tạo cơ sở cho framework-aware và context-aware design.

---

## 3. Những việc phải làm

### 3.1. Repository Analyzer

Phát triển tool có khả năng tự động nhận diện:

- Framework:
  - React.
  - Next.js.
  - Vue.
  - Nuxt.
  - Svelte.
  - SvelteKit.
  - Angular.
  - Static HTML/CSS/JS.
  - Spring Boot + Thymeleaf.
  - Các stack khác có thể mở rộng sau.
- Framework version.
- Router.
- Build tool.
- Template engine.
- Styling system:
  - CSS.
  - CSS Modules.
  - Sass/SCSS.
  - Tailwind.
  - Bootstrap.
  - styled-components.
  - Emotion.
  - custom CSS system.
- UI library:
  - shadcn/ui.
  - MUI.
  - Bootstrap Components.
  - Ant Design.
  - Chakra UI.
  - internal component library.
- Icon library.
- Motion/animation library.
- State-management library.
- Existing test/runtime commands.
- Package manager.
- Main entrypoints.
- Asset locations.
- Theme/token files.

### 3.2. Route & Page Detector

Tạo inventory đầy đủ của:

- Routes.
- Pages.
- Nested routes.
- Layouts.
- Shared layouts.
- Templates.
- Protected/authenticated pages.
- Dynamic routes.
- Error pages.
- Loading pages.
- Empty states.

Output phải cho AI biết:

```text
Route → Page → Layout → Components
```

### 3.3. Component Graph Analyzer

Phân tích:

- Shared components.
- Local components.
- Component hierarchy.
- Component usage.
- Component duplication.
- Variant usage.
- Props liên quan UI.
- Component nào ảnh hưởng nhiều page.

Tạo **Component Dependency Graph**.

Ví dụ:

```text
ProductCard
├── Home
├── Search
├── Product Listing
└── Related Products
```

Plugin phải tính được mức độ ảnh hưởng:

```text
blast_radius:
  low | medium | high
```

### 3.4. Layout Structure Analyzer

Nhận diện:

- Global shell.
- Header.
- Navbar.
- Sidebar.
- Main content.
- Footer.
- Containers.
- Grid.
- Flex layout.
- Section structure.
- Card layout.
- Dashboard layout.
- Multi-column layout.
- Sticky elements.
- Fixed elements.
- Scroll regions.

Phải xây được **Layout Graph** thay vì chỉ trả về DOM hoặc filename.

### 3.5. Design Token Detector

Trích xuất:

- Primary colors.
- Secondary colors.
- Accent colors.
- Neutral palette.
- Background.
- Surface.
- Text colors.
- Border colors.
- Semantic colors.
- Typography family.
- Typography scale.
- Font weight.
- Line height.
- Spacing system.
- Radius.
- Shadows.
- Breakpoints.
- Container widths.
- Z-index conventions.

Nguồn token có thể đến từ:

- CSS variables.
- Tailwind config/theme.
- SCSS variables.
- theme provider.
- MUI theme.
- design-token files.
- computed runtime styles.

### 3.6. Runtime UI Analyzer

Tận dụng Playwright/runtime hiện có để phân tích UI đang render thật.

Thu thập:

- DOM tree cần thiết.
- Computed styles.
- Bounding boxes.
- Visible text.
- Interactive elements.
- Scrollable regions.
- Overflow.
- Hidden elements.
- Focusable elements.
- Accessibility tree.
- Actual viewport behavior.
- Responsive transformations.
- Navigation behavior.
- Modal/drawer behavior.
- Forms và validation states.

Runtime analyzer phải chạy trên nhiều viewport:

- Desktop.
- Tablet.
- Mobile.

### 3.7. Visual UI Analyzer

Phân tích screenshot/runtime evidence để suy ra:

- Visual hierarchy.
- Content hierarchy.
- Alignment.
- Whitespace.
- Density.
- Surface hierarchy.
- Color dominance.
- Typographic hierarchy.
- CTA prominence.
- Image prominence.
- Section rhythm.
- Balance.
- Consistency.
- Visual grouping.
- Repetition.
- Contrast.
- Brand feeling.
- Motion intensity nếu có.

Kết quả phải có confidence score thay vì giả định mọi nhận định đều chắc chắn.

### 3.8. UX Flow Analyzer

Phát hiện hoặc xây dựng flow từ route/page/component:

Ví dụ:

```text
Search
→ Result
→ Detail
→ Select
→ Checkout
→ Payment
→ Result
```

Cần nhận diện:

- Entry point.
- Main action.
- Next step.
- Back path.
- Error state.
- Empty state.
- Confirmation state.
- Drop-off point.
- Missing state.
- Inconsistent flow.

### 3.9. Existing UI State Classifier

Phân loại repo thành:

```text
GREENFIELD
PARTIAL_UI
MATURE_EXISTING_UI
```

Mục đích là giúp Workflow Router chọn quyền thiết kế phù hợp.

### 3.10. UI Context Model

Tất cả tool ở P0 phải hợp nhất về một output chuẩn:

```yaml
ui_context:
  repo: {}
  framework: {}
  architecture: {}
  routes: []
  pages: []
  components: []
  design_system: {}
  visual_language: {}
  ux_flows: {}
  responsive: {}
  accessibility: {}
  runtime: {}
  issues: []
  protected_properties: {}
  confidence: {}
```

Không để từng tool sinh report rời rạc mà không có canonical context.

### 3.11. Understanding Gate

Tạo hard gate:

> **NO DESIGN WITHOUT UNDERSTANDING**

AI không được đi sang THINK/DO với Existing UI nếu chưa biết tối thiểu:

- Framework.
- Styling system.
- Affected pages.
- Relevant components.
- Current palette.
- Current layout.
- Shared components.
- Responsive behavior cơ bản.
- Navigation/UX flow liên quan.
- Protected properties.
- Runtime capability.

Nếu thiếu:

```text
UNDERSTANDING_INCOMPLETE
```

Plugin phải thu thêm evidence trước khi tiếp tục.

---

## 4. Mục tiêu phải đạt

P0 hoàn thành khi AI có thể trả lời một cách machine-readable và có evidence:

- Repo đang dùng công nghệ gì?
- Frontend nằm ở đâu?
- UI hiện có hay chưa?
- Trang nào liên quan task?
- Layout hiện tại như thế nào?
- Component nào được tái sử dụng?
- Màu sắc hiện tại là gì?
- Typography và spacing hiện tại ra sao?
- UI render thực tế như thế nào?
- Mobile khác desktop như thế nào?
- UX flow hiện tại là gì?
- Những property nào phải được bảo vệ?
- Sửa component này sẽ ảnh hưởng những đâu?

---

## 5. Output bắt buộc

- `repo_profile.json`
- `page_inventory.json`
- `component_graph.json`
- `layout_graph.json`
- `design_tokens.json`
- `ux_flow_map.json`
- `runtime_ui_profile.json`
- `visual_ui_profile.json`
- `ui_context.json`
- `understanding_gate_report.json`

---

## 6. Definition of Done

- Framework detection đúng trên benchmark repo.
- Styling system detection đủ tin cậy.
- Route/page inventory không bỏ sót các page chính.
- Shared component mapping hoạt động.
- Có runtime evidence ít nhất cho các page bị ảnh hưởng.
- Extract được palette và visual identity cơ bản.
- Responsive behavior được quan sát, không chỉ suy đoán từ source.
- UI Context Model được sử dụng trực tiếp bởi P2 và P3.
- Existing UI task không được bypass Understanding Gate.

---

# P1 — KNOW: UI ENGINEERING KNOWLEDGE SYSTEM

## 1. Vai trò

P1 là tầng cung cấp **tri thức thiết kế và hướng dẫn implementation thực tế** cho AI coding.

P1 giải quyết bài toán:

> **“Một UI tốt nên được thiết kế và triển khai như thế nào?”**

Plugin không thể chỉ nói cho AI cái gì không được làm. Nó phải cung cấp cho AI:

- Design principles.
- Pattern selection.
- Component anatomy.
- Layout guidance.
- UX guidance.
- Framework-specific implementation guidance.
- Code recipes.

---

## 2. Mục đích

- Giảm việc AI tự suy diễn thiết kế từ đầu.
- Biến plugin thành một hệ tri thức UI Engineering.
- Đưa ra hướng dẫn cụ thể thay vì chỉ rule/constraint.
- Giúp kết quả giữa các AI coding agent nhất quán hơn.
- Cho phép Knowledge Router chỉ nạp đúng kiến thức cần thiết.
- Tăng chất lượng implementation cho từng framework.
- Tạo nền cho Design Reasoning ở P2.

---

## 3. Những việc phải làm

### 3.1. Design Foundation Pack

Xây tri thức cho:

- Color usage.
- Typography.
- Type scale.
- Line length.
- Spacing.
- Density.
- Radius.
- Border.
- Shadow.
- Surface.
- Contrast.
- Hierarchy.
- Visual emphasis.
- Content width.
- Container.
- Icon usage.

Mỗi tài liệu phải giải thích:

```text
WHEN
WHY
HOW
OPTIONS
ANTI-PATTERNS
IMPLEMENTATION NOTES
VALIDATION
```

### 3.2. Layout Engineering Pack

Bổ sung hướng dẫn chi tiết cho:

- Centered layout.
- Split layout.
- Editorial layout.
- Bento.
- Dashboard.
- Sidebar.
- Master-detail.
- Grid.
- Masonry khi phù hợp.
- Data-dense layout.
- Full-width marketing layout.
- Sticky summary.
- Responsive collapse.

Mỗi pattern phải có selection rules.

### 3.3. Component Engineering Pack

Xây knowledge theo component:

- Button.
- Input.
- Select.
- Checkbox.
- Radio.
- Date picker.
- Card.
- Product card.
- Navbar.
- Sidebar.
- Breadcrumb.
- Tabs.
- Modal.
- Drawer.
- Toast.
- Tooltip.
- Table.
- Data grid.
- Filter.
- Search.
- Pagination.
- Pricing card.
- Hero.
- Feature section.
- Testimonial.
- FAQ.
- Empty state.
- Error state.
- Loading/skeleton.
- Stepper.

Mỗi component phải có:

- Purpose.
- Anatomy.
- Variants.
- State.
- Interaction.
- Accessibility.
- Responsive behavior.
- Selection rule.
- Anti-pattern.
- Framework implementation notes.
- Related recipes.

### 3.4. UX Pattern Library

Xây hướng dẫn flow cho:

- Authentication.
- Registration.
- Password reset.
- Onboarding.
- Search.
- Filter.
- Product selection.
- Cart.
- Checkout.
- Booking.
- Payment.
- Dashboard.
- CRUD.
- Settings.
- Profile.
- Notification.
- Multi-step form.
- Upload.
- Empty/error/retry.
- Confirmation.
- Destructive actions.

### 3.5. Domain Design Packs

Phát triển sâu cho các domain:

- E-commerce.
- Beauty/Fashion.
- SaaS.
- AI Product.
- Developer Tool.
- Hospitality/Travel.
- Healthcare.
- Finance/Fintech.
- Education.
- Portfolio/Agency.
- Admin/Internal Tool.

Domain Pack chỉ được cung cấp guidance, không override explicit user request hoặc existing brand identity.

### 3.6. Framework Knowledge Packs

Xây tài liệu implementation cho:

- React.
- Next.js.
- Vue.
- Nuxt.
- Svelte.
- SvelteKit.
- Angular.
- HTML/CSS/JS.
- Spring Boot + Thymeleaf.

### 3.7. Styling/UI Library Packs

Bổ sung:

- Tailwind.
- Bootstrap.
- shadcn/ui.
- MUI.
- CSS Modules.
- Sass.
- styled-components.
- custom design system.

### 3.8. Responsive Engineering Pack

Không chỉ rule “phải responsive”, mà hướng dẫn:

- What collapses.
- What stacks.
- What hides.
- What becomes drawer.
- What becomes horizontal scroll.
- Touch target.
- Mobile priority.
- Desktop density.
- Breakpoint strategy.

### 3.9. Motion & Interaction Pack

Hướng dẫn:

- When motion is useful.
- Enter/exit.
- Hover.
- Focus.
- Loading.
- Navigation transition.
- Modal/drawer.
- Reduced motion.
- Performance cost.
- Motion restraint.

### 3.10. Code Recipe System

Mở rộng recipe theo:

```text
Pattern
→ Framework
→ Styling system
→ Recipe
```

Recipe phải:

- Type-safe nếu stack hỗ trợ.
- Có dependency metadata.
- Có usage conditions.
- Có accessibility requirements.
- Có responsive behavior.
- Có variant.
- Có test/evidence expectation.
- Không hardcode brand palette.
- Có khả năng adapt vào existing design tokens.

### 3.11. Knowledge Metadata & Registry

Mỗi knowledge item phải có metadata:

```yaml
id:
category:
domain:
framework:
styling:
task_type:
ui_state:
applies_when:
avoid_when:
dependencies:
related_patterns:
related_recipes:
version:
source:
```

### 3.12. Knowledge Router

Router phải chọn context dựa trên:

```text
UI Context
+
User Intent
+
Workflow
+
Task Type
```

Chỉ load knowledge liên quan để tránh context bloat.

---

## 4. Mục tiêu phải đạt

P1 hoàn thành khi AI không còn chỉ nhận các câu kiểu:

```text
“làm giao diện hiện đại”
```

mà có thể nhận knowledge cụ thể như:

```text
- layout pattern nào phù hợp;
- component anatomy;
- responsive transformation;
- UX flow;
- framework implementation;
- related code recipe;
- anti-pattern cần tránh.
```

---

## 5. Output bắt buộc

- `knowledge_registry.json`
- `pattern_registry.json`
- `component_guides/`
- `ux_patterns/`
- `domain_packs/`
- `framework_packs/`
- `styling_packs/`
- `recipes/`
- `knowledge_selection.json`

---

## 6. Definition of Done

- Các nhóm component chính có hướng dẫn HOW, không chỉ DO/DON'T.
- Có framework guidance cho các stack mục tiêu.
- Knowledge Router không load toàn bộ knowledge.
- Recipe được liên kết với pattern và framework.
- Domain pack không override user instruction.
- Existing UI knowledge có khả năng adapt theo design token hiện hữu.
- Có benchmark chứng minh knowledge giúp AI tạo UI tốt hơn so với chỉ dùng rule.

---

# P2 — THINK: DESIGN REASONING & PLANNING ENGINE

## 1. Vai trò

P2 là tầng biến:

```text
User Request
+
UI Context
+
Knowledge
+
Constraints
```

thành một **Design Decision** và **Modification Plan** cụ thể.

P2 giải quyết:

> **“Với hệ thống này và yêu cầu này, nên làm gì?”**

---

## 2. Mục đích

- Ngăn AI nhảy từ prompt sang code.
- Biến design reasoning thành một bước có cấu trúc.
- Tách diagnosis khỏi implementation.
- Giúp mọi thay đổi có justification.
- Kiểm soát mức độ can thiệp.
- Tạo traceability giữa user request và code change.
- Chọn đúng knowledge/recipe trước khi sửa.

---

## 3. Những việc phải làm

### 3.1. Requirement Intelligence

Phân tích:

- User goal.
- Explicit requirements.
- Implicit requirements.
- Constraints.
- Target user.
- Domain.
- Task scope.
- Desired visual direction.
- Requested framework constraints.
- Allowed redesign level.

### 3.2. Workflow Classification

Phân loại:

```text
GREENFIELD
EXISTING_UI
PARTIAL_UI
AUDIT_ONLY
```

### 3.3. Problem Diagnosis

Trước khi đề xuất solution phải chỉ ra vấn đề:

- Visual.
- UX.
- Responsive.
- Accessibility.
- Consistency.
- Information architecture.
- Component duplication.
- Performance UI.
- Interaction.

Không được dùng các diagnosis mơ hồ như:

```text
“UI chưa đẹp”
```

mà phải cụ thể hóa thành issue có evidence.

### 3.4. Ambition / Change Level

Chuẩn hóa:

- `L1 – Safe Refinement`
- `L2 – Local Structural Change`
- `L3 – Major Redesign`

Existing UI:

- L1: mặc định cho phép.
- L2: cần justification.
- L3: cần explicit user permission.

### 3.5. Preservation Reasoning

Kết hợp UI Context để xác định:

- Locked properties.
- Protected properties.
- Controlled properties.
- Freely adjustable properties.

### 3.6. Design Strategy Selection

Chọn:

- Design direction.
- Layout strategy.
- Component strategy.
- Typography strategy.
- Responsive strategy.
- Motion strategy.
- Pattern set.
- Recipe set.

### 3.7. Knowledge Selection

P2 yêu cầu Knowledge Router lấy đúng:

- Domain pack.
- Framework pack.
- Styling pack.
- Pattern guides.
- Component guides.
- Recipes.

### 3.8. Impact Analysis

Xác định:

- Files affected.
- Pages affected.
- Components affected.
- Shared components.
- Business logic risk.
- Blast radius.
- Regression risk.

### 3.9. Modification Plan

Sinh plan chuẩn:

```yaml
user_goal:
workflow:
problems:
preserve:
change_level:
design_strategy:
knowledge_used:
recipes_used:
affected_pages:
affected_components:
affected_files:
expected_result:
risks:
runtime_checks:
rollback:
```

### 3.10. Decision Trace

Mỗi thay đổi quan trọng cần trace:

```text
Requirement
→ Diagnosis
→ Knowledge/Rule
→ Decision
→ Change
→ Verification
```

---

## 4. Mục tiêu phải đạt

P2 hoàn thành khi AI có thể giải thích rõ:

- Tại sao phải sửa.
- Sửa cái gì.
- Không sửa cái gì.
- Dùng knowledge nào.
- Dùng recipe nào.
- Mức thay đổi là L1/L2/L3.
- Ảnh hưởng tới component/page nào.
- Cần kiểm tra gì sau implementation.

---

## 5. Output bắt buộc

- `requirement_profile.json`
- `workflow_decision.json`
- `problem_diagnosis.json`
- `design_decision.json`
- `impact_analysis.json`
- `modification_plan.json`
- `decision_trace.json`

---

## 6. Definition of Done

- Không cho phép DO chạy khi chưa có Modification Plan.
- Existing UI L2 phải có justification.
- Existing UI L3 phải có permission trace.
- Mọi file change phải map về plan.
- Design strategy phải dựa trên UI Context + Knowledge, không phải preference ngẫu nhiên của AI.
- Plan phải chỉ định runtime checks tương ứng.

---

# P3 — DO: CONTROLLED IMPLEMENTATION ENGINE

## 1. Vai trò

P3 là tầng thực thi code theo quyết định đã được chuẩn hóa ở P2.

P3 giải quyết:

> **“Làm thế nào để biến Design Decision thành code mà không phá hệ thống?”**

---

## 2. Mục đích

- Giảm mức tự do không cần thiết của AI coding.
- Giữ implementation đúng framework hiện tại.
- Tận dụng shared component trước khi patch từng page.
- Giảm blast radius.
- Không đụng business logic ngoài scope.
- Áp dụng design token và recipe đúng cách.
- Theo dõi chính xác những gì đã thay đổi.

---

## 3. Những việc phải làm

### 3.1. Controlled Change Executor

Executor chỉ được nhận:

```text
UI Context
+
Design Decision
+
Modification Plan
+
Knowledge Selection
```

Không cho phép code trực tiếp chỉ từ user prompt.

### 3.2. Framework-Aware Implementation

Implementation phải tuân thủ conventions của framework detect ở P0.

Ví dụ:

- Không đổi React sang Vue.
- Không tự đưa Tailwind vào project Bootstrap.
- Không đổi Thymeleaf sang SPA nếu user không yêu cầu.
- Không thay UI library chỉ vì AI thích library khác.

### 3.3. Recipe Resolver

Chọn recipe phù hợp theo:

- Component.
- Pattern.
- Framework.
- Styling system.
- Existing design tokens.
- Change level.

Recipe phải được adapt thay vì copy cứng.

### 3.4. Shared-First Strategy

Nguyên tắc:

> **SHARED FIRST**

Nếu vấn đề xuất phát từ shared component:

```text
Shared component
→ fix once
→ verify all consumers
```

Không patch lặp nhiều page nếu có thể sửa đúng abstraction.

### 3.5. Scoped Editing

Chỉ sửa:

- Files trong modification plan.
- Component liên quan.
- Token liên quan.
- Layout liên quan.

Nếu cần mở rộng scope, phải quay lại THINK để cập nhật plan.

### 3.6. Dependency Guard

Không được:

- Tự cài package mới nếu chưa cần.
- Đổi framework.
- Đổi architecture.
- Thêm UI library trùng.
- Thêm dependency nặng để giải quyết vấn đề nhỏ.

### 3.7. Business Logic Guard

Không sửa:

- Domain logic.
- API contract.
- Database logic.
- Authentication logic.
- Payment logic.
- Backend flow.

trừ khi UI task thực sự yêu cầu và user cho phép.

### 3.8. Design Token Reuse

Existing UI phải ưu tiên reuse:

- Existing colors.
- Existing typography.
- Existing spacing.
- Existing radius.
- Existing component variants.

Không tự tạo token song song nếu không cần.

### 3.9. Change Ledger

Ghi:

```yaml
file:
component:
change:
reason:
plan_item:
change_level:
blast_radius:
```

### 3.10. Incremental Execution

Task lớn nên chia thành các nhóm thay đổi nhỏ:

```text
implement
→ verify
→ continue
```

Không rewrite toàn bộ rồi mới kiểm tra.

---

## 4. Mục tiêu phải đạt

P3 hoàn thành khi implementation:

- Đúng stack.
- Đúng plan.
- Đúng scope.
- Tái sử dụng component hiện tại.
- Không phá business logic.
- Không tự redesign ngoài quyền.
- Có change trace.
- Có thể rollback/repair theo từng nhóm thay đổi.

---

## 5. Output bắt buộc

- Source changes.
- `change_ledger.json`
- `implementation_report.json`
- `affected_surface_manifest.json`
- Runtime handoff cho P4.

---

## 6. Definition of Done

- Không có file change ngoài plan mà không có trace.
- Framework conventions được giữ.
- Shared component được ưu tiên.
- Existing palette không bị thay ngoài permission.
- Không có dependency thừa.
- Không có unrelated refactor.
- Mỗi nhóm thay đổi có thể được CHECK độc lập.

---

# P4 — CHECK: RUNTIME CRITIC & VERIFICATION

## 1. Vai trò

P4 là tầng kiểm chứng xem implementation có thực sự đạt mục tiêu hay không.

P4 giải quyết:

> **“Code đã sửa có thực sự đúng, đẹp, an toàn và đạt design intent không?”**

P4 không chỉ kiểm tra build thành công mà phải đánh giá UI thực tế.

---

## 2. Mục đích

- Chứng minh kết quả bằng evidence.
- Phát hiện visual regression.
- Phát hiện structural regression.
- Phát hiện preservation violation.
- Kiểm tra responsive.
- Kiểm tra interaction.
- Kiểm tra accessibility.
- Kiểm tra performance UI cơ bản.
- Tạo critic/repair loop có kiểm soát.

---

## 3. Những việc phải làm

### 3.1. Before/After Evidence

Existing UI phải capture baseline trước khi sửa.

Sau implementation:

```text
BEFORE
vs
AFTER
```

Evidence phải liên kết với:

- Page.
- Viewport.
- Scenario.
- Modification plan item.

### 3.2. Runtime Verification

Kiểm tra:

- App start.
- Route load.
- Console errors.
- Runtime errors.
- Missing assets.
- Broken links.
- Broken interactions.

### 3.3. Visual Regression Guard

Phát hiện:

- Overflow.
- Missing section.
- Layout collapse.
- Unexpected movement.
- Broken grid.
- Text clipping.
- Invisible controls.
- Unwanted palette change.
- Inconsistent spacing.

### 3.4. Structural Regression

So sánh:

- Route structure.
- Navigation.
- Important content.
- Section presence.
- Interactive elements.

### 3.5. Preservation Validation

Existing UI phải kiểm tra:

- Palette.
- Brand identity.
- Navigation.
- Major layout identity.
- Protected tokens.
- L1/L2/L3 budget.

Nếu vi phạm ngoài plan:

```text
PRESERVATION_FAIL
```

### 3.6. Responsive Matrix

Kiểm tra tối thiểu:

- Desktop.
- Tablet.
- Mobile.

Với page quan trọng cần scenario cụ thể.

### 3.7. Interaction Scenarios

Test:

- Navigation.
- Menu.
- Modal.
- Drawer.
- Forms.
- Tabs.
- Filters.
- Search.
- Checkout/booking flow.
- Error state.
- Loading state nếu có.

### 3.8. Accessibility Validation

Kiểm tra:

- Keyboard.
- Focus.
- Labels.
- Semantic structure.
- Contrast.
- Touch targets.
- Accessible states.
- axe khi capability có sẵn.

### 3.9. Performance UI Check

Bổ sung:

- CLS.
- LCP indicators.
- Excessive animation.
- Large image misuse.
- JS cost do UI dependency mới.
- Layout thrashing nếu phát hiện được.

### 3.10. Visual Critic

Critic không chỉ hỏi:

```text
“Có lỗi không?”
```

mà phải so:

```text
Design Intent
vs
Runtime Result
```

Đánh giá:

- Hierarchy.
- Consistency.
- Readability.
- Density.
- CTA emphasis.
- Alignment.
- Whitespace.
- Balance.
- Domain appropriateness.

### 3.11. Targeted Repair Loop

Nếu fail:

```text
CHECK
→ Issue
→ THINK
→ Targeted Repair Plan
→ DO
→ Targeted Recapture
→ CHECK
```

Không cho AI tự sửa ngẫu nhiên.

---

## 4. Mục tiêu phải đạt

P4 hoàn thành khi plugin có thể chứng minh:

- UI chạy.
- UI không regression.
- Existing identity được giữ.
- Responsive hoạt động.
- Interaction hoạt động.
- Accessibility không giảm.
- Visual result phù hợp design intent.
- Mọi lỗi có evidence.
- Repair chỉ tác động vào vùng fail.

---

## 5. Output bắt buộc

- Screenshots.
- Evidence manifest.
- Before/after comparison.
- `runtime_report.json`
- `visual_regression_report.json`
- `preservation_report.json`
- `responsive_report.json`
- `accessibility_report.json`
- `critic_report.json`
- `repair_plan.json` nếu fail.
- Final verification report.

---

## 6. Definition of Done

- Không kết thúc task chỉ vì build pass.
- Có evidence cho các surface bị sửa.
- Existing UI có before/after evidence.
- Preservation Gate pass.
- Responsive Gate pass.
- Interaction Gate pass với core flow.
- Accessibility không có regression nghiêm trọng.
- Critic issue được map về evidence.
- Repair loop chỉ sửa targeted area.
- Final state phải có PASS hoặc documented limitation.

---

# 7. QUAN HỆ GIỮA CÁC P

```text
USER REQUEST
     │
     ▼
┌───────────────┐
│ P0 — SEE      │
│ Understand    │
└───────┬───────┘
        │
        ▼
   UI Context
        │
        ▼
┌───────────────┐
│ P1 — KNOW     │
│ Knowledge     │
└───────┬───────┘
        │
        ▼
Relevant Knowledge
        │
        ▼
┌───────────────┐
│ P2 — THINK    │
│ Reason/Plan   │
└───────┬───────┘
        │
        ▼
Design Decision
Modification Plan
        │
        ▼
┌───────────────┐
│ P3 — DO       │
│ Implement     │
└───────┬───────┘
        │
        ▼
Implementation
        │
        ▼
┌───────────────┐
│ P4 — CHECK    │
│ Verify/Critic │
└───────┬───────┘
        │
    PASS│FAIL
        │
   ┌────┴─────┐
   │          │
 DONE     back to
           THINK
```

---

# 8. MỨC ĐỘ ƯU TIÊN PHÁT TRIỂN

| Ưu tiên | Tầng | Mức cần phát triển | Lý do |
|---|---|---:|---|
| P0 | SEE | Rất cao | AI hiện chưa hiểu đủ sâu UI/repo trước khi sửa |
| P1 | KNOW | Rất cao | Plugin còn thiên về rule, thiếu HOW TO DESIGN/HOW TO IMPLEMENT |
| P2 | THINK | Cao | Reasoning hiện phân tán, cần gom thành decision engine |
| P3 | DO | Trung bình–cao | AI coding vẫn có quá nhiều tự do trong implementation |
| P4 | CHECK | Trung bình | Nền runtime/evidence đã khá tốt, chủ yếu cần mở rộng critic/regression |

---

# 9. THỨ TỰ TRIỂN KHAI ĐỀ XUẤT

## Giai đoạn 1 — Làm lại P0

Ưu tiên:

1. Repository Analyzer.
2. Framework/Styling Detector.
3. Page/Route Inventory.
4. Component Graph.
5. Design Token Detector.
6. Runtime UI Analyzer.
7. Visual UI Analyzer.
8. UI Context Model.
9. Understanding Gate.

Không nên mở rộng thêm nhiều style/domain trước khi P0 đủ mạnh.

---

## Giai đoạn 2 — Xây lại P1

Ưu tiên:

1. Chuẩn hóa format knowledge.
2. Design Foundation.
3. Layout Engineering.
4. Component Engineering.
5. UX Patterns.
6. Framework Packs.
7. Domain Packs.
8. Recipe System.
9. Knowledge Router.

---

## Giai đoạn 3 — Gom P2 thành Reasoning Engine

Ưu tiên:

1. Requirement Intelligence.
2. Workflow Decision.
3. Diagnosis.
4. Preservation Reasoning.
5. Knowledge Selection.
6. Impact Analysis.
7. Design Decision.
8. Modification Plan.
9. Decision Trace.

---

## Giai đoạn 4 — Siết P3

Ưu tiên:

1. Controlled executor.
2. Scoped editing.
3. Shared-first.
4. Recipe resolver.
5. Framework guard.
6. Dependency guard.
7. Change ledger.

---

## Giai đoạn 5 — Nâng P4

Ưu tiên:

1. Before/after.
2. Preservation validation.
3. Visual regression.
4. Interaction matrix.
5. Responsive matrix.
6. Visual Critic.
7. Performance check.
8. Targeted repair loop.

---

# 10. NGUYÊN TẮC CHỐT

## SEE

> Không thiết kế khi chưa hiểu.

## KNOW

> Không để AI tự suy diễn nếu plugin có thể cung cấp kiến thức và implementation guidance.

## THINK

> Không code khi chưa có diagnosis, decision và plan.

## DO

> Không sửa ngoài phạm vi, không phá stack, không bỏ qua shared architecture.

## CHECK

> Không coi task hoàn thành nếu chưa có runtime evidence chứng minh kết quả.

---

# 11. ĐÍCH ĐẾN CỦA PLUGIN

Plugin sau khi hoàn thành các P không còn là:

```text
Prompt
+ Rules
+ AI Coding
```

mà trở thành:

```text
Perception
+ Knowledge
+ Reasoning
+ Controlled Execution
+ Verification
```

hay ngắn gọn:

> **SEE → KNOW → THINK → DO → CHECK**

Đây là kiến trúc giúp AI coding không chỉ “làm UI”, mà thực sự **hiểu hệ thống, biết cách thiết kế, biết lý do lựa chọn, thực thi đúng phạm vi và chứng minh được kết quả**.
