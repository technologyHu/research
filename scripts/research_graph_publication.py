"""Write a deployment manifest tying the published bundle to a source commit."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ASSETS = ("index.html", "app.js", "style.css", "graph.json", "graph-data.js", "preview.gif", "preview.png")


def publication_manifest(site: Path, source_commit: str, artifact_commit: str) -> dict:
    if not all(re.fullmatch(r"[0-9a-f]{40}", sha) for sha in (source_commit, artifact_commit)):
        raise ValueError("Full Git commit hashes are required")
    graph = json.loads((site / "graph.json").read_text(encoding="utf-8"))
    return {"schemaVersion": 1, "repository": graph["repository"], "branch": graph["branch"],
            "sourceCommit": source_commit, "artifactCommit": artifact_commit,
            "fingerprint": graph["fingerprint"],
            "assets": {name: hashlib.sha256((site / name).read_bytes()).hexdigest() for name in ASSETS}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("docs/research-graph"))
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--artifact-commit", required=True)
    args = parser.parse_args()
    manifest = publication_manifest(args.site, args.source_commit, args.artifact_commit)
    (args.site / "publication.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"sourceCommit": manifest["sourceCommit"], "fingerprint": manifest["fingerprint"]}))


if __name__ == "__main__":
    main()
