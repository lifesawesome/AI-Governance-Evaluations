import ast
import copy
import inspect
import json
import math
import os
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd
from azure.ai.projects.models import EvaluatorVersion
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError


NOTEBOOK = (
    Path(__file__).resolve().parents[1]
    / "labs"
    / "lab-04-portal-sdk-custom"
    / "lab-04-portal-sdk-custom.ipynb"
)
CELLS = json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
SOURCES = {
    cell["id"]: "".join(cell["source"])
    for cell in CELLS
    if cell["cell_type"] == "code"
}


def notebook_functions():
    namespace = {
        "ResourceNotFoundError": ResourceNotFoundError,
        "math": math,
        "os": os,
        "pd": pd,
        "time": time,
    }
    for cell_id, source in SOURCES.items():
        tree = ast.parse(source, filename=f"{NOTEBOOK}:{cell_id}")
        definitions = [
            node for node in tree.body if isinstance(node, ast.FunctionDef)
        ]
        exec(
            compile(ast.Module(body=definitions, type_ignores=[]), str(NOTEBOOK), "exec"),
            namespace,
        )
    return namespace


class Lab04Tests(unittest.TestCase):
    def setUp(self):
        self.ns = notebook_functions()
        tree = ast.parse(SOURCES["69df68ca"])
        tree.body = [node for node in tree.body if isinstance(node, ast.Assign)]
        exec(compile(tree, str(NOTEBOOK), "exec"), self.ns)
        code_source = ast.get_source_segment(
            SOURCES["5c687977"], ast.parse(SOURCES["5c687977"]).body[0]
        )
        setup = SOURCES["b6774f06"].split('print("Existing custom evaluator catalog:")')[0]
        with patch.dict("os.environ", {}, clear=True), patch.object(
            inspect, "getsource", return_value=code_source
        ):
            exec(compile(setup, str(NOTEBOOK), "exec"), self.ns)

    def evaluator(self, spec, version="1"):
        return EvaluatorVersion({**spec, "version": version})

    def test_all_cells_compile_and_ids_are_unique(self):
        ids = [cell["id"] for cell in CELLS]
        self.assertEqual(len(ids), len(set(ids)))
        for cell_id, source in SOURCES.items():
            compile(source, f"{NOTEBOOK}:{cell_id}", "exec")

    def test_reuses_same_agent_without_creating_a_version(self):
        project = Mock()
        existing = SimpleNamespace(name="contoso-support-agent-eval", version="1")
        project.agents.get.return_value.versions.latest = existing
        self.assertIs(self.ns["resolve_agent"](project, existing.name), existing)
        project.agents.create_version.assert_not_called()
        project.agents.get_version.return_value = existing
        self.assertIs(self.ns["resolve_agent"](project, existing.name, "1"), existing)
        project.agents.get_version.assert_called_once_with(
            agent_name=existing.name, agent_version="1"
        )

    def test_missing_agent_does_not_create_replacement(self):
        project = Mock()
        project.agents.get.side_effect = ResourceNotFoundError("missing")
        with self.assertRaisesRegex(RuntimeError, "no agent was created"):
            self.ns["resolve_agent"](project, "missing")
        project.agents.create_version.assert_not_called()

    def test_registers_only_missing_evaluators(self):
        for spec_key in ("code_spec", "tone_spec"):
            spec = self.ns[spec_key]
            for missing in ([], ResourceNotFoundError("missing")):
                catalog = Mock()
                if isinstance(missing, Exception):
                    catalog.list_versions.side_effect = missing
                else:
                    catalog.list_versions.return_value = missing
                catalog.create_version.return_value = self.evaluator(spec)
                result = self.ns["reuse_or_register_evaluator"](catalog, spec)
                self.assertEqual(result.version, "1")
                catalog.create_version.assert_called_once_with(
                    name=spec["name"], evaluator_version=spec
                )

    def test_reuses_matching_latest_or_pinned_evaluator(self):
        spec = self.ns["tone_spec"]
        catalog = Mock()
        old, latest = self.evaluator(spec, "2"), self.evaluator(spec, "10")
        catalog.list_versions.return_value = [latest, old]
        self.assertIs(
            self.ns["reuse_or_register_evaluator"](catalog, spec), latest
        )
        catalog.get_version.return_value = old
        self.assertIs(
            self.ns["reuse_or_register_evaluator"](catalog, spec, "2"), old
        )
        catalog.create_version.assert_not_called()

    def test_incompatible_definition_is_not_overwritten(self):
        spec = self.ns["tone_spec"]
        for field in ("prompt_text", "data_schema", "metrics", "init_parameters"):
            changed = copy.deepcopy(spec)
            changed["definition"][field] = (
                "Different rubric" if field == "prompt_text" else {}
            )
            catalog = Mock()
            catalog.list_versions.return_value = [self.evaluator(changed)]
            with self.assertRaisesRegex(ValueError, field):
                self.ns["reuse_or_register_evaluator"](catalog, spec)
            catalog.create_version.assert_not_called()

    def test_auth_errors_and_missing_pinned_versions_propagate(self):
        spec = self.ns["code_spec"]
        catalog = Mock()
        catalog.list_versions.side_effect = HttpResponseError("Forbidden")
        with self.assertRaises(HttpResponseError):
            self.ns["reuse_or_register_evaluator"](catalog, spec)
        catalog.create_version.assert_not_called()
        catalog.get_version.side_effect = ResourceNotFoundError("missing version")
        with self.assertRaises(ResourceNotFoundError):
            self.ns["reuse_or_register_evaluator"](catalog, spec, "99")
        catalog.create_version.assert_not_called()

    def test_cloud_code_scores_real_response_and_preserves_threshold(self):
        scope = {}
        exec(self.ns["code_text"], scope)
        grade = scope["grade"]
        for response in (
            "",
            "Yes.",
            "Employees receive 20 days of annual leave. Contact HR for details.",
            "as an AI, I cannot help. I'm just a language model",
            "x" * 2001,
        ):
            item = {
                "query": "salary",
                "sample": {"output_text": response},
                "ground_truth": "This must never be evaluated as the response.",
            }
            expected = self.ns["response_quality_checker"](response, "salary")
            score = grade({}, item)
            self.assertEqual(score, (expected["score"] - 1) / 4)
            self.assertEqual(score >= 0.75, expected["label"] == "pass")
            self.assertTrue(0 <= score <= 1)
        with self.assertRaises(KeyError):
            grade({}, {"query": "test", "ground_truth": "not a response"})
        with self.assertRaises(TypeError):
            grade({}, {"query": "test", "sample": {"output_text": None}})

    def test_cloud_prompt_uses_foundry_contract(self):
        prompt = self.ns["tone_prompt"]
        for required in ("{{query}}", "{{response}}", '"result":', '"reason":'):
            self.assertIn(required, prompt)
        self.assertNotIn('"score":', prompt)
        self.assertNotIn('"reasoning":', prompt)

    def output_item(self, item_id=0):
        return {
            "datasource_item_id": item_id,
            "datasource_item": {"query": "Question", "category": "happy_path"},
            "sample": {"output": [{"content": "Actual generated answer"}], "error": None},
            "results": [
                {"name": "Professional Tone", "score": 3, "passed": False, "reason": "Too casual"}
            ],
        }

    def test_summary_uses_actual_scores_and_retains_failures(self):
        run = SimpleNamespace(status="completed", per_testing_criteria_results=[])
        items = [self.output_item(), self.output_item(1)]
        items[1]["datasource_item"] = {"item": items[1]["datasource_item"]}
        items[1]["results"][0].update(score=5, passed=True)
        frame, scores, issues = self.ns["summarize_results"](
            items, [{"name": "Professional Tone"}], 2, run
        )
        self.assertEqual(
            scores["Professional Tone"],
            {
                "mean_score": 4.0, "accuracy": 0.5, "defect_count": 1,
                "sample_count": 2, "total_count": 2, "result_count": 2, "generation_error_count": 0,
                "errored_count": 0, "skipped_count": 0,
            },
        )
        self.assertEqual(issues, [])
        self.assertEqual(frame.iloc[0]["reason"], "Too casual")
        self.assertEqual(frame.iloc[0]["response"], "Actual generated answer")

    def test_malformed_results_raise_explicit_errors(self):
        run = SimpleNamespace(status="completed", per_testing_criteria_results=[])
        criterion = [{"name": "Professional Tone"}]
        mutations = [
            lambda item: item["results"].clear(),
            lambda item: item["results"][0].update(score=None),
            lambda item: item["results"][0].update(score=float("nan")),
            lambda item: item["results"][0].update(score=True),
            lambda item: item["results"][0].update(passed=None),
        ]
        for mutate in mutations:
            item = self.output_item()
            mutate(item)
            with self.assertRaises(ValueError):
                self.ns["summarize_results"]([item], criterion, 1, run)
        with self.assertRaises(ValueError):
            self.ns["summarize_results"]([], criterion, 1, run)
        item = self.output_item()
        with self.assertRaises(ValueError):
            self.ns["summarize_results"]([item, item], criterion, 2, run)

    def test_service_errors_are_retained_and_invalidate_comparison(self):
        run = SimpleNamespace(status="completed", per_testing_criteria_results=[])
        criteria = [{"name": "Professional Tone"}]
        for status in ("error", "errored", "skipped"):
            item = self.output_item()
            item["results"][0].update(score=None, passed=None, status=status)
            frame, scores, issues = self.ns["summarize_results"](
                [item], criteria, 1, run
            )
            self.assertTrue(issues)
            self.assertEqual(len(frame), 1)
            self.assertFalse(frame.iloc[0]["usable_for_comparison"])
            self.assertIsNone(scores["Professional Tone"]["mean_score"])
            self.assertIsNone(scores["Professional Tone"]["accuracy"])
            self.assertEqual(scores["Professional Tone"]["sample_count"], 0)
            self.assertEqual(scores["Professional Tone"]["total_count"], 1)
        for counter in ("errored", "skipped"):
            run.per_testing_criteria_results = [
                SimpleNamespace(testing_criteria="Professional Tone", **{counter: 1})
            ]
            _, _, issues = self.ns["summarize_results"](
                [self.output_item()], criteria, 1, run
            )
            self.assertTrue(issues)

    def test_filtered_generation_excludes_all_reported_scores_without_dropping_case(self):
        run = SimpleNamespace(status="completed", per_testing_criteria_results=[])
        item = self.output_item()
        item["sample"].update(error={"code": "content_filtered"}, output=[])
        item["results"][0].update(score=None, passed=None, status="completed")
        frame, scores, issues = self.ns["summarize_results"](
            [item], [{"name": "Professional Tone"}], 1, run
        )
        self.assertTrue(issues)
        self.assertEqual(len(frame), 1)
        self.assertIsNone(frame.iloc[0]["score"])
        self.assertEqual(frame.iloc[0]["generation_error"]["code"], "content_filtered")
        self.assertFalse(frame.iloc[0]["usable_for_comparison"])
        self.assertIsNone(scores["Professional Tone"]["accuracy"])
        self.assertEqual(scores["Professional Tone"]["generation_error_count"], 1)

    def test_duplicate_service_results_are_retained_but_not_double_counted(self):
        run = SimpleNamespace(status="completed", per_testing_criteria_results=[])
        item = self.output_item()
        item["results"].append({
            "name": "Professional Tone", "status": "error",
            "score": None, "passed": None, "sample": {"error": {"code": "FAILED_EXECUTION"}},
        })
        frame, scores, issues = self.ns["summarize_results"](
            [item], [{"name": "Professional Tone"}], 1, run
        )
        self.assertTrue(issues)
        self.assertEqual(len(frame), 2)
        self.assertEqual(scores["Professional Tone"]["total_count"], 1)
        self.assertEqual(scores["Professional Tone"]["result_count"], 2)
        self.assertEqual(scores["Professional Tone"]["sample_count"], 0)
        self.assertIsNone(scores["Professional Tone"]["accuracy"])

    def test_polling_returns_completed_run_and_surfaces_errors(self):
        client = Mock()
        queued = SimpleNamespace(id="run1", status="queued")
        completed = SimpleNamespace(id="run1", status="completed")
        client.evals.runs.retrieve.return_value = completed
        self.assertIs(
            self.ns["wait_for_run"](client, "eval1", queued, poll_seconds=0),
            completed,
        )
        for status in ("failed", "canceled", "cancelled"):
            with self.assertRaises(RuntimeError):
                self.ns["wait_for_run"](
                    client, "eval1", SimpleNamespace(id="run1", status=status)
                )
        with self.assertRaisesRegex(TimeoutError, "NOT been canceled"):
            self.ns["wait_for_run"](client, "eval1", queued, timeout_seconds=0)


if __name__ == "__main__":
    unittest.main()
