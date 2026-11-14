# ai-generated: 100% - Codex implemented the published P-14 to P-23 matching rules and tests.
"""Compute a defect-level scanner matrix using the Lab 5 CI-SPEC rules.

Only the standard library is used; run with Python 3.13 and ``-S -E``.
Inputs are read only. Results outside the labelled set belong in TRIAGE.md,
not in this matrix.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import unquote


CLASS_CWES = {
    "secret": {259, 260, 321, 798},
    "injection": {74, 77, 78, 79, 80, 88, 89, 90, 91, 94, 95, 96, 611, 776, 917, 943, 1336},
    "deserialization": {502},
    "weak-crypto": {261, 326, 327, 328, 330, 331, 338, 759, 760, 916},
    "insecure-transport": {295, 297, 319, 322, 757},
    "path-traversal": {22, 23, 35, 36, 73},
    "ssrf": {918},
    "vulnerable-dependency": {937, 1035, 1104, 1395},
    "misconfiguration": {16, 215, 250, 489, 668, 732, 1188},
    "access-control": {284, 285, 639, 862, 863},
}
CWE_CLASSES = {str(cwe): cls for cls, cwes in CLASS_CWES.items() for cwe in cwes}
CWE_PATTERN = re.compile(r"(?<![A-Za-z0-9])CWE-([0-9]+)", re.IGNORECASE | re.ASCII)
PACKAGE_PATTERN = re.compile(r"[A-Za-z0-9._-]+")
SEMGREP_NAMES = {
    "semgrep", "semgrep oss", "semgrep ce", "semgrep community edition", "semgrep pro",
}
TRIVY_CLASSES = {
    "vulnerability": "vulnerable-dependency",
    "secret": "secret",
    "misconfiguration": "misconfiguration",
}


def _object(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _array(value: object) -> list:
    return value if isinstance(value, list) else []


def _tool_id(driver: dict) -> str:
    name = driver.get("name")
    if not isinstance(name, str):
        return "unknown"
    name = name.strip().lower()
    if name in SEMGREP_NAMES:
        return "semgrep"
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-") or "unknown"


def _set_file(uri: str, root: str) -> str | None:
    path = unquote(uri)
    if path[:7].lower() == "file://":
        path = path[7:]
    if path.startswith("./"):
        path = path[2:]
    components = path.split("/")
    for index in range(len(components) - 1, -1, -1):
        if components[index] == root:
            return "/".join(components[index:])
    return None


def _lines(physical: dict) -> tuple[int | None, int | None]:
    region = _object(physical.get("region"))
    start = region.get("startLine")
    # bool is an int subclass in Python, but is not a JSON integer (P-18).
    if type(start) is not int or start < 1:
        return None, None
    end = region.get("endLine")
    if type(end) is not int or end < start:
        end = start
    return start, end


def _tags(item: dict) -> list[str]:
    tags = _array(_object(item.get("properties")).get("tags"))
    return [tag for tag in tags if isinstance(tag, str)]


def _classes(result: dict, rule: dict, tool: str) -> set[str]:
    explicit = _object(result.get("properties")).get("class")
    if isinstance(explicit, str) and explicit in CLASS_CWES:
        return {explicit}
    if tool == "gitleaks":
        return {"secret"}
    if tool in {"grype", "osv-scanner"}:
        return {"vulnerable-dependency"}
    rule_tags = _tags(rule)
    if tool == "trivy":
        classes = {TRIVY_CLASSES[tag.lower()] for tag in rule_tags if tag.lower() in TRIVY_CLASSES}
        if classes:
            return classes
    classes = set()
    for tag in _tags(result) + rule_tags:
        for match in CWE_PATTERN.finditer(tag):
            # String normalization also handles arbitrarily many leading zeros.
            cwe = match.group(1).lstrip("0") or "0"
            if cwe in CWE_CLASSES:
                classes.add(CWE_CLASSES[cwe])
    return classes or {"other"}


def _package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.lower())


def _packages(result: dict) -> set[str]:
    message = _object(result.get("message")).get("text")
    if not isinstance(message, str):
        return set()
    return {
        _package_name(token.strip("._-"))
        for token in PACKAGE_PATTERN.findall(message)
        if token.strip("._-")
    }


def confusion_matrix(labels: dict, sarif_documents: list[dict]) -> dict:
    """Return P-21 counts and P-22 scores for all tool runs in the inputs."""
    root = labels["set"]
    defects = labels["defects"]
    by_file: dict[str, list[dict]] = {}
    for defect in defects:
        by_file.setdefault(defect["file"], []).append(defect)
    found: dict[str, set[str]] = {}
    false_positives: dict[str, set[tuple]] = {}

    for document in sarif_documents:
        for run in _array(_object(document).get("runs")):
            if not isinstance(run, dict):
                continue
            driver = _object(_object(run.get("tool")).get("driver"))
            tool = _tool_id(driver)
            found.setdefault(tool, set())
            false_positives.setdefault(tool, set())
            rules = {}
            for rule in _array(driver.get("rules")):
                if isinstance(rule, dict) and isinstance(rule.get("id"), str):
                    rules.setdefault(rule["id"], rule)  # P-19: first identical id wins.

            for result in _array(run.get("results")):
                if not isinstance(result, dict):
                    continue
                if result.get("kind") not in (None, "fail") or result.get("suppressions"):
                    continue
                locations = _array(result.get("locations"))
                if not locations:
                    continue
                physical = _object(_object(locations[0]).get("physicalLocation"))
                uri = _object(physical.get("artifactLocation")).get("uri")
                if not isinstance(uri, str) or not uri:
                    continue
                file = _set_file(uri, root)
                if file is None:
                    continue
                start, end = _lines(physical)
                rule_id = result.get("ruleId")
                if not isinstance(rule_id, str):
                    rule_id = None
                classes = _classes(result, rules.get(rule_id, {}), tool)
                packages = _packages(result) if "vulnerable-dependency" in classes else set()
                matches = set()
                for defect in by_file.get(file, []):
                    cls = defect["class"]
                    if cls not in classes:
                        continue
                    if cls == "vulnerable-dependency":
                        matched = _package_name(defect["package"]) in packages
                    else:
                        matched = start is not None and start <= defect["end_line"] and defect["start_line"] <= end
                    if matched:
                        matches.add(defect["id"])
                if matches:
                    found[tool].update(matches)
                else:
                    false_positives[tool].add((rule_id, file, start, end))

    def score(numerator: int, denominator: int) -> float | None:
        return round(numerator / denominator, 4) if denominator else None

    tools = {}
    for tool in sorted(found):
        tp = len(found[tool])
        fp = len(false_positives[tool])
        fn = len(defects) - tp
        tools[tool] = {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": score(tp, tp + fp),
            "recall": score(tp, tp + fn),
            "f1": score(2 * tp, 2 * tp + fp + fn),
        }
    return {"set": root, "defects": len(defects), "tools": tools}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Per-tool defect matrix of SARIF against Lab 5 labels")
    parser.add_argument("--labels", required=True, help="the labels JSON file")
    parser.add_argument("sarif", nargs="+", help="SARIF 2.1.0 files")
    args = parser.parse_args(argv)
    with open(args.labels, encoding="utf-8-sig") as stream:
        labels = json.load(stream)
    documents = []
    for path in args.sarif:
        with open(path, encoding="utf-8-sig") as stream:
            documents.append(json.load(stream))
    json.dump(confusion_matrix(labels, documents), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
