# ai-generated: 100% - Codex wrote independent edge-case tests from CI-SPEC P-14 to P-23.
"""Regression tests for the published matching contract; no third-party modules."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bakeoff import confusion_matrix


ROOT = "hidden-set"
FILE = ROOT + "/app.py"


def defect(identifier="D1", cls="injection", start=5, end=8, file=FILE):
    return {"id": identifier, "file": file, "class": cls, "start_line": start, "end_line": end}


def finding(rule="r", file=FILE, start=5, end=None, cls="injection", **extra):
    physical = {"artifactLocation": {"uri": file}}
    if start is not None:
        physical["region"] = {"startLine": start}
        if end is not None:
            physical["region"]["endLine"] = end
    result = {"ruleId": rule, "locations": [{"physicalLocation": physical}]}
    if cls is not None:
        result["properties"] = {"class": cls}
    result.update(extra)
    return result


def run(results=None, name="Example", rules=None):
    return {"tool": {"driver": {"name": name, "rules": rules or []}}, "results": results or []}


def matrix(defects, *runs):
    return confusion_matrix({"set": ROOT, "defects": defects}, [{"runs": list(runs)}])


class BakeoffTests(unittest.TestCase):
    def assert_counts(self, actual, tp, fp, fn, tool="example"):
        self.assertEqual((actual["tools"][tool]["tp"], actual["tools"][tool]["fp"], actual["tools"][tool]["fn"]), (tp, fp, fn))

    def test_multiple_defects_found_once_and_overlapping_ranges(self):
        labels = [defect(), defect("D2", start=8, end=10), defect("D3", start=11, end=11)]
        self.assert_counts(matrix(labels, run([finding(start=8), finding(start=8)])), 2, 0, 1)

    def test_tool_names_and_merging_across_files(self):
        names = [" Semgrep ", "Semgrep OSS", "semgrep CE", "Semgrep Community Edition", "Semgrep Pro"]
        documents = [{"runs": [run([finding()], name)]} for name in names]
        documents += [{"runs": [run(name="AI / Reviewer!"), run(name="TrIvY"), run(name=" Grype "), run(name="OSV-Scanner")]}]
        actual = confusion_matrix({"set": ROOT, "defects": [defect()]}, documents)
        self.assertEqual(set(actual["tools"]), {"semgrep", "ai-reviewer", "trivy", "grype", "osv-scanner"})
        self.assert_counts(actual, 1, 0, 0, "semgrep")

    def test_unknown_names_and_nonobject_runs(self):
        runs = [None, 4, [], "bad", {}, {"tool": None}, {"tool": {"driver": []}}]
        runs += [run(name=name) for name in [None, 7, {}, [], "!!!", "   "]]
        actual = matrix([defect()], *runs)
        self.assertEqual(set(actual["tools"]), {"unknown"})
        self.assert_counts(actual, 0, 0, 1, "unknown")

    def test_kind_and_suppression_filtering(self):
        for kind in [None, "fail"]:
            for suppression in [None, [], {}, False, 0, ""]:
                with self.subTest(kind=kind, suppression=suppression):
                    self.assert_counts(matrix([defect()], run([finding(kind=kind, suppressions=suppression)])), 1, 0, 0)
        for kind in ["FAIL", "pass", "review", False, 0, []]:
            self.assert_counts(matrix([defect()], run([finding(kind=kind)])), 0, 0, 1)
        for suppression in [[None], [False], {"status": "rejected"}, "false", 1, True]:
            self.assert_counts(matrix([defect()], run([finding(suppressions=suppression)])), 0, 0, 1)

    def test_only_first_location_and_required_uri(self):
        good = finding()
        for first in [None, 2, {}, {"physicalLocation": None}, {"physicalLocation": {"artifactLocation": {"uri": 3}}}]:
            result = finding(locations=[first, good["locations"][0]])
            self.assert_counts(matrix([defect()], run([result])), 0, 0, 1)
        for locations in [None, {}, "wrong", []]:
            self.assert_counts(matrix([defect()], run([finding(locations=locations)])), 0, 0, 1)
        self.assert_counts(matrix([defect()], run([finding(file="")])), 0, 0, 1)

    def test_nonarray_results_and_nonobject_results(self):
        for results in [None, {}, "wrong", [None, [], 2, "wrong"]]:
            self.assert_counts(matrix([defect()], {"tool": {"driver": {"name": "Example"}}, "results": results}), 0, 0, 1)
        self.assertEqual(confusion_matrix({"set": ROOT, "defects": []}, [{"runs": {}}, {"runs": None}])["tools"], {})

    def test_path_decoding_last_root_and_exact_components(self):
        for path in [FILE, "./" + FILE, "/src/" + FILE, "FiLe:///src/" + FILE, "././" + FILE,
                     "elsewhere/hidden-set/old/" + FILE, "hidden%2Dset%2Fapp.py"]:
            with self.subTest(path=path):
                self.assert_counts(matrix([defect()], run([finding(file=path)])), 1, 0, 0)
        for path in ["HIDDEN-SET/app.py", "prefix-hidden-set/app.py", "hidden-set2/app.py", "hidden-set\\app.py"]:
            self.assert_counts(matrix([defect()], run([finding(file=path)])), 0, 0, 1)
        self.assert_counts(matrix([defect(file=ROOT + "/bad%zz.py")], run([finding(file=ROOT + "/bad%zz.py")])), 1, 0, 0)
        self.assert_counts(matrix([defect(file=ROOT + "/é.py")], run([finding(file=ROOT + "/%C3%A9.py")])), 1, 0, 0)

    def test_line_types_and_end_defaults(self):
        for start in [None, 0, -1, True, 5.0, "5", [], {}]:
            with self.subTest(start=start):
                self.assert_counts(matrix([defect()], run([finding(start=start)])), 0, 1, 1)
        for end in [None, 0, 4, True, 8.0, "8", [], {}]:
            self.assert_counts(matrix([defect()], run([finding(start=5, end=end)])), 1, 0, 0)
            self.assert_counts(matrix([defect(start=6)], run([finding(start=5, end=end)])), 0, 1, 1)
        self.assert_counts(matrix([defect()], run([finding(start=1, end=5)])), 1, 0, 0)
        self.assert_counts(matrix([defect()], run([finding(start=9)])), 0, 1, 1)

    def test_explicit_class_precedes_tool_and_cwes(self):
        item = finding(cls="injection", properties={"class": "injection", "tags": ["CWE-798"]})
        self.assert_counts(matrix([defect(), defect("S", "secret")], run([item], "gitleaks")), 1, 0, 1, "gitleaks")
        for invalid in [None, "INJECTION", "other", [], {}]:
            item = finding(properties={"class": invalid})
            self.assert_counts(matrix([defect(cls="secret")], run([item], "gitleaks")), 1, 0, 0, "gitleaks")

    def test_trivy_rule_tags_are_whole_untrimmed_and_override_cwes(self):
        item = finding(cls=None, properties={"tags": ["CWE-89"]})
        rules = [{"id": "r", "properties": {"tags": ["SECRET", "Misconfiguration", "CWE-918"]}}]
        labels = [defect("S", "secret"), defect("M", "misconfiguration"), defect("I")]
        self.assert_counts(matrix(labels, run([item], "trivy", rules)), 2, 0, 1, "trivy")
        for tags in [[" secret "], ["vulnerability something"], "secret", [None, 3]]:
            rules = [{"id": "r", "properties": {"tags": tags}}]
            self.assert_counts(matrix([defect()], run([item], "trivy", rules)), 1, 0, 0, "trivy")

    def test_first_rule_id_wins_and_rule_index_is_ignored(self):
        rules = [{"id": "r", "properties": {"tags": ["CWE-22"]}}, {"id": "r", "properties": {"tags": ["CWE-89"]}}]
        self.assert_counts(matrix([defect()], run([finding(cls=None, ruleIndex=1)], rules=rules)), 0, 1, 1)
        item = finding(rule="missing", cls=None, ruleIndex=0)
        self.assert_counts(matrix([defect(cls="path-traversal")], run([item], rules=rules)), 0, 1, 1)

    def test_cwe_boundaries_case_zeroes_and_multiple_classes(self):
        for tag in ["CWE-89: SQL", "external/cwe/cwe-089", "éCWE-00089", "_CWE-89", "CWE-89x",
                    "KCWE-89", "İCWE-89", "ıCWE-89", "ſCWE-89"]:
            self.assert_counts(matrix([defect()], run([finding(properties={"tags": [tag]})])), 1, 0, 0)
        for tag in ["XCWE-89", "9CWE-89", "CWE 89", "CWE-890", "CWE-８９"]:
            self.assert_counts(matrix([defect()], run([finding(properties={"tags": [tag]})])), 0, 1, 1)
        item = finding(properties={"tags": ["CWE-89 and cwe-918"]})
        rules = [{"id": "r", "properties": {"tags": ["CWE-22"]}}]
        labels = [defect(), defect("S", "ssrf"), defect("P", "path-traversal")]
        self.assert_counts(matrix(labels, run([item], rules=rules)), 3, 0, 0)

    def test_every_course_class_cwe(self):
        cases = {"secret": 798, "injection": 1336, "deserialization": 502, "weak-crypto": 916,
                 "insecure-transport": 757, "path-traversal": 73, "ssrf": 918,
                 "misconfiguration": 1188, "access-control": 863}
        for cls, cwe in cases.items():
            with self.subTest(cls=cls):
                item = finding(properties={"tags": [f"CWE-{cwe}"]})
                self.assert_counts(matrix([defect(cls=cls)], run([item])), 1, 0, 0)
        item = finding(properties={"tags": ["CWE-1395"]}, message={"text": "Some_Package"}, start=None)
        label = {"id": "D", "class": "vulnerable-dependency", "file": FILE, "package": "Some-Package"}
        self.assert_counts(matrix([label], run([item])), 1, 0, 0)

    def test_dependency_matching_pep503_tokens_without_lines(self):
        label = {"id": "D", "class": "vulnerable-dependency", "file": FILE, "package": "My...Package"}
        for name in ["grype", "osv-scanner"]:
            for text in ["Package: my_package.", "Uses 'MY--PACKAGE@1.0'.", "__my.package__"]:
                self.assert_counts(matrix([label], run([finding(cls=None, start=None, message={"text": text})], name)), 1, 0, 0, name)
            for message in [{"text": "my-package-extra"}, {"markdown": "my-package"}, {"text": None}, {"id": "my-package"}, {"text": 123}]:
                self.assert_counts(matrix([label], run([finding(cls=None, message=message)], name)), 0, 1, 1, name)

    def test_fp_dedup_uses_normalized_lines_and_missing_rule_marker(self):
        items = [finding(rule="r", start=9), finding(rule="r", start=9, end=9), finding(rule="r", start=9, end=8),
                 finding(rule="r", start=None), finding(rule="r", start=False),
                 finding(rule=None, start=None), finding(rule=9, start=None), finding(rule="", start=None)]
        self.assert_counts(matrix([defect()], run(items)), 0, 4, 1)

    def test_matching_result_is_removed_before_fp_dedup(self):
        # Same key, different class: one TP and one unmatched result still yields an FP.
        matching = finding()
        unmatched = finding(cls="ssrf")
        self.assert_counts(matrix([defect()], run([matching, unmatched, copy.deepcopy(unmatched)])), 1, 1, 0)

    def test_empty_labels_and_absent_predictions(self):
        empty = matrix([], run())["tools"]["example"]
        self.assertEqual(empty, {"tp": 0, "fp": 0, "fn": 0, "precision": None, "recall": None, "f1": None})
        only_fp = matrix([], run([finding()]))["tools"]["example"]
        self.assertEqual(only_fp, {"tp": 0, "fp": 1, "fn": 0, "precision": 0.0, "recall": None, "f1": 0.0})
        no_predictions = matrix([defect()], run())["tools"]["example"]
        self.assertEqual(no_predictions, {"tp": 0, "fp": 0, "fn": 1, "precision": None, "recall": 0.0, "f1": 0.0})

    def test_f1_calculated_from_counts(self):
        labels = [defect(str(i), start=i, end=i) for i in range(1, 10)]
        actual = matrix(labels, run([finding(start=i) for i in range(1, 6)] + [finding(start=20), finding(start=21)]))
        self.assertEqual(actual["tools"]["example"], {"tp": 5, "fp": 2, "fn": 4, "precision": 0.7143, "recall": 0.5556, "f1": 0.625})

    def test_cli_standard_library_and_read_only_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            labels = directory / "labels.json"
            sarif = directory / "scanner.sarif"
            labels.write_text(json.dumps({"set": ROOT, "defects": [defect()]}), encoding="utf-8")
            sarif.write_text(json.dumps({"version": "2.1.0", "runs": [run([finding()])]}), encoding="utf-8")
            before = (labels.read_bytes(), sarif.read_bytes())
            process = subprocess.run([sys.executable, "-S", "-E", str(Path(__file__).resolve().parents[1] / "bakeoff.py"),
                                      "--labels", str(labels), str(sarif)], capture_output=True, text=True, timeout=60)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assert_counts(json.loads(process.stdout), 1, 0, 0)
            self.assertEqual(before, (labels.read_bytes(), sarif.read_bytes()))


if __name__ == "__main__":
    unittest.main()
