# 3. Hướng nâng cấp và phát triển sau này

Lộ trình chia 3 giai đoạn. Mỗi giai đoạn có mục tiêu, sản phẩm bàn giao và tiêu chí đo được. Nguyên tắc xuyên suốt
giữ nguyên: **giữ nội dung và thương hiệu, nâng thiết kế, chứng minh bằng kết quả render thật, không tự cài gì vào
dự án của người dùng.**

## 3.1. Giai đoạn ngắn hạn (v0.2.x — 2 đến 4 tuần)

**Mục tiêu:** đưa đợt nâng cấp vào tay người dùng và làm nó đáng tin trên nhiều dự án.

| Hạng mục | Bàn giao | Tiêu chí hoàn thành |
|---|---|---|
| Phát hành v0.2.0 | Version, release notes, gói phát hành, GitHub Release | `claude plugin update` cài được; MCP xanh trên Windows/macOS/Linux |
| CI cho recipe | Job Node: `tsc --strict` + build Next.js fixture + chụp ảnh + axe | Mọi PR đổi recipe đều được build và chụp tự động |
| Dark mode | Token sáng/tối trong theme, recipe dùng `dark:` nhất quán | axe không lỗi tương phản ở cả hai chế độ |
| Gate màu thương hiệu | So `dominant_hues` trước/sau trong `score_visual_critique` | Đổi hue ngoài phép → gate major |
| Eval E81–E90 | Kịch bản cho ambition, map, recipe, critique | `run_evals` bao phủ toàn bộ tính năng mới |
| Recipe màn hình ứng dụng (đợt 1) | Form nhiều bước, bảng dữ liệu, trang cài đặt, empty/error state | `suggest_recipes` có ứng viên cho role `form`, `data-table` |

## 3.2. Giai đoạn trung hạn (v0.3 – v0.4 — 1 đến 3 tháng)

**Mục tiêu:** phủ các stack phổ biến khác và có số liệu chất lượng khách quan.

1. **Bộ benchmark thật:** 8–12 dự án mã nguồn mở (landing, SaaS, e-commerce, docs, admin), chạy trọn vòng và công bố
   bảng điểm trước/sau theo từng phiên bản plugin. Dùng để hiệu chỉnh ngưỡng rubric và gate.
2. **Đa framework:** recipe cho Vue/Nuxt và Svelte/SvelteKit (cùng registry, cùng role/signature move), bản đồ UI hiểu
   props/slot của Vue và Svelte.
3. **Thư viện component:** biến thể recipe cho shadcn/ui + Radix và MUI; `suggest_recipes` chọn theo thư viện dự án
   đang dùng (`analyze_repository` → `ui_library`).
4. **Visual regression:** so ảnh theo vùng section, cảnh báo khi vùng ngoài phạm vi thay đổi (ví dụ khung app bị đổi).
5. **Hiệu năng như một gate:** LCP, CLS, kích thước JS của trang sau khi thêm Motion/GSAP; recipe chuyển động phải giữ
   trong ngân sách hiệu năng hiện có.
6. **Critic trên mọi host:** chế độ critique độc lập cho Codex và client MCP thuần (prompt chuẩn hoá, kiểm tra tính
   độc lập của ngữ cảnh).

## 3.3. Giai đoạn dài hạn (v1.0 và sau đó)

**Mục tiêu:** từ "nâng cấp từng trang" thành "đồng hành thiết kế cho cả sản phẩm".

- **Trích xuất design system từ code có sẵn:** sinh `DESIGN-SYSTEM.md` + token + kho component chuẩn hoá từ bản đồ UI
  của cả ứng dụng; phát hiện component trùng lặp và đề xuất hợp nhất.
- **Nhất quán đa trang:** chấm điểm theo cả ứng dụng (các trang cùng chung signature moves, nhịp khoảng cách, cấp
  heading), không chỉ từng trang.
- **Đầu vào thiết kế:** nhận ảnh chụp tham khảo hoặc file Figma (qua MCP) làm reference DNA, có kiểm tra chống sao chép.
- **Học từ phản hồi:** lưu điểm critic, lựa chọn recipe và đánh giá của người dùng theo dự án để ưu tiên recipe/hướng
  thiết kế phù hợp hơn ở lần sau (dữ liệu cục bộ, không gửi đi).
- **Xem trước tương tác:** tạo trang preview so sánh trước/sau (slider) từ ảnh chụp và bản đồ UI để người dùng duyệt
  trước khi áp thay đổi.
- **Chế độ nhóm:** báo cáo critique dạng PR comment, gate trong CI của dự án người dùng (ví dụ chặn merge khi điểm giảm).

## 3.4. Chỉ số theo dõi

| Chỉ số | Hiện tại | Mục tiêu v0.3 |
|---|---|---|
| Điểm rubric trung bình sau Elevate (benchmark) | 4.0 (1 fixture) | ≥ 3.8 trên ≥ 8 dự án |
| Tỷ lệ giữ nguyên nội dung (`content_preserved`) | 100% (fixture) | 100% |
| Tỷ lệ section được bố cục lại | 100% (fixture) | ≥ 60% trung bình |
| Lỗi axe mới do thay đổi | 0 | 0 |
| Số framework có recipe | 1 (React/Next) | 3 (React/Next, Vue/Nuxt, Svelte/SvelteKit) |
| Số recipe | 18 | ≥ 35 (thêm màn hình ứng dụng, dark mode, thư viện component) |

## 3.5. Rủi ro và cách giảm

| Rủi ro | Cách giảm |
|---|---|
| Elevate thay đổi quá tay, người dùng mất cảm giác quen thuộc | Gate giữ nội dung/khung app/màu thương hiệu; cụm từ bảo thủ luôn đưa về Refine; báo cáo trước/sau để người dùng duyệt |
| Critic thiên vị (chấm dễ) | Critic độc lập, chỉ có quyền đọc, bắt buộc bằng chứng; gate đo lường không phụ thuộc critic; hiệu chỉnh bằng benchmark |
| Recipe trở thành "template mới" khiến các sản phẩm giống nhau | Signature moves phải gắn với nội dung; banlist áp cho cả recipe; nhiều biến thể mỗi vai trò |
| Phụ thuộc thư viện chuyển động | Chỉ một thư viện, luôn có bản CSS thay thế, không tự cài |
| Chi phí chạy trình duyệt | Vòng lặp chỉ chụp lại phần bị ảnh hưởng (`recapture_evidence`), tối đa 2 lần lặp |
