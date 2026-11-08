"""Build the repository's research index, graph data and animated README preview.

Run from any directory: python scripts/research_graph.py
Only Git-tracked <theme>/plan.md and report-level Markdown under each theme's
type directories are inputs; old type-first paths remain readable in place. Objects represent
concrete research work, never candidate names extracted from report prose.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime
from fnmatch import fnmatchcase
from html import escape
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import unicodedata
from urllib.parse import unquote, urlsplit, quote

from markdown_it import MarkdownIt
import yaml

TYPES = {"paper": "论文", "open-source": "开源项目", "product": "产品",
         "benchmark": "评测", "analysis": "分析判断"}
COLORS = {"theme": "#b0a0ff", "paper": "#ffbe75",
          "open-source": "#57deca", "product": "#75acff", "benchmark": "#f78dc1",
          "analysis": "#c7a3ff", "unknown": "#9aaac6"}
STATUS = {"draft": "草案", "active": "进行中", "paused": "暂停",
          "completed": "已完成", "archived": "已归档", "planned": "待开始",
          "in_progress": "进行中", "partial": "部分完成", "blocked": "阻塞",
          "done": "已完成", "deferred": "暂缓", "cancelled": "已取消",
          "complete": "完整", "unknown": "未标注"}
MD = MarkdownIt("commonmark").enable("table")
START, END = "<!-- research-graph:start -->", "<!-- research-graph:end -->"
EXCLUDED = {".tmp", "references", "assets", "archive", "node_modules", ".git", ".agents"}
SUPPORT_ROOTS = EXCLUDED | {"docs", "scripts", "tests", "plans", "reports"}


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def inline_text(token) -> str:
    if token.children is None:
        return token.content
    return "".join(t.content if t.type not in {"softbreak", "hardbreak"} else " "
                   for t in token.children if t.type in {"text", "code_inline", "softbreak", "hardbreak"})


def work_ids(headers: list[str], row: list[str]) -> list[str]:
    """Read identity columns only; dependency/reference IDs are not owners."""
    identity_fields = {"id", "任务", "工作", "任务id", "工作id", "任务编号", "工作编号",
                       "调研工作id", "调研工作编号", "关联任务", "关联工作", "关联任务id", "关联工作id",
                       "任务/对象id", "工作/对象id"}
    values = []
    for header, value in zip(headers, row):
        normalized = re.sub(r"\s+", "", unicodedata.normalize("NFKC", header)).casefold()
        if normalized in identity_fields:
            values.append(value)
    return list(dict.fromkeys(re.findall(r"\bT\d+\b", " ".join(values))))


def parse_markdown(text: str) -> dict:
    """Read headings, actual Markdown links and tables; ignore links in code/comments."""
    meta = {}
    body = text
    front = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.S)
    if front:
        value = yaml.safe_load(front.group(1))
        if not isinstance(value, dict):
            raise ValueError("Markdown front matter must be a mapping")
        meta = value
        body = text[front.end():]
    tokens = MD.parse(body)
    body_lines = body.splitlines()
    title, section, tables, links, summaries, paragraphs = "", "", [], [], [], []
    rows, row = [], []
    in_table = False
    headings, table_headers, row_links = [], [], []
    table_order = 0
    for i, token in enumerate(tokens):
        if token.type == "heading_open":
            section = inline_text(tokens[i + 1])
            level = int(token.tag[1:])
            while headings and headings[-1][0] >= level:
                headings.pop()
            headings.append((level, section))
            if token.tag == "h1" and not title:
                title = section
        elif token.type == "html_block":
            match = re.search(r"<!--\s*research-summary\s*\n(.*?)-->", token.content, re.S)
            if match:
                summaries.append(match.group(1))
        elif token.type == "table_open":
            rows = []
            in_table = True
            table_headers = []
            table_order = i
        elif token.type == "tr_open":
            row = []
            row_links = []
        elif token.type == "inline":
            cell_index = len(row)
            if i and tokens[i - 1].type in {"th_open", "td_open"}:
                row.append(inline_text(token))
            elif not in_table and i and tokens[i - 1].type != "heading_open":
                paragraphs.append({"section": section, "sections": [h[1] for h in headings],
                                   "order": i, "text": inline_text(token)})
            children = token.children or []
            for child in children:
                if child.type == "link_open":
                    link = {"href": child.attrGet("href"), "section": section,
                            "sections": [h[1] for h in headings], "inTable": in_table,
                            "field": table_headers[cell_index] if cell_index < len(table_headers) else "",
                            "text": inline_text(token),
                            "context": "\n".join(body_lines[slice(*token.map)]) if token.map else token.content}
                    links.append(link)
                    if in_table:
                        row_links.append(link)
        elif token.type == "tr_close":
            if not table_headers:
                table_headers = list(row)
            else:
                # Bind a report cell to the row's work-ID column, never IDs in
                # a prerequisite/reference column elsewhere on the same row.
                for link in row_links:
                    link["taskIds"] = work_ids(table_headers, row)
            rows.append(row)
        elif token.type == "table_close" and rows:
            tables.append({"section": section, "sections": [h[1] for h in headings],
                           "order": table_order, "headers": rows[0], "rows": rows[1:]})
            in_table = False
    return {"meta": meta, "title": title, "tables": tables, "links": links, "summaries": summaries,
            "paragraphs": paragraphs}


def next_steps(parsed: dict) -> list[str]:
    """Summarize the plan's explicit next actions without inventing follow-up work."""
    steps = []
    for table in parsed["tables"]:
        if not in_section(table, "下一步"):
            continue
        for index, row in enumerate(table["rows"]):
            action = table_value(table["headers"], row, "下一步", "恢复条件", "后续安排")
            if action:
                identity = table_value(table["headers"], row, "问题", "任务", "工作")
                steps.append((table["order"], index, f"{identity}：{action}" if identity else action))
    steps.extend((p["order"], 0, p["text"]) for p in parsed.get("paragraphs", []) if in_section(p, "下一步") and p["text"].strip())
    return list(dict.fromkeys(text for _, _, text in sorted(steps)))


