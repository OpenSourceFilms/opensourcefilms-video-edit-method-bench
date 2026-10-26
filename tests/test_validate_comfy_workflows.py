"""Offline regression checks for method-bench ComfyUI graph validation."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"validation/validate_comfy_workflows.py"
spec=importlib.util.spec_from_file_location("bench_validator",SRC)
validator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

class MethodBenchGraphTests(unittest.TestCase):
    def check(self,doc):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"test_graph.json"
            path.write_text(json.dumps(doc),encoding="utf-8")
            return validator.validate(path)

    def test_api_graph_counted_and_validated(self):
        doc={"1":{"class_type":"LoadImage","inputs":{"image":"synthetic.png"}},
             "2":{"class_type":"SaveImage","inputs":{"images":["1",0]}}}
        got=self.check(doc)
        self.assertTrue(got["ok"],got["errors"])
        self.assertEqual(got["graphs"],1)
        self.assertEqual(got.get("format"),"api")

    def test_namespaced_api_ids_are_legitimate(self):
        doc={"489:311":{"class_type":"Custom","inputs":{}},
             "2":{"class_type":"Save","inputs":{"image":["489:311",0]}}}
        got=self.check(doc)
        self.assertTrue(got["ok"],got["errors"])
        self.assertEqual(got["format"],"api")
        self.assertEqual(got["graphs"],1)

    def test_api_missing_upstream_is_not_success(self):
        doc={"2":{"class_type":"SaveImage","inputs":{"images":["888",0]}}}
        got=self.check(doc)
        self.assertFalse(got["ok"])
        self.assertEqual(got["graphs"],1)
        self.assertIn("missing", " ".join(got["errors"]).lower())

    def test_api_bad_slot_is_not_success(self):
        doc={"1":{"class_type":"LoadImage","inputs":{}},
             "2":{"class_type":"SaveImage","inputs":{"images":["1",True]}}}
        got=self.check(doc)
        self.assertFalse(got["ok"])

    def test_api_invalid_input_shape(self):
        doc={"1":{"class_type":"Source","inputs":[]}}
        got=self.check(doc)
        self.assertFalse(got["ok"])

    def test_api_invalid_class_type(self):
        doc={"1":{"class_type":"","inputs":{}}}
        got=self.check(doc)
        self.assertFalse(got["ok"])

    def test_zero_graph_is_not_success(self):
        for doc in ({},{ "unrelated":"file" },{"nodes":[],"links":None}):
            with self.subTest(doc=doc):
                got=self.check(doc)
                self.assertFalse(got["ok"])

    def test_simple_ui_graph_valid(self):
        doc={"nodes":[{"id":1,"type":"Source","inputs":[],"outputs":[{"links":[1]}]},
                      {"id":2,"type":"Sink","inputs":[{"link":1}],"outputs":[]}],
             "links":[[1,1,0,2,0,"IMAGE"]]}
        got=self.check(doc)
        self.assertTrue(got["ok"],got["errors"])
        self.assertEqual(got["graphs"],1)

    def test_nested_ui_graphs_counted(self):
        doc={"examples":[{"nodes":[],"links":[]},{"nodes":[],"links":[]}]}
        got=self.check(doc)
        self.assertTrue(got["ok"],got["errors"])
        self.assertEqual(got["graphs"],2)

    def test_invalid_ui_link_missing_node(self):
        doc={"nodes":[{"id":1,"type":"Source","inputs":[],"outputs":[{"links":[] }]}],
             "links":[[1,1,0,99,0,"IMAGE"]]}
        self.assertFalse(self.check(doc)["ok"])

    def test_invalid_ui_unhashable_link_diagnostic(self):
        doc={"nodes":[{"id":1,"type":"Source","inputs":[],"outputs":[{"links":[] }]}],
             "links":[[[1],1,0,1,0,"IMAGE"]]}
        got=self.check(doc)
        self.assertFalse(got["ok"])

    def test_invalid_ui_boolean_ids_not_accepted(self):
        doc={"nodes":[{"id":True,"type":"Source","inputs":[],"outputs":[]}],"links":[]}
        self.assertFalse(self.check(doc)["ok"])

    def test_unreadable_json_reports_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"bad.json"
            path.write_text("{oops")
            got=validator.validate(path)
            self.assertFalse(got["ok"])


if __name__=="__main__":
    unittest.main()
