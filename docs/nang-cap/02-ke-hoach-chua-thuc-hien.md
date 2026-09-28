# 2. Những gì có trong kế hoạch nhưng chưa làm

Các mục dưới đây đã được đề xuất hoặc phát sinh trong quá trình nâng cấp nhưng **chưa được thực hiện** (hoặc mới làm
một phần). Mỗi mục ghi lý do, mức ưu tiên và ước lượng công sức (S: dưới 1 ngày, M: 1–3 ngày, L: trên 3 ngày).

## 2.1. Phát hành và vận hành

| Mục | Trạng thái | Vì sao chưa làm | Ưu tiên | Công sức |
|---|---|---|---|---|
| **Phát hành v0.2.0** (tăng version, release notes, gói phát hành, GitHub Release) | Chưa làm; CHANGELOG đang ở mục "Unreleased" | Chờ hoàn tất cả 4 bước nâng cấp | Cao | S |
| Xác nhận **MCP xanh trên máy người dùng** (Windows) sau v0.1.1 | Chờ phản hồi | Cần kết quả `claude plugin list`, `claude mcp list`, `python --version` từ máy người dùng | Cao | S |
| Xác nhận **Release v0.1.1** đã được publish trên GitHub | Chưa rõ | Việc tạo tag/release phải làm qua giao diện GitHub | Trung bình | S |
| Kiểm chứng V14 (gói giống hệt giữa các hệ điều hành) cho các thay đổi mới | Chỉ chạy trên CI của `main` | Workflow đóng gói không chạy trên PR | Trung bình | S |
| Làm mới `tests/run_rc_qualification.py` | Hỏng từ trước (cần zip `dist/0.1.0` cũ) | Không nằm trong CI | Thấp | S |

## 2.2. Bước "benchmark trước/sau" (F trong kế hoạch ban đầu)

Kế hoạch ban đầu có 6 phần: A bản đồ UI, B ambition, C direction + banlist, D recipe, E vòng ảnh chụp, **F benchmark**.
A–E đã xong. F mới làm **một phần**: có một fixture Next.js + Tailwind và bản dựng lại, test chứng minh giữ nội dung và
đạt chuẩn Elevate.

Còn thiếu:
- Bộ benchmark **nhiều dự án thật** (landing page, SaaS dashboard, e-commerce, blog/docs, form-heavy app) chạy trọn
  vòng: map → recipe → critique → điểm; lưu điểm trước/sau thành báo cáo so sánh giữa các phiên bản plugin.
- Cập nhật `development/benchmark_harness.py` để chạy vòng critique mới.
- Chạy critic bằng **subagent thật** trên nhiều mẫu để hiệu chỉnh ngưỡng (hiện ngưỡng 3.6 / +0.75 được đặt theo phán
  đoán và một fixture).

Ưu tiên: cao — công sức: L.

## 2.3. Độ phủ của recipe

| Mục | Hiện trạng | Ưu tiên | Công sức |
|---|---|---|---|
| Recipe cho **màn hình ứng dụng**: form nhiều bước, trang cài đặt, bảng dữ liệu đầy đủ (lọc, sắp xếp, trạng thái rỗng), onboarding, auth, empty/error state | Chỉ có `dashboard-focus` cho phần đầu dashboard | Cao | L |
| **Dark mode** cho theme token (cặp token sáng/tối, kiểm tra tương phản) | Theme chỉ có chế độ sáng | Cao | M |
| Recipe cho **Vue / Nuxt, Svelte / SvelteKit, Astro** | Chỉ React/Next; plugin chỉ nhắc "port bố cục và class" | Trung bình | L |
| Recipe cho **Tailwind v3** (config `theme.extend`) dạng file thật | Chỉ có hướng dẫn trong comment | Trung bình | S |
| Tích hợp **shadcn/ui, Radix, MUI, Chakra**: recipe dùng lại component thư viện của dự án | Recipe dùng thẻ HTML thuần + props `LinkComponent` | Trung bình | M |
| Recipe **navigation/footer** cho Reimagine | Cố ý không có (Elevate giữ khung app) | Thấp | M |
| CI chạy **`tsc` và build Next.js** cho recipe | Chỉ chạy thủ công ngoài bộ test (cần npm) | Cao | M |

## 2.4. Bản đồ UI (`map_ui_structure`)

| Mục | Hiện trạng | Ưu tiên | Công sức |
|---|---|---|---|
| Nhận diện class từ **CSS Modules, styled-components, Emotion, vanilla-extract** | Chỉ đọc class Tailwind/`class`/`className` và chuỗi trong `cn()`/`clsx()` | Trung bình | M |
| Suy diễn giá trị qua **hàm, hook, dữ liệu fetch, i18n** (`t("hero.title")`) | Chỉ literal, hằng số module, props, `.map` trên mảng literal | Trung bình | M |
| Import và scope đầy đủ cho **Vue SFC / Svelte** (props, slot, `v-for`) | Đọc template, chưa suy diễn props | Trung bình | M |
| Kiểm tra **màu thương hiệu có bị đổi** (so token trước/sau, màu chủ đạo từ ảnh chụp) thành một gate | Có `tokens.used.dominant_hues` nhưng chưa thành gate | Cao | S |
| Vai trò section do người dùng hiệu chỉnh được lưu lại (`.uiux/roles.json`) | Vai trò là heuristic, agent sửa tay trong tài liệu | Thấp | S |

## 2.5. Vòng review và đánh giá

| Mục | Hiện trạng | Ưu tiên | Công sức |
|---|---|---|---|
| Thêm **kịch bản eval E81+** cho ambition, bản đồ UI, recipe, critique | Evals dừng ở E01–E80 | Cao | M |
| **Visual regression bằng pixel** (so ảnh trước/sau theo vùng, phát hiện thay đổi ngoài phạm vi) | Chỉ có so sánh cấu trúc (`diff_ui_maps`) và critic | Trung bình | M |
| Critic tự động trên **Codex** / host không có subagent | Hướng dẫn chạy critique ngữ cảnh mới, chưa có tự động | Trung bình | M |
| Probe **hiệu năng** (LCP, CLS, JS bundle) làm gate cho recipe chuyển động | Motion probe có CLS; chưa có LCP/bundle | Trung bình | M |
| Kiểm thử **trực tiếp trên Codex** | Mới kiểm tra cấu trúc | Trung bình | S |

## 2.6. Nợ kỹ thuật nhỏ đã biết

- `run_rc_qualification.py` phụ thuộc vào artifact cũ.
- Trong bento recipe, các ô phụ để trống khá nhiều khi không có visual (critic đã ghi nhận — nên thêm biến thể có số
  liệu hoặc hình nhỏ).
- Gate "giảm chuyển động" chỉ phát hiện animation vô hạn; lỗi kiểu "kẹt blur" phải dựa vào critic nhìn ảnh.
- Ngưỡng tap target (> 3 phần tử < 24 px trên mobile) và chữ nhỏ (> 5 phần tử < 12 px) là giá trị khởi đầu, cần hiệu
  chỉnh bằng benchmark.