def in_section(item: dict, keyword: str) -> bool:
    return any(keyword in title for title in item.get("sections", [item["section"]]))


def is_result_link(link: dict) -> bool:
    """Only a declared result location can establish a work's delivered report."""
    if link["inTable"]:
        field = re.sub(r"\s+", "", link["field"])
        if any(word in field for word in ("参考", "预期", "预计", "计划", "待", "前置", "依赖")):
            return False
        if field in {"实际报告", "实际交付", "已交付报告", "交付报告", "成果报告", "实际成果", "交付成果"}:
            return True
        if field not in {"报告", "报告链接", "成果", "成果链接"}:
            return False
    elif re.match(r"^(?:实际报告|已交付报告|交付报告|成果报告)[：:]", link["text"].strip()):
        return True
    if any(any(word in title for word in ("参考", "下一步", "预期", "待办")) for title in link["sections"]):
        return False
    return any(in_section(link, name) for name in ("成果索引", "实际交付", "已交付报告", "交付成果"))


def text_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def safe_file(root: Path, path: Path) -> bool:
    """Never follow input symlinks or references escaping the checkout."""
    try:
        rel = path.relative_to(root)
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return not any(p in EXCLUDED for p in rel.parts) and not any(
        root.joinpath(*rel.parts[:i]).is_symlink() for i in range(1, len(rel.parts) + 1))


def resolve_link(root: Path, source: Path, href: str) -> str | None:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    candidate = (source.parent / unquote(parsed.path)).resolve()
    if safe_file(root, candidate) and candidate.is_file():
        return candidate.relative_to(root).as_posix()
    return None


def table_value(headers: list[str], row: list[str], *names: str) -> str:
    for index, header in enumerate(headers):
        if any(name in header for name in names):
            return row[index].strip() if index < len(row) else ""
    return ""


def canonical_status(value: str) -> str:
    aliases = {"已完成": "done", "进行中": "in_progress", "待开始": "planned",
               "部分完成": "partial", "阻塞": "blocked", "暂缓": "deferred", "已取消": "cancelled",
               "完整": "complete", "部分": "partial"}
    return aliases.get(value, value) if value else "unknown"


def github_url(repository: str, branch: str, path: str) -> str:
    return f"https://github.com/{repository}/blob/{quote(branch, safe='')}/{quote(path, safe='/')}"


def tracked_inputs(root: Path) -> set[str]:
    result = subprocess.check_output(["git", "ls-files", "-z", "--cached"], cwd=root)
    return set(result.decode("utf-8").split("\0")) - {""}


