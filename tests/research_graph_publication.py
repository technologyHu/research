"""Verify an actual deployment, its asset hashes, data and browser behavior."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from research_graph_publication import ASSETS
from research_graph_browser import exercise
from playwright.sync_api import sync_playwright


def fetch(url, commit):
    request = Request(url + ("&" if "?" in url else "?") + "release=" + commit,
                      headers={"Cache-Control": "no-cache", "User-Agent": "research-graph-release-check"})
    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise AssertionError(f"Unexpected status {response.status}: {url}")
        return response.read()


def verify_bundle(site_url, expected_commit, expected_fingerprint, repository):
    manifest = json.loads(fetch(urljoin(site_url, "publication.json"), expected_commit))
    assert manifest["schemaVersion"] == 1
    assert manifest["sourceCommit"] == expected_commit, "Deployment is from a different source commit"
    assert manifest["fingerprint"] == expected_fingerprint, "Deployment has a different data fingerprint"
    assert manifest["repository"] == repository and manifest["branch"] == "openjiuwen-harness"
    assert set(manifest["assets"]) == set(ASSETS), "Manifest must cover the complete published bundle"
    payloads = {}
    for name in ASSETS:
        body = fetch(urljoin(site_url, name), expected_commit)
        assert hashlib.sha256(body).hexdigest() == manifest["assets"][name], f"Published asset differs: {name}"
        payloads[name] = body
    graph = json.loads(payloads["graph.json"])
    assert graph["fingerprint"] == expected_fingerprint
    assert graph["repository"] == repository and graph["branch"] == manifest["branch"]
    return graph, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-url", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-fingerprint", required=True)
    parser.add_argument("--repository", default="technologyHu/research")
    parser.add_argument("--attempts", type=int, default=8)
    args = parser.parse_args()
    site_url = args.site_url.rstrip("/") + "/"
    if urlsplit(site_url).scheme not in {"http", "https"}:
        parser.error("An HTTP(S) deployment URL is required")
    output = ROOT / ".tmp/research-graph/publication"
    output.mkdir(parents=True, exist_ok=True)
    for attempt in range(args.attempts):
        try:
            graph, manifest = verify_bundle(site_url, args.expected_commit, args.expected_fingerprint, args.repository)
            with sync_playwright() as p:
                browser = p.chromium.launch()
                try:
                    context = browser.new_context(viewport={"width": 1440, "height": 1050}, reduced_motion="reduce",
                                                  extra_http_headers={"Cache-Control": "no-cache"})
                    page = context.new_page()
                    exercise(page, site_url + "?release=" + args.expected_commit, graph)
                    assert page.evaluate("window.RESEARCH_GRAPH.fingerprint") == args.expected_fingerprint
                    page.screenshot(path=str(output / "desktop.png"), full_page=True)
                    phone = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True,
                                                has_touch=True, reduced_motion="reduce").new_page()
                    phone.goto(site_url + "?release=" + args.expected_commit)
                    phone.wait_for_function("document.querySelector('#visible-count').textContent.includes('个匹配节点')")
                    assert phone.evaluate("window.RESEARCH_GRAPH.fingerprint") == args.expected_fingerprint
                    assert phone.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    phone.screenshot(path=str(output / "mobile.png"), full_page=True)
                finally:
                    browser.close()
            result = {"siteUrl": site_url, "sourceCommit": manifest["sourceCommit"],
                      "artifactCommit": manifest["artifactCommit"], "fingerprint": graph["fingerprint"],
                      "stats": graph["stats"], "verifiedAssets": list(ASSETS), "browserChecks": "passed"}
            (output / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result, ensure_ascii=False))
            return
        except Exception as error:
            print(f"Deployment check {attempt + 1}/{args.attempts}: {error}", flush=True)
            if attempt + 1 == args.attempts:
                raise
            time.sleep(5)


if __name__ == "__main__":
    main()
