#!/usr/bin/env python3
"""Validate a standalone executive HTML report and its evidence map."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_:-]+\}\}")
CAUSAL_TERMS = ("导致", "驱动", "促进", "提升", "贡献", "证明", "决定", "归因于", "带来")
SENSITIVE_TERMS = (
    "user_id",
    "account_id",
    "device_id",
    "手机号",
    "身份证",
    "邮箱",
    "open_id",
    "union_id",
)
REQUIRED_SECTION_IDS = ("summary", "problem", "evidence", "actions", "limits")
REQUIRED_EVIDENCE_COLUMNS = (
    "claim_id",
    "section",
    "claim",
    "evidence_id",
    "source",
    "metric_definition",
    "scope",
    "causal_status",
    "review_status",
)
ALLOWED_CAUSAL_STATUS = {"descriptive", "associational", "quasi_causal", "causal"}
REQUIRED_VISUAL_TOKENS = {
    "primary blue": "#2859a5",
    "secondary blue": "#4a7fd4",
    "up red": "#d64545",
    "down green": "#2e8b57",
    "page background": "#f5f7fa",
    "border": "#d0d7e3",
}


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.external_urls: list[str] = []
        self.scripts: list[dict[str, str | None]] = []
        self.stylesheets: list[str] = []
        self.headings: list[tuple[str, str]] = []
        self._heading_tag: str | None = None
        self._heading_parts: list[str] = []
        self.has_main = False
        self.has_title = False
        self.has_charset = False
        self.has_viewport = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if attr.get("id"):
            self.ids.append(attr["id"] or "")
        if tag == "a" and attr.get("href"):
            href = attr["href"] or ""
            self.hrefs.append(href)
            self._collect_external(href)
        if tag in {"img", "iframe", "video", "audio", "source"} and attr.get("src"):
            self._collect_external(attr["src"] or "")
        if tag == "script":
            self.scripts.append({"src": attr.get("src"), "type": attr.get("type")})
            if attr.get("src"):
                self._collect_external(attr["src"] or "")
        if tag == "link" and attr.get("href"):
            rel = (attr.get("rel") or "").lower()
            href = attr["href"] or ""
            if "stylesheet" in rel:
                self.stylesheets.append(href)
            self._collect_external(href)
        if tag == "main":
            self.has_main = True
        if tag == "title":
            self.has_title = True
        if tag == "meta" and (attr.get("charset") or "").lower() == "utf-8":
            self.has_charset = True
        if tag == "meta" and (attr.get("name") or "").lower() == "viewport":
            self.has_viewport = True
        if tag in {"h1", "h2", "h3"}:
            self._heading_tag = tag
            self._heading_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == self._heading_tag:
            self.headings.append((tag, "".join(self._heading_parts).strip()))
            self._heading_tag = None
            self._heading_parts = []

    def handle_data(self, data: str) -> None:
        if self._heading_tag:
            self._heading_parts.append(data)

    def _collect_external(self, value: str) -> None:
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} or value.startswith("//"):
            self.external_urls.append(value)


def add(items: list[str], message: str) -> None:
    if message not in items:
        items.append(message)


def validate_html(path: Path) -> tuple[list[str], list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[str] = []
    text = path.read_text(encoding="utf-8")
    lower = text.lower()

    parser = ReportParser()
    try:
        parser.feed(text)
    except Exception as exc:  # HTMLParser is permissive, but report the unexpected.
        add(errors, f"HTML 解析失败：{exc}")

    placeholders = sorted(set(PLACEHOLDER_RE.findall(text)))
    if placeholders:
        add(errors, f"仍有 {len(placeholders)} 个模板占位符，例如：{', '.join(placeholders[:5])}")
    else:
        checks.append("未发现未替换的模板占位符")

    duplicates = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
    if duplicates:
        add(errors, f"存在重复 id：{', '.join(duplicates[:10])}")
    else:
        checks.append("未发现重复 id")

    id_set = set(parser.ids)
    missing_sections = [section for section in REQUIRED_SECTION_IDS if section not in id_set]
    if missing_sections:
        add(errors, f"缺少必要章节 id：{', '.join(missing_sections)}")
    else:
        checks.append("必要管理层报告章节齐全")

    broken_anchors = sorted(
        {href for href in parser.hrefs if href.startswith("#") and href != "#" and href[1:] not in id_set}
    )
    if broken_anchors:
        add(errors, f"存在无效页内锚点：{', '.join(broken_anchors[:10])}")
    else:
        checks.append("页内目录锚点有效")

    if parser.external_urls:
        add(errors, f"发现外部资源或链接依赖：{', '.join(sorted(set(parser.external_urls))[:8])}")
    else:
        checks.append("未发现 http(s) 外部资源依赖")

    if parser.stylesheets:
        add(warnings, f"发现 link 样式表引用，请确认是否为本地且会随报告交付：{', '.join(parser.stylesheets[:5])}")

    if not parser.has_title or not re.search(r"<title>\s*[^<]+\s*</title>", text, re.I):
        add(errors, "缺少有效 <title>")
    else:
        checks.append("页面标题存在")
    if not parser.has_charset:
        add(errors, "缺少 UTF-8 charset 声明")
    if not parser.has_viewport:
        add(errors, "缺少 viewport 声明")
    if not parser.has_main:
        add(warnings, "缺少语义化 <main> 容器")

    h1_count = sum(1 for tag, value in parser.headings if tag == "h1" and value)
    if h1_count != 1:
        add(warnings, f"建议只有一个非空 h1，当前为 {h1_count}")
    else:
        checks.append("存在唯一主标题 h1")

    if "@media" not in lower or "max-width" not in lower:
        add(warnings, "未检测到明确的窄屏响应式样式")
    else:
        checks.append("检测到响应式样式")
    if "@media print" not in lower:
        add(warnings, "未检测到打印样式")
    else:
        checks.append("检测到打印样式")

    missing_tokens = [label for label, value in REQUIRED_VISUAL_TOKENS.items() if value not in lower]
    if missing_tokens:
        add(errors, "缺少必要视觉令牌：" + "、".join(missing_tokens))
    else:
        checks.append("核心视觉令牌齐全")

    up_rule = re.search(r"\.metric-up\s*\{[^}]*?(?:var\(--up\)|#d64545)", lower, re.S)
    down_rule = re.search(r"\.metric-down\s*\{[^}]*?(?:var\(--down\)|#2e8b57)", lower, re.S)
    if not up_rule or not down_rule:
        add(errors, "涨跌样式映射不完整：必须使用 .metric-up=红、.metric-down=绿")
    else:
        checks.append("涨跌样式符合红涨、绿跌")

    causal_hits = {term: len(re.findall(re.escape(term), text)) for term in CAUSAL_TERMS}
    causal_hits = {term: count for term, count in causal_hits.items() if count}
    if causal_hits:
        add(warnings, "检测到高风险因果词，请核对证据等级：" + "、".join(f"{k}({v})" for k, v in causal_hits.items()))

    sensitive_hits = {term: len(re.findall(re.escape(term), text, re.I)) for term in SENSITIVE_TERMS}
    sensitive_hits = {term: count for term, count in sensitive_hits.items() if count}
    if sensitive_hits:
        add(warnings, "检测到疑似敏感字段词，请人工检查 HTML 源码：" + "、".join(f"{k}({v})" for k, v in sensitive_hits.items()))

    if "待确认" in text:
        add(warnings, "报告中仍包含“待确认”，发布前需人工处理")

    if "数据" not in text and "口径" not in text and "样本" not in text:
        add(warnings, "未检测到明显的数据、口径或样本说明")

    metrics = {
        "html_chars": len(text),
        "ids": len(parser.ids),
        "headings": len(parser.headings),
        "scripts": len(parser.scripts),
        "external_urls": len(parser.external_urls),
        "placeholders": len(placeholders),
        "visual_tokens": len(REQUIRED_VISUAL_TOKENS) - len(missing_tokens),
    }
    return errors, warnings, checks, metrics


def validate_evidence_map(path: Path) -> tuple[list[str], list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[str] = []
    metrics = {"claims": 0, "claims_without_evidence": 0, "invalid_causal_status": 0}

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        missing = [column for column in REQUIRED_EVIDENCE_COLUMNS if column not in columns]
        if missing:
            add(errors, f"evidence-map.csv 缺少字段：{', '.join(missing)}")
            return errors, warnings, checks, metrics
        rows = list(reader)

    if not rows:
        add(errors, "evidence-map.csv 没有结论记录")
        return errors, warnings, checks, metrics

    metrics["claims"] = len(rows)
    claim_ids: set[str] = set()
    duplicate_claim_ids: set[str] = set()
    for line_no, row in enumerate(rows, start=2):
        claim_id = (row.get("claim_id") or "").strip()
        if not claim_id:
            add(errors, f"第 {line_no} 行缺少 claim_id")
        elif claim_id in claim_ids:
            duplicate_claim_ids.add(claim_id)
        claim_ids.add(claim_id)

        if not (row.get("claim") or "").strip():
            add(errors, f"第 {line_no} 行缺少 claim")
        if not (row.get("evidence_id") or "").strip() or not (row.get("source") or "").strip():
            metrics["claims_without_evidence"] += 1
            add(errors, f"第 {line_no} 行结论缺少 evidence_id 或 source")
        if not (row.get("metric_definition") or "").strip():
            add(warnings, f"第 {line_no} 行未填写 metric_definition")
        if not (row.get("scope") or "").strip():
            add(warnings, f"第 {line_no} 行未填写 scope")

        status = (row.get("causal_status") or "").strip()
        if status not in ALLOWED_CAUSAL_STATUS:
            metrics["invalid_causal_status"] += 1
            add(errors, f"第 {line_no} 行 causal_status 无效：{status or '<空>'}")

        claim_text = row.get("claim") or ""
        if status in {"descriptive", "associational"} and any(term in claim_text for term in CAUSAL_TERMS):
            add(warnings, f"第 {line_no} 行结论含因果词，但 causal_status={status}")

    if duplicate_claim_ids:
        add(errors, f"claim_id 重复：{', '.join(sorted(duplicate_claim_ids))}")
    if metrics["claims_without_evidence"] == 0:
        checks.append("每条结论均填写 evidence_id 和 source")
    if metrics["invalid_causal_status"] == 0:
        checks.append("causal_status 均为允许值")
    checks.append(f"证据表包含 {len(rows)} 条结论")
    return errors, warnings, checks, metrics


def render_report(
    html_path: Path,
    evidence_path: Path | None,
    errors: list[str],
    warnings: list[str],
    checks: list[str],
    metrics: dict[str, int],
) -> str:
    status = "通过" if not errors else "未通过"

    def bullets(items: list[str], empty: str) -> str:
        if not items:
            return f"- {empty}"
        return "\n".join(f"- {item}" for item in items)

    evidence_label = str(evidence_path) if evidence_path else "未提供"
    metric_lines = "\n".join(f"- `{key}`: {value}" for key, value in metrics.items())
    return f"""# 报告校验结果