def build_graph(root: Path, repository: str, branch: str, *, input_paths: set[str] | None = None) -> dict:
    root = root.resolve()
    if input_paths is None:
        input_paths = tracked_inputs(root)
    config_path = root / ".research-graph.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {"schema_version": 1, "exclude_paths": []}
    if config.get("schema_version") != 1 or not isinstance(config.get("exclude_paths"), list) or any(
            not isinstance(pattern, str) for pattern in config["exclude_paths"]):
        raise ValueError("Invalid .research-graph.json")

    def accepted(path):
        rel = path.relative_to(root).as_posix()
        return rel in input_paths and safe_file(root, path) and not any(
            fnmatchcase(rel, pattern) for pattern in config["exclude_paths"])

    nodes, edges, warnings, source_text = {}, {}, [], {}

    def node(**data):
        if data["id"] not in nodes:
            data["color"] = COLORS.get(data.get("type", data["kind"]), COLORS["unknown"])
            data["statusLabel"] = STATUS.get(data.get("status"), data.get("status", "未标注"))
            data["url"] = github_url(repository, branch, data["path"])
            nodes[data["id"]] = data
        return nodes[data["id"]]

    def edge(a, b, relation, evidence):
        key = (a, b, relation)
        if key not in edges:
            edges[key] = {"source": a, "target": b, "relation": relation, "evidence": evidence}

    def read(path):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8-sig")
        source_text[rel] = text
        return text, parse_markdown(text)

    reports = {}
    report_candidates = {}
    for category in TYPES:
        for path in root.glob(f"*/{category}/*/*.md"):
            theme = path.relative_to(root).parts[0]
            if theme not in SUPPORT_ROOTS:
                report_candidates[path] = (category, theme)
    # Compatibility is read-only: indexing an old report never moves it.
    for category in TYPES:
        for path in (root / category).glob("*/*/*.md"):
            report_candidates.setdefault(path, (category, path.relative_to(root).parts[1]))
    for report_type in TYPES:
        for path, theme in sorted((path, theme) for path, (kind, theme) in report_candidates.items() if kind == report_type):
            if not accepted(path):
                continue
            text = path.read_text(encoding="utf-8-sig")
            parsed = parse_markdown(text)
            summaries = parsed["summaries"]
            if path.name != "report.md" and not summaries:
                continue
            rel = path.relative_to(root).as_posix()
            source_text[rel] = text
            if len(summaries) > 1:
                raise ValueError(f"Duplicate research-summary in {rel}")
            summary = {}
            if summaries:
                try:
                    summary = json.loads(summaries[0])
                    if not isinstance(summary, dict):
                        raise ValueError("expected object")
                    if not isinstance(summary.get("items", []), list) or any(
                            not isinstance(item, dict) for item in summary.get("items", [])):
                        raise ValueError("items must be a list of objects")
                except (ValueError, TypeError) as error:
                    raise ValueError(f"Invalid research-summary in {rel}: {error}") from error
            completion = summary.get("completion", "")
            if not completion:
                marker = re.search(r"^>\s*调研状态[：:]\s*(.+)$", text, re.M)
                completion = marker.group(1).strip() if marker else "unknown"
            report = node(id="report:" + rel, kind="report", type=report_type,
                          label=parsed["title"] or path.stem, path=rel, theme=theme,
                          status=canonical_status(completion), runId=summary.get("run_id", ""),
                          updatedAt="")
            reports[rel] = (report, parsed)

    plans, tasks = {}, {}
    plan_candidates = {path for path in root.glob("*/plan.md") if path.parent.name not in SUPPORT_ROOTS}
    plan_candidates.update((root / "plans").glob("*/plan.md"))
    for path in sorted(plan_candidates):
        if not accepted(path):
            continue
        _, parsed = read(path)
        meta = parsed["meta"]
        theme = text_value(meta.get("theme_id") or path.parent.name)
        if theme in plans:
            raise ValueError(f"Duplicate theme_id: {theme}")
        rel = path.relative_to(root).as_posix()
        theme_node = node(id="theme:" + theme, kind="theme", type="theme", theme=theme,
                          label=text_value(meta.get("title")) or parsed["title"] or theme,
                          status=canonical_status(text_value(meta.get("status"))), path=rel,
                          revision=meta.get("revision"), updatedAt=text_value(meta.get("updated_at")))
        plans[theme] = (theme_node, parsed)
        for table in parsed["tables"]:
            if not in_section(table, "对象与任务"):
                continue
            for row in table["rows"]:
                identifiers = work_ids(table["headers"], row)
                if len(identifiers) != 1:
                    warnings.append(f"{rel}: 工作定义行需明确一个工作编号，当前为 {identifiers or '未识别'}")
                    continue
                task_id = identifiers[0]
                identity = f"task:{theme}:{task_id}"
                if identity in tasks:
                    raise ValueError(f"Duplicate task ID in {rel}: {task_id}")
                target = table_value(table["headers"], row, "类型", "对象")
                task_type = re.split(r"[／/：:]", target)[0].strip()
                task = node(id=identity, kind="task", type=task_type if task_type in TYPES else "unknown",
                            label=table_value(table["headers"], row, "本次目标", "目标") or target,
                            target=target,
                            taskId=task_id, theme=theme, path=rel,
                            status=canonical_status(table_value(table["headers"], row, "状态")),
                            priority=table_value(table["headers"], row, "优先级"),
                            runId=table_value(table["headers"], row, "run_id"),
                            updatedAt=theme_node["updatedAt"])
                tasks[identity] = (task, table_value(table["headers"], row, "前置", "依赖"))
                edge(theme_node["id"], identity, "contains", rel + " · 对象与任务")

    # Report directories remain browsable even when no persistent theme plan exists.
    for rel, (report, _) in reports.items():
        theme = report["theme"]
        if theme not in plans:
            theme_node = node(id="theme:" + theme, kind="theme", type="theme", theme=theme,
                              label=theme, status="unknown", path=rel, revision=None,
                              updatedAt="", inferredFromDirectory=True)
            plans[theme] = (theme_node, {"tables": [], "links": []})
        theme_node = plans[theme][0]
        report["updatedAt"] = theme_node["updatedAt"]
        edge(theme_node["id"], report["id"], "groups", rel + " · 目录归类")

    for theme, (theme_node, parsed) in plans.items():
        plan_path = root / theme_node["path"]
        for link in parsed["links"]:
            if not is_result_link(link):
                continue
            resolved = resolve_link(root, plan_path, link["href"])
            if resolved not in reports:
                continue
            report = reports[resolved][0]
            edge(theme_node["id"], report["id"], "delivers", theme_node["path"] + " · " + link["section"])
            # Explicit task IDs must share this actual Markdown paragraph/table row.
            identifiers = link.get("taskIds", re.findall(r"\bT\d+\b", link["context"]))
            for task_id in identifiers:
                key = f"task:{theme}:{task_id}"
                if key in tasks:
                    edge(key, report["id"], "produces", theme_node["path"] + " · 成果关联")
        for table in parsed["tables"]:
            if not in_section(table, "依赖与接受条件"):
                continue
            for row in table["rows"]:
                joined = " ".join(row)
                match = re.search(r"(T\d+)\s*(?:←|<-|依赖)\s*(T\d+)", joined)
                if match:
                    downstream, upstream = (f"task:{theme}:{v}" for v in match.groups())
                    if downstream in tasks and upstream in tasks and downstream != upstream:
                        edge(upstream, downstream, "depends", theme_node["path"] + " · 依赖与接受条件")
    for key, (task, prerequisite) in tasks.items():
        for task_id in re.findall(r"\bT\d+\b", prerequisite):
            upstream = f"task:{task['theme']}:{task_id}"
            if upstream in tasks and upstream != key:
                edge(upstream, key, "depends", task["path"] + " · 前置任务")
            else:
                warnings.append(f"{task['path']}: {task['taskId']} 前置任务 {task_id} 无效")
    for rel, (report, parsed) in reports.items():
        for link in parsed["links"]:
            target = resolve_link(root, root / rel, link["href"])
            if target in reports and target != rel:
                edge(report["id"], reports[target][0]["id"], "cites", rel + " · Markdown 链接")

    # The overview's "object" is a concrete research work item, never an entity
    # mentioned by a report. Reports are supporting links, not graph nodes.
    work_nodes = {}
    output_edges = {}
    report_metadata = {}
    report_work = {}
    for rel, (report, _) in reports.items():
        report_metadata[report["id"]] = {k: report[k] for k in ("id", "label", "path", "url", "status", "statusLabel", "type")}
    for key, (task, _) in tasks.items():
        work = {**task, "id": f"work:{task['theme']}:{task['taskId']}", "kind": "object",
                "reportIds": [], "pendingReportIds": [], "sourceKind": "plan"}
        work_nodes[work["id"]] = work
        for e in edges.values():
            if e["source"] == key and e["relation"] == "produces":
                work["reportIds"].append(e["target"])
                report_work.setdefault(e["target"], set()).add(work["id"])

    # Index every explicit association before processing supplemental filenames:
    # details.md may sort before report.md, but must not become a new work.
    directory_work = {}
    for report_id, work_set in report_work.items():
        directory = Path(report_metadata[report_id]["path"]).parent.as_posix()
        directory_work.setdefault(directory, set()).update(work_set)
    for rel, (report, _) in reports.items():
        if report["id"] in report_work:
            report_metadata[report["id"]].update(associationStatus="explicit", workIds=sorted(report_work[report["id"]]))
            continue
        directory = Path(rel).parent.as_posix()
        candidates = sorted(directory_work.get(directory, set()))
        if candidates:
            # Directory proximity is enough to avoid a duplicate work, but is
            # not evidence that any particular plan item delivered this file.
            report_metadata[report["id"]].update(associationStatus="pending", workIds=[], candidateWorkIds=candidates)
            for work_id in candidates:
                work_nodes[work_id]["pendingReportIds"].append(report["id"])
            warnings.append(f"{rel}: 补充报告待关联（候选工作：{', '.join(candidates)}），未新增工作或计为已交付")
            continue
        # With no matching plan item, one target directory denotes one work.
        work_id = "work:" + digest(directory)
        if work_id not in work_nodes:
            work_nodes[work_id] = {**report, "id": work_id, "kind": "object", "reportIds": [],
                                   "pendingReportIds": [], "sourceKind": "report"}
        elif Path(rel).name == "report.md":
            # The canonical report supplies the directory work's display name.
            work_nodes[work_id].update({key: report[key] for key in ("label", "path", "url", "status", "statusLabel", "runId", "updatedAt")})
        work_nodes[work_id]["reportIds"].append(report["id"])
        report_work[report["id"]] = {work_id}
        report_metadata[report["id"]].update(associationStatus="directory", workIds=[work_id])
    for work in work_nodes.values():
        theme_id = "theme:" + work["theme"]
        output_edges[(theme_id, work["id"], "includes")] = {
            "source": theme_id, "target": work["id"], "relation": "includes", "evidence": work["path"]}
    for e in edges.values():
        if e["relation"] == "depends":
            a, b = e["source"].replace("task:", "work:", 1), e["target"].replace("task:", "work:", 1)
            if a in work_nodes and b in work_nodes:
                output_edges[(a, b, "depends")] = {**e, "source": a, "target": b}
    output = sorted([n for n in nodes.values() if n["kind"] == "theme"] + list(work_nodes.values()), key=lambda n: n["id"])
    overview = []
    for theme, (theme_node, parsed) in sorted(plans.items()):
        report_ids = {r for work in work_nodes.values() if work["theme"] == theme for r in work["reportIds"]}
        report_ids.update(e["target"] for e in edges.values()
                          if e["source"] == theme_node["id"] and e["relation"] in {"groups", "delivers"})
        overview.append({"theme": theme, "title": theme_node["label"],
                         "status": theme_node["status"], "statusLabel": theme_node["statusLabel"],
                         "planPath": None if theme_node.get("inferredFromDirectory") else theme_node["path"],
                         "reportIds": sorted(report_ids), "nextSteps": next_steps(parsed)})
    assign_layout(output)
    counts = Counter(n["kind"] for n in output)
    fingerprint = digest(json.dumps({"sources": source_text, "policy": config}, ensure_ascii=False, sort_keys=True))
    return {"schemaVersion": 2, "repository": repository, "branch": branch,
            "fingerprint": fingerprint, "types": TYPES, "colors": COLORS,
            "stats": {"themes": counts["theme"], "types": len({n["type"] for n in work_nodes.values() if n["type"] in TYPES}),
                      "objects": counts["object"], "reports": len(reports)},
            "updatedAt": max((n.get("updatedAt", "") for n in output), default=""),
            "nodes": output, "edges": sorted(output_edges.values(), key=lambda e: (e["source"], e["target"], e["relation"])),
            "reports": sorted(report_metadata.values(), key=lambda r: r["id"]),
            "themeOverview": overview,
            "warnings": sorted(set(warnings))}


