---
name: build-executive-analysis-report
description: Turn completed business analysis findings, metric definitions, and aggregate tables into an evidence-traceable, conclusion-first, standalone HTML executive review. Use when users ask to create, rewrite, standardize, or audit management-facing business analysis reports, operating reviews, campaign retrospectives, strategy evaluations, or AI-generated HTML reports from existing conclusions; also use when users want to reuse a natural-language report workflow across teams. Do not use it to pretend to perform missing source-data analysis.
---

# Build Executive Analysis Report

## Purpose

Convert an analysis that already exists into a management-facing report that corrects metric misreadings, exposes the structure behind totals, connects every major claim to evidence, and ends with owned actions. Treat visual polish as a delivery layer, not the analytical product.

## Required workflow

Follow these stages in order. Do not generate the final HTML before the report specification is approved unless the user explicitly requests a one-pass draft.

### 1. Inspect the supplied material

Read the user's brief, notes, tables, existing documents, and prior report. Extract only facts supported by the supplied material. Do not silently recompute or invent results.

Collect or infer, then confirm when material:

- report topic and intended readers;
- decision the report should support;
- surface metric and why it may be misleading;
- confirmed findings and supporting values;
- observation unit, numerator, denominator, time window, and sample scope;
- valid comparisons and analytical method already used;
- recommended action, owner, and expected validation signal;
- confidentiality level and de-identification requirements;
- desired output directory.

Ask only blocking questions. If a field is non-blocking, mark it `待确认` instead of stalling.

### 2. Reconstruct the business logic

Use the reusable logic in `references/report-framework.md`:

1. Surface signal
2. Misreading risk
3. Observation-unit and metric reconstruction
4. Structural decomposition
5. Comparison and evidence
6. Business interpretation
7. Owned action
8. Boundary disclosure

Do not force a contrarian thesis. If the surface metric is already valid, state the qualification rather than manufacture a reversal.

### 3. Build the report specification

Create `report-spec.md` before HTML. Include:

- working title and one-sentence core thesis;
- audience and decision;
- 3-5 KPI cards;
- section sequence;
- one question answered by each chart or table;
- claim-to-evidence map;
- actions with owners;
- scope, causal, and confidentiality boundaries;
- unresolved items.

Use this default executive sequence unless the evidence requires a different order:

1. Hero: topic, thesis, scope/disclosure
2. Executive findings: 3-5 KPI or conclusion cards
3. Decision recommendation
4. Business problem and metric misreading
5. Reconstructed framework and observation unit
6. Structural decomposition and comparisons
7. Evidence details and method diagnostics
8. Actions by owner
9. Limitations, follow-up metrics, and appendix

Present the specification for confirmation. If the user has already approved an equivalent outline, proceed without asking again.

### 4. Create the evidence map

Create `evidence-map.csv` with these columns:

```text
claim_id,section,claim,evidence_id,source,metric_definition,scope,causal_status,review_status
```

Every headline claim and KPI must have at least one `evidence_id`. Use `causal_status` values `descriptive`, `associational`, `quasi_causal`, or `causal`. Do not upgrade the user's method.

Read and follow `references/evidence-and-language-rules.md` when claims contain percentages, percentage points, samples, treatment effects, attribution, or sensitive information.

### 5. Select only decision-useful components

Read `references/component-catalog.md`. Choose the smallest set that proves the thesis.

- Do not visualize a number merely because it exists.
- Each chart must have an explicit analytical question and a nearby conclusion.
- Keep deep methods and detailed tables later in the document or in collapsible sections.
- Prefer direct labels and plain language over decorative complexity.

### 6. Generate a standalone HTML report

Use `assets/executive-report-template.html` as the visual and structural base. Copy it into the output and replace its marked blocks; do not mutate the asset itself.

Before generating HTML, read and follow `references/visual-system-and-qa.md`. Its palette and validation rules are mandatory unless the user explicitly supplies another brand system. In particular, numeric direction follows the Chinese market convention: **red means up and green means down**. Direction colors describe movement, not whether the movement is good or bad.

Requirements:

- one self-contained HTML file;
- no CDN, remote font, analytics pixel, or external script;
- responsive desktop and narrow-screen layout;
- print-friendly styles;
- semantic headings, tables, navigation, and accessible labels;
- core thesis, numbers, and actions understandable above the method details;
- scope and evidence notes adjacent to the claims they qualify;
- only aggregate or explicitly authorized data embedded in source code.
- use the provided visual tokens rather than inventing near-duplicate colors;
- use `.metric-up` for increases and `.metric-down` for decreases; add text or an icon so meaning does not depend on color alone.

Use deterministic HTML/CSS/SVG or simple local JavaScript for rendering. Do not paste row-level source data into JavaScript just to enable tooltips.

### 7. Run quality gates

Run:

```powershell
python "${CLAUDE_SKILL_DIR}/scripts/validate_report.py" "<output>/report.html" --evidence-map "<output>/evidence-map.csv" --output "<output>/validation-report.md"
```

If `${CLAUDE_SKILL_DIR}` is unavailable, resolve paths relative to this `SKILL.md`.

Then inspect the report in a browser at desktop and narrow width when browser tooling is available. Fix objective failures before delivery. Do not claim browser or print validation if it was not run.

The final human review must confirm:

- analytical definitions and business interpretation;
- causal wording;
- action feasibility and ownership;
- confidentiality and publication permission.

### 8. Deliver truthfully

Default outputs:

```text
report-output/
├── report.html
├── report-spec.md
├── evidence-map.csv
└── validation-report.md
```

State what was generated, what was validated, what remains `待确认`, and whether any source analysis was intentionally left untouched.

## Non-negotiable rules

- Never invent a number, source, sample, owner, or business conclusion.
- Never describe an association as causation without matching evidence.
- Never generalize a selected sample to a full population without support.
- Never hide a material caveat in the appendix when it changes the headline interpretation.
- Never send or embed confidential row-level data without explicit authorization.
- Never equate attractive HTML with analysis quality.
- Never claim efficiency, reach, or adoption improvements without measured baselines and follow-up data.

## Resource guide

- `references/report-framework.md`: read when reconstructing the story and section order.
- `references/evidence-and-language-rules.md`: read before writing headline conclusions or reviewing language.
- `references/component-catalog.md`: read when selecting cards, charts, tables, and disclosure components.
- `references/visual-system-and-qa.md`: read before generating or auditing HTML; it defines the palette, red-up/green-down convention, and visual quality gates.
- `assets/executive-report-template.html`: copy as the report shell.
- `scripts/validate_report.py`: run on every finished report.