## 总体状态

**{status}**

- HTML：`{html_path}`
- 证据表：`{evidence_label}`
- 错误：{len(errors)}
- 风险/人工确认：{len(warnings)}

## 已通过检查

{bullets(checks, "无")}

## 必须修复

{bullets(errors, "无")}

## 风险与人工确认

{bullets(warnings, "无")}

## 文件指标

{metric_lines}

## 说明

该脚本只执行确定性和启发式检查，不能替代分析师对业务口径、因果识别、建议可行性、保密权限和视觉效果的最终确认。
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path, help="Standalone report HTML")
    parser.add_argument("--evidence-map", type=Path, default=None, help="Claim-to-evidence CSV")
    parser.add_argument("--output", type=Path, default=None, help="Markdown validation report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.html.is_file():
        print(f"HTML not found: {args.html}", file=sys.stderr)
        return 2
    if args.evidence_map is not None and not args.evidence_map.is_file():
        print(f"Evidence map not found: {args.evidence_map}", file=sys.stderr)
        return 2

    errors, warnings, checks, metrics = validate_html(args.html)
    if args.evidence_map:
        e_errors, e_warnings, e_checks, e_metrics = validate_evidence_map(args.evidence_map)
        errors.extend(e_errors)
        warnings.extend(e_warnings)
        checks.extend(e_checks)
        metrics.update({f"evidence_{key}": value for key, value in e_metrics.items()})
    else:
        warnings.append("未提供 evidence-map.csv，无法检查结论证据覆盖")

    report = render_report(args.html, args.evidence_map, errors, warnings, checks, metrics)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    print(report)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
