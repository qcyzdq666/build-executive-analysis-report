# Visual system and quality gates

Use this reference when creating or auditing the final HTML. It is a reusable, brand-neutral reporting system.

## Palette

Use semantic CSS variables so charts, tables, cards, and labels share the same colors.

```css
:root {
  --blue: #2859a5;
  --blue-light: #4a7fd4;
  --blue-bg: #e8f0fe;
  --up: #d64545;
  --down: #2e8b57;
  --warning: #d97706;
  --bg: #f5f7fa;
  --card: #ffffff;
  --border: #d0d7e3;
  --text: #333333;
  --text-m: #666666;
  --text-l: #999999;
  --highlight: #fffde7;
  --hover: #f0f4ff;
  --fill-1: #c9d9ee;
  --fill-2: #9adcc2;
  --fill-3: #f5cf9a;
  --fill-4: #edb6be;
  --line-1: #8ba8c8;
  --line-2: #6bc4a0;
  --line-3: #d4a458;
  --line-4: #cc8490;
}
```

Use blue for structure and primary emphasis, amber for warnings, and soft fills for large chart areas. Prefer white cards on the light-gray page background, restrained borders, and light shadows.

## Direction colors

- Increase: `.metric-up`, `#d64545` (red).
- Decrease: `.metric-down`, `#2e8b57` (green).
- The colors describe numeric direction only. For an undesirable increase such as rising churn, keep it red and state the business meaning in words.
- Pair color with `+`/`-`, an arrow, or explicit text. Never rely on color alone.

## Tables and charts

- Table headers use `#2859a5` with white text.
- A current or selected row may use `#fffde7`; hover uses `#f0f4ff`.
- Large chart fills use the soft fill palette; line series use the corresponding darker line palette.
- Bars have no black outline. Keep chart backgrounds light with a border and rounded corners.
- Keep the same series color across the report and label the analytical conclusion near the chart.

## Delivery checks

Run `scripts/validate_report.py` on every final report. Fix errors before delivery and review warnings.

The deterministic gate checks:

- unresolved placeholders, duplicate IDs, required sections, and broken anchors;
- external dependencies, title/charset/viewport/main structure;
- responsive and print styles;
- required visual tokens and the red-up/green-down CSS mapping;
- evidence-map completeness and causal-status validity;
- risky causal language, sensitive field names, and unresolved `待确认` markers.

Then inspect desktop and narrow-screen rendering. Human review must confirm visual consistency, contrast, business meaning of directional changes, evidence quality, confidentiality, and publication permission.
