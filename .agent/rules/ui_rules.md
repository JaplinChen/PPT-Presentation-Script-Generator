# UI RULES: TAILWIND STRICT MODE

> Tailwind CSS 嚴格模式 (推薦現代 Web 開發)
> 適用場景：使用 Next.js, React, Vue 並搭配 Tailwind CSS 的專案。
> 防止 Agent 寫出雜亂的 class 字串或自定義數值。

## 1. CLASS MANAGEMENT

* **Order**: Follow strict ordering: `Layout` > `Spacing` > `Sizing` > `Typography` > `Effects` > `Interactivity`.
* **Utility Only**: FORBIDDEN to use arbitrary values like `w-[355px]` or `bg-[#123456]`. You MUST use `tailwind.config.js` tokens (e.g., `w-96`, `bg-primary-500`).
* **Grouping**: If classes exceed 4 utility classes, strictly recommend using a utility function like `clsx` or `cn()` (shadcn/ui style) for readability.

## 2. RESPONSIVE DESIGN

* **Mobile First**: Default styles are mobile. Use `md:`, `lg:` prefixes for larger screens. NEVER use `max-width` media queries unless creating a specific modal override.
* **Layout Stability**: Always define explicit `width` and `height` for images/media to prevent Cumulative Layout Shift (CLS).

## 3. DOM STRUCTURE

* **Wrapper Hell**: FORBIDDEN to add extra `<div>` wrappers solely for positioning. Use Grid/Flex on the parent container instead.
* **Semantic HTML**:
    * Clickable elements? Use `<button>` or `<a>`. DO NOT put `onClick` on `<div>`.
    * Headings? Use `<h1>` to `<h6>` strictly for hierarchy, not for sizing.

## 4. COLOR SYSTEM

* **Theme Enforcement**: Use ONLY semantic color names (`text-error`, `bg-surface-muted`) defined in the theme. DO NOT use hardcoded palette colors (`red-500`, `gray-100`) directly in business logic components.