def assign_layout(nodes):
    """Stable, hash-seeded cluster layout shared by GIF and browser; no random runs."""
    themes = sorted(n["theme"] for n in nodes if n["kind"] == "theme")
    anchors = {}
    for i, theme in enumerate(themes):
        angle = 2 * math.pi * i / max(1, len(themes)) - math.pi / 2
        anchors[theme] = (0.5 + (0.29 * math.cos(angle) if len(themes) > 1 else 0),
                          0.5 + (0.29 * math.sin(angle) if len(themes) > 1 else 0))
    for n in nodes:
        cx, cy = anchors[n["theme"]]
        phase = int(digest(n["id"]), 16) / 0xffffffffffffffff
        radius = {"theme": 0, "object": 0.26}[n["kind"]]
        radius /= max(1, len(themes) ** 0.35)
        angle = phase * math.tau
        n["x"], n["y"] = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
    # Gentle local repulsion makes small/current graphs readable; deterministic ordering.
    for _ in range(100):
        delta = {n["id"]: [0.0, 0.0] for n in nodes}
        for i, a in enumerate(nodes):
            for b in nodes[i + 1:]:
                dx, dy = a["x"] - b["x"], (a["y"] - b["y"]) * 0.68
                dist = max(math.hypot(dx, dy), 0.001)
                minimum = 0.115 if a["kind"] == "theme" or b["kind"] == "theme" else 0.072
                if dist < minimum:
                    force = (minimum - dist) * 0.17
                    for item, sign in ((a, 1), (b, -1)):
                        if item["kind"] != "theme":
                            delta[item["id"]][0] += sign * dx / dist * force
                            delta[item["id"]][1] += sign * dy / dist * force
        for n in nodes:
            n["x"] = round(min(0.88, max(0.12, n["x"] + delta[n["id"]][0])), 6)
            n["y"] = round(min(0.88, max(0.12, n["y"] + delta[n["id"]][1])), 6)


