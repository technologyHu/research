"""Browser smoke tests against the actual built graph; Playwright is optional."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import sys
import tempfile

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs" / "research-graph"
OUTPUT = ROOT / ".tmp" / "research-graph"
sys.path.insert(0, str(ROOT / "scripts"))
from research_graph import build_graph


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def exercise(page, url, expected):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(url)
    page.wait_for_function("document.querySelector('#visible-count').textContent.includes('个匹配节点')")
    node_count = len(expected["nodes"])
    require(page.locator(".result").count() == node_count, "all real nodes should be accessible")
    require(page.locator("#motion").get_attribute("aria-pressed") == "true", "reduced motion must pause animation")
    require(page.locator("#branch").inner_text() == expected["branch"], "branch should match source data")
    require(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "page must not overflow horizontally")
    require(page.locator("#show-tasks").count() == 0, "there is no extra task-node toggle")
    require(page.locator("#status-filter").count() == 0, "filters only reflect the agreed elements")
    if not node_count:
        require(page.locator("#empty").is_visible(), "empty repository has an explicit empty state")
        require("暂无调研工作" in page.locator("#detail").inner_text(), "empty details do not show sample works")
        require(page.locator("#stats").inner_text().count("0") == 3, "theme/type/work counts are all zero")
        page.locator("#search").fill("skill")
        require(page.locator(".result").count() == 0, "skill packages must not appear")
        page.locator("#clear-filters").click()
        require(not errors, "empty state must have no JavaScript errors")
        return
    page.locator("#search").fill("no-such-research-7654321")
    require(page.locator("#empty").is_visible(), "empty search should be explicit")
    require(page.locator(".result").count() == 0, "empty search should not fabricate results")
    page.locator("#clear-filters").click()
    page.locator("#type-filter").select_option("product")
    product_count = sum(n["type"] == "product" for n in expected["nodes"])
    require(page.locator(".result").count() == product_count, "type filter must match exact type")
    page.locator("#clear-filters").click()
    work = next((n for n in expected["nodes"] if n["kind"] == "object"), expected["nodes"][0])
    work_button = page.locator(f'button[data-node-id={json.dumps(work["id"], ensure_ascii=False)}]')
    require(work_button.locator(".result-label").inner_text() == work["displayLabel"],
            "node list uses the short display label")
    page.locator("#search").fill(work["displayLabel"])
    require(work_button.is_visible(), "the short display label is searchable")
    page.locator("#clear-filters").click()
    work_button.click()
    require(page.locator("#detail h2").inner_text() == work["label"], "selecting work shows details")
    require(page.locator("#detail .open-link").get_attribute("href") == work["url"], "detail opens correct branch source")
    for report_id in work.get("reportIds", []):
        report = next(r for r in expected["reports"] if r["id"] == report_id)
        report_link = page.get_by_role("link", name=f"{report['label']}（{report['statusLabel']}） ↗", exact=True)
        require(report_link.get_attribute("href") == report["url"], "details show each report's status and source link")
    if work.get("pendingReportIds"):
        require("尚未作为本项工作的交付成果" in page.locator("#detail").inner_text(), "supplemental reports must be labeled pending")
        for report_id in work["pendingReportIds"]:
            report = next(r for r in expected["reports"] if r["id"] == report_id)
            pending_link = page.get_by_role("link", name=f"待关联：{report['label']}（{report['statusLabel']}） ↗", exact=True)
            require(pending_link.get_attribute("href") == report["url"], "pending links still open the correct report")
    if page.locator("#detail .detail-links li").count():
        page.locator("#detail .detail-links button").first.click()
        require(page.locator("#detail h2").inner_text() != work["label"], "relationship click navigates to neighbor")
    page.locator("#reset").click()
    canvas = page.locator("#graph")
    before = canvas.screenshot()
    page.locator("#zoom-in").click()
    require(canvas.screenshot() != before, "zoom changes graph geometry")
    page.locator("#zoom-out").click()
    rect = canvas.bounding_box()
    page.mouse.move(rect["x"] + 25, rect["y"] + 70)
    page.mouse.down()
    page.mouse.move(rect["x"] + 100, rect["y"] + 100, steps=6)
    page.mouse.up()
    require(canvas.screenshot() != before, "dragging the background pans the graph")
    page.locator("#reset").click()
    theme = next(n for n in expected["nodes"] if n["kind"] == "theme")
    tx = rect["x"] + rect["width"] / 2 + (theme["x"] - .5) * rect["width"] * .98
    ty = rect["y"] + rect["height"] / 2 + (theme["y"] - .5) * rect["height"] * .92
    page.mouse.click(tx, ty)
    require(page.locator("#detail h2").inner_text() == theme["label"], "canvas node hit testing selects actual theme")
    before_drag = canvas.screenshot()
    page.mouse.move(tx, ty)
    page.mouse.down()
    page.mouse.move(tx + 48, ty - 33, steps=7)
    page.mouse.up()
    require(canvas.screenshot() != before_drag, "nodes are draggable")
    page.locator("#motion").click()
    require(page.locator("#motion").get_attribute("aria-pressed") == "false", "animation can resume")
    page.locator("#motion").click()
    require(page.locator("#motion").get_attribute("aria-pressed") == "true", "animation can pause")
    require(not errors, "JavaScript errors: " + "; ".join(errors))
    page.locator("#reset").click()
    return errors


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    expected = json.loads((SITE / "graph.json").read_text(encoding="utf-8"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(SITE)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={"width": 1440, "height": 1050}, reduced_motion="reduce")
            page = context.new_page()
            exercise(page, (SITE / "index.html").as_uri(), expected)
            page.screenshot(path=str(OUTPUT / "desktop.png"), full_page=True)
            exercise(page, f"http://127.0.0.1:{server.server_port}/", expected)
            page.screenshot(path=str(OUTPUT / "http.png"), full_page=True)
            mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                         is_mobile=True, has_touch=True, reduced_motion="reduce")
            phone = mobile.new_page()
            phone.goto((SITE / "index.html").as_uri())
            phone.wait_for_function("document.querySelector('#visible-count').textContent.includes('个匹配节点')")
            require(phone.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "mobile should not overflow")
            if expected["nodes"]:
                first_id = phone.locator(".result").first.get_attribute("data-node-id")
                phone.locator(".result").first.click()
                require(phone.locator("#detail h2").inner_text() == next(n for n in expected["nodes"] if n["id"] == first_id)["label"], "mobile node list works")
            else:
                require(phone.locator("#empty").is_visible(), "mobile empty state is visible")
            phone.screenshot(path=str(OUTPUT / "mobile.png"), full_page=True)
            # Nonempty interactions use an isolated test fixture served only to
            # this browser. It never enters graph.json, README or published data.
            with tempfile.TemporaryDirectory(dir=OUTPUT) as fixture_dir:
                fixture_root = Path(fixture_dir)
                plan_path = fixture_root / "evaluation" / "plan.md"
                plan_path.parent.mkdir(parents=True)
                plan_path.write_text('---\ntheme_id: evaluation\ntitle: 评估方法\n---\n# 评估方法\n## 对象与任务\n| ID | 类型／对象 | 本次目标 | 前置任务 | 状态 |\n| --- | --- | --- | --- | --- |\n| T001 | product／工具甲 | 分析工具甲 | 无 | planned |\n| T002 | paper／方法乙 | 分析方法乙 | T001 | planned |\n', encoding="utf-8")
                plan_path.write_text(plan_path.read_text(encoding="utf-8") + '\n## 成果索引\n\nT001：[主报告](product/tool/report.md)\n', encoding="utf-8")
                report_root = fixture_root / "evaluation/product/tool"
                report_root.mkdir(parents=True)
                (report_root / "report.md").write_text('# 主报告\n\n<!-- research-summary\n{"completion":"complete","update":{"sections":["## 分析"]}}\n-->\n', encoding="utf-8")
                (report_root / "details.md").write_text('# 补充报告\n\n<!-- research-summary\n{"completion":"partial"}\n-->\n', encoding="utf-8")
                (fixture_root / "themes.yaml").write_text(json.dumps({"schema_version": 1, "themes": [
                    {"id": "agent", "slug": "agent", "name": "Agent", "parent": None},
                    {"id": "agent-memory", "slug": "memory", "name": "记忆", "parent": "agent"}]}), encoding="utf-8")
                for key, title, day in (("a", "A 旧报告", "08"), ("b", "Z 新报告", "09")):
                    directory = fixture_root / f"analysis-reports/agent-memory-{key}-202611{day}-120000"
                    directory.mkdir(parents=True)
                    summary = {"report_id": "report-" + key * 32, "theme_id": "agent-memory", "completion": "complete",
                               "updated_at": f"2026-11-{day}T12:00:00+08:00"}
                    (directory / "report.md").write_text("# " + title + "\n\n<!-- research-summary\n" + json.dumps(summary) + "\n-->\n", encoding="utf-8")
                input_paths = {p.relative_to(fixture_root).as_posix() for p in fixture_root.rglob("*.md")}
                input_paths.add("themes.yaml")
                fixture = build_graph(fixture_root, expected["repository"], expected["branch"], input_paths=input_paths)
                page.route("**/graph-data.js", lambda route: route.fulfill(content_type="application/javascript", body="window.RESEARCH_GRAPH = " + json.dumps(fixture)))
                exercise(page, f"http://127.0.0.1:{server.server_port}/", fixture)
                result_ids = page.locator(".result").evaluate_all("items => items.map(item => item.dataset.nodeId)")
                require(result_ids.index("work:report-" + "b" * 32) < result_ids.index("work:report-" + "a" * 32),
                        "same-theme reports follow revision time rather than title order")
                require(result_ids.index("work:report-" + "a" * 32) < result_ids.index("theme:evaluation"),
                        "theme nodes and works stay together in the results list")
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print("Browser checks passed: file://, HTTP, search, filters, details, relationships, zoom, pan, node drag, motion and mobile.")


if __name__ == "__main__":
    main()
