# P0 Audit Report — SEE: UI Perception & Context Intelligence

## 1. Mục tiêu Audit
Đánh giá trạng thái hiện tại của plugin `ui-engineering` theo chuẩn P0 của kiến trúc SEE -> KNOW -> THINK -> DO -> CHECK. Đảm bảo tận dụng tối đa (reuse/extend/integrate) các module đang có, không xây dựng song song (duplicate architecture) đối với các khả năng đã tồn tại.

## 2. Capability Matrix Hiện Tại

### 2.1 Repository Analyzer
- **Trạng thái**: Đã tồn tại (Strong)
- **File/Module**: `uiux/engine/repo_intelligence/` (`framework.py`, `styling.py`, `profile.py`, v.v.)
- **Điểm mạnh**: Hỗ trợ detect nhiều framework (React, Next.js, Vue, Nuxt, Svelte, Angular, Spring), thư viện styling, package manager, có schema rõ ràng (`repo-profile.schema.json`).
- **Điểm thiếu**: Thiếu một số cấu hình project (e.g. build_tool, custom runtime commands) có thể sâu hơn, tuy nhiên đã đáp ứng ~90% yêu cầu.
- **Action**: **Reuse & Bổ sung nhỏ**.

### 2.2 Route / Page / Layout Inventory
- **Trạng thái**: Đã tồn tại (Strong)
- **File/Module**: `uiux/engine/repo_intelligence/routes.py`, `uiux/engine/ui_map/builder.py`.
- **Điểm mạnh**: Quét được SPA routes (React/Vue Router) và file-system routing (Next.js/Nuxt). `map_ui_structure` phân tách section rất tốt.
- **Action**: **Reuse**.

### 2.3 Component Graph Analyzer
- **Trạng thái**: Chỉ mới làm một phần (Incomplete)
- **File/Module**: `uiux/engine/repo_intelligence/components.py`, `uiux/engine/existing_ui/components.py`.
- **Điểm mạnh**: Có phân loại component (shared, layout, primitive).
- **Điểm thiếu**: Chưa xây dựng Component Dependency Graph. Chưa track được quan hệ: `ProductCard -> Home -> Search`. Chưa tính được `blast_radius` (mức độ ảnh hưởng khi sửa đổi).
- **Action**: **Refactor & Extend** (Mở rộng để quét AST/Import map xây graph).

### 2.4 Layout Structure Analyzer
- **Trạng thái**: Đã tồn tại (Strong)
- **File/Module**: `uiux/engine/existing_ui/layout.py`, `uiux/engine/ui_map/builder.py`.
- **Điểm mạnh**: Xây dựng thành công Layout Graph (`ui-map.json`), nhận diện app shell, section hierarchy.
- **Action**: **Reuse**.

### 2.5 Design Token Detector
- **Trạng thái**: Đã tồn tại (Good)
- **File/Module**: `uiux/engine/repo_intelligence/tokens.py`, `uiux/engine/existing_ui/identity.py`.
- **Điểm mạnh**: Quét được CSS vars, Tailwind config, tự suy luận primary colors, font stack, radius, spacing.
- **Điểm thiếu**: Trace evidence cho các token có thể cần cấu trúc rõ ràng hơn.
- **Action**: **Reuse & Tinh chỉnh evidence trace**.

### 2.6 Runtime UI Analyzer
- **Trạng thái**: Đã tồn tại (Strong)
- **File/Module**: `uiux/runtime/browser.py`, `evidence.py`, `accessibility.py`, `probes.py`.
- **Điểm mạnh**: Playwright-based, không tải trình duyệt tuỳ tiện, giữ đúng policy partial failure.
- **Action**: **Reuse**.

### 2.7 Visual UI Analyzer
- **Trạng thái**: Còn thiếu / Rất sơ sài (Incomplete)
- **File/Module**: Hiện mới có một số hàm trong `evaluator.py`, `critique.py`.
- **Điểm mạnh**: N/A
- **Điểm thiếu**: Chưa có module phân tích các đặc tính visual từ runtime evidence (visual hierarchy, alignment, whitespace, density, color dominance) ra dạng metadata phân tách rõ MEASURED vs INFERRED.
- **Action**: **Bổ sung module mới** (Tạo `uiux/engine/existing_ui/visual.py` hoặc tương tự).

### 2.8 UX Flow Analyzer
- **Trạng thái**: Chỉ mới làm một phần (Partial)
- **File/Module**: `uiux/engine/existing_ui/ux_flows.py`.
- **Điểm mạnh**: Dựa vào heuristic string matching trên routes và file content để phát hiện state (loading, error, empty).
- **Điểm thiếu**: Chưa map thành chuỗi flow step-by-step thực sự.
- **Action**: **Extend**.

### 2.9 UI State Classifier
- **Trạng thái**: Đã tồn tại (Strong)
- **File/Module**: `uiux/engine/repo_intelligence/ui_state_detector.py`.
- **Điểm mạnh**: Định danh GREENFIELD, PARTIAL_UI, EXISTING_UI.
- **Action**: **Reuse**.

### 2.10 UI Context Model
- **Trạng thái**: Đã tồn tại (Strong)
- **File/Module**: `schemas/existing-ui-profile.schema.json`, `uiux/engine/existing_ui/profile.py`.
- **Điểm mạnh**: Schema canonical tốt, cover các phần layout, identity, component.
- **Action**: **Extend schema** (Thêm `visual_language` metrics, `component_graph` dependencies, `understanding_gate`).

### 2.11 Understanding Gate
- **Trạng thái**: Còn thiếu (Missing)
- **File/Module**: N/A
- **Điểm thiếu**: Chưa có machine-readable gate (PASS / PARTIAL / BLOCKED) theo contract P0 để chặn AI đi sang tầng THINK khi thiếu context trọng yếu.
- **Action**: **Bổ sung module mới** (`uiux/engine/existing_ui/understanding_gate.py`).

## 3. Kế Hoạch Triển Khai (Implementation Plan)

Dựa trên Audit, P0 sẽ tuân theo nguyên tắc: **Không duplicate, chỉ mở rộng và tích hợp.**

1. **Bổ sung `Understanding Gate`**:
   - Thêm `understanding_gate.py` trong `uiux/engine/existing_ui/`.
   - Update `existing-ui-profile.schema.json` và `api.py` để expose kết quả gate.
2. **Mở rộng `Component Graph Analyzer`**:
   - Refactor `components.py` trong `uiux/engine/existing_ui` (hoặc tạo `component_graph.py`) để phân tích imports/dependencies và tính toán `blast_radius`.
3. **Mở rộng `Visual UI Analyzer`**:
   - Tạo `visual_analyzer.py` nhận đầu vào là `RepositorySnapshot` và `RuntimeEvidence` để sinh structured metadata cho hierarchy, density, alignment.
4. **Nâng cấp Schema & Merge**:
   - Cập nhật `existing-ui-profile.schema.json` chứa `visual_analysis`, `component_graph`, `understanding_gate`.
   - Cập nhật `build_existing_ui_profile` để kết hợp các luồng dữ liệu này.

## 4. Migration Impact
- **Backward Compatibility**: API hiện hữu (`analyze_repository`, `analyze_existing_ui`, `map_ui_structure`) không bị phá vỡ. Các field mới sẽ được thêm vào (Additive changes).
- **Performance**: Việc xây dựng component graph có thể thêm thời gian xử lý AST/Regex trên file lớn, sẽ sử dụng cache/fingerprint giới hạn nếu cần.
- **Evals/Tests**: Cần cập nhật tests để cover `Understanding Gate` và `Component Graph`.