def markdown_link(label, path):
    return f"[{label.replace('[', '').replace(']', '').replace('|', '／')}]({quote(path, safe='/')})"


def table_text(value):
    return escape(str(value), quote=False).replace("|", "&#124;").replace("\n", "<br>")


def update_readme(root: Path, graph: dict, site_url: str):
    path = root / "README.md"
    old = path.read_text(encoding="utf-8") if path.exists() else "# openJiuwen Harness 调研工作\n\n本分支归纳 openJiuwen Harness 组织内部的调研计划、报告与后续工作。\n"
    counts = graph["stats"]
    lines = [START, "", "## 调研图谱", "",
             f"[![动态调研图谱](docs/research-graph/preview.gif)]({site_url})", "",
             f"**{counts['themes']} 个调研主题 · {counts['types']} 种类型 · {counts['objects']} 项调研工作**", "",
             f"[打开交互图谱]({site_url}) · [本地页面](docs/research-graph/index.html) · [静态预览](docs/research-graph/preview.png) · [生成与维护说明](docs/research-graph-guide.md)", "",
             f"数据分支：`{graph['branch']}`。只索引已纳入 Git 的调研内容；技能资料不进入总览。", "",
             "新调研目录：`<theme>/<type>/<target>/`；主题计划：`<theme>/plan.md`。目录统一使用英文，中文正式产品名等对象名称可保留原名。", "",
             "图谱按实际关联自由布局：主题与具体调研工作连接，类型通过颜色、标签和筛选体现。", "",
             "## 主题总览", "", "| 主题 | 状态 | 计划 | 报告 | 下一步 |", "| --- | --- | --- | --- | --- |"]
    report_index = {r["id"]: r for r in graph["reports"]}
    for topic in graph["themeOverview"]:
        plan = markdown_link("调研计划", topic["planPath"]) if topic["planPath"] else "尚未建立"
        report_links = []
        for report_id in topic["reportIds"]:
            report = report_index[report_id]
            association = "；工作待关联" if report.get("associationStatus") == "pending" else ""
            report_links.append(markdown_link(report["label"], report["path"]) + f"（{table_text(report['statusLabel'])}{association}）")
        reports = "<br>".join(report_links) or "暂无报告"
        actions = "<br>".join(table_text(step) for step in topic["nextSteps"]) or "未记录"
        lines.append(f"| {table_text(topic['title'])} | {table_text(topic['statusLabel'])} | {plan} | {reports} | {actions} |")
    if not graph["themeOverview"]:
        lines.append("| 暂无调研主题 | — | 暂无计划 | 暂无报告 | 暂无下一步安排 |")
    lines += ["", "主题状态取自计划；报告旁标注其自身完整度。下一步取自计划记录，未记录时不自动推断。", "",
              "## 调研工作索引", "", "| 主题 | 类型 | 具体调研工作 |", "| --- | --- | --- |"]
    for theme in (n for n in graph["nodes"] if n["kind"] == "theme"):
        works = [n for n in graph["nodes"] if n["kind"] == "object" and n["theme"] == theme["theme"]]
        label = markdown_link(theme["label"], theme["path"])
        if not works:
            lines.append(f"| {label} | — | 暂无具体调研工作 |")
        for work in works:
            lines.append(f"| {label} | {TYPES.get(work['type'], '未标注')} | {markdown_link(work['label'], work['path'])} |")
    if not counts["themes"]:
        lines.append("| 暂无调研主题 | — | 暂无调研工作 |")
    lines += ["", f"当前纳入总览的调研报告：{counts['reports']} 份。暂无数据时显示空状态，不添加演示节点。", "", END]
    generated = "\n".join(lines)
    if old.count(START) != old.count(END) or old.count(START) > 1:
        raise ValueError("README graph markers are unbalanced or duplicated")
    if START in old:
        if old.index(START) > old.index(END):
            raise ValueError("README graph markers are reversed")
        content = old[:old.index(START)] + generated + old[old.index(END) + len(END):]
    else:
        content = old.rstrip() + "\n\n" + generated + "\n"
    write_if_changed(path, content)


def write_if_changed(path: Path, content: str):
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def generate_artifacts(root: Path, graph: dict, site_url: str, *, preview: bool = True):
    from research_graph_delivery import publish_bundle

    paths = ["docs/research-graph/graph.json", "docs/research-graph/graph-data.js",
             "docs/research-graph/.nojekyll", "README.md"]
    if preview:
        paths += ["docs/research-graph/preview.gif", "docs/research-graph/preview.png"]

    def prepare(stage_root):
        output = stage_root / "docs" / "research-graph"
        output.mkdir(parents=True)
        # README marker validation happens on the candidate, before touching any
        # public files or paying the cost of rendering the animated preview.
        update_readme(stage_root, graph, site_url)
        serialized = json.dumps(graph, ensure_ascii=False, indent=2) + "\n"
        write_if_changed(output / "graph.json", serialized)
        # Data script works over file:// without network calls or CORS handling.
        safe_json = serialized.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
        write_if_changed(output / "graph-data.js", "// Generated by scripts/research_graph.py; do not edit.\nwindow.RESEARCH_GRAPH = " + safe_json.rstrip() + ";\n")
        write_if_changed(output / ".nojekyll", "")
        if preview:
            from PIL import Image
            from research_graph_preview import render_preview
            render_preview(graph, output)
            dimensions = []
            for name, expected_format in (("preview.gif", "GIF"), ("preview.png", "PNG")):
                with Image.open(output / name) as picture:
                    if picture.format != expected_format:
                        raise ValueError(f"Unexpected preview format: {name}")
                    dimensions.append(picture.size)
                    picture.verify()
            if dimensions[0] != dimensions[1]:
                raise ValueError("GIF and PNG preview dimensions differ")
        disk_graph = json.loads((output / "graph.json").read_text(encoding="utf-8"))
        script_payload = (output / "graph-data.js").read_text(encoding="utf-8").split("window.RESEARCH_GRAPH = ", 1)[1].rstrip().removesuffix(";")
        if disk_graph != graph or json.loads(script_payload) != graph:
            raise ValueError("Graph data representations disagree")

    publish_bundle(root, paths, prepare)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--repository", default="technologyHu/research")
    parser.add_argument("--branch", help="Defaults to the current checked out Git branch")
    parser.add_argument("--site-url", default="https://technologyhu.github.io/research/")
    parser.add_argument("--no-preview", action="store_true", help="Skip GIF generation (development only)")
    args = parser.parse_args()
    root = args.root.resolve()
    branch = args.branch or subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip()
    if not branch or not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repository):
        parser.error("A named branch and owner/repository are required")
    graph = build_graph(root, args.repository, branch)
    generate_artifacts(root, graph, args.site_url, preview=not args.no_preview)
    print(json.dumps({"branch": branch, **graph["stats"], "warnings": graph["warnings"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
