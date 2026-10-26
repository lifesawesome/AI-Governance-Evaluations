import ast
import copy
import json
import math
import os
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import nbformat
import pandas as pd
from azure.ai.projects.models import EvaluatorVersion, RubricBasedEvaluatorDefinition
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "labs" / "lab-04-portal-sdk-custom" / "lab-04b-llm-as-judge-rubric.ipynb"
CELLS = nbformat.read(NOTEBOOK, as_version=4).cells
SOURCES = {cell.id: cell.source for cell in CELLS if cell.cell_type == "code"}


def functions_namespace():
    namespace = {
        "ResourceNotFoundError": ResourceNotFoundError,
        "math": math,
        "pd": pd,
        "time": time,
        "display": Mock(),
    }
    for source in SOURCES.values():
        functions = [
            node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)
        ]
        exec(
            compile(ast.Module(body=functions, type_ignores=[]), str(NOTEBOOK), "exec"),
            namespace,
        )
    exec(SOURCES["rubric-authored-dimensions"], {**namespace, "PASS_THRESHOLD": 0.8})
    return namespace


class RubricNotebookTests(unittest.TestCase):
    def setUp(self):
        self.ns = functions_namespace()
        scope = {**self.ns, "PASS_THRESHOLD": 0.8}
        exec(SOURCES["rubric-authored-dimensions"], scope)
        self.dimensions = scope["dimensions"]
        self.spec = {
            "name": "contoso_test_rubric",
            "evaluator_type": "custom",
            "categories": ["quality"],
            "definition": {
                "type": "rubric",
                "dimensions": self.dimensions,
                "pass_threshold": 0.8,
            },
        }

    def evaluator(self, spec=None, version="1"):
        return EvaluatorVersion({**(spec or self.spec), "version": version})

    def item(self, case_id="accurate_leave"):
        return {
            "datasource_item": {
                "case_id": case_id,
                "query": "Policy reference: 20 days. Question: annual leave?",
                "response": "20 days, under the policy.",
            },
            "results": [{
                "name": "Contoso Support Rubric",
                "status": "completed",
                "score": 0.7,
                "passed": False,
                "label": "fail",
                "threshold": 0.5,
                "reason": "The service verdict is retained, not locally recalculated.",
                "properties": {
                    "dimension_scores": [
                        {
                            "id": dimension["id"],
                            "score": None if dimension["id"] == "appropriate_escalation" else 5,
                            "applicable": dimension["id"] != "appropriate_escalation",
                            "weight": dimension["weight"],
                            "reason": "Not applicable to routine policy questions."
                            if dimension["id"] == "appropriate_escalation"
                            else "Supported by the reference.",
                        }
                        for dimension in self.dimensions
                    ]
                },
            }],
        }

    def tables(self, items, cases=None):
        return self.ns["rubric_result_tables"](
            items, self.dimensions, cases or ["accurate_leave"], "Contoso Support Rubric"
        )

    def test_notebook_schema_and_all_cells_compile(self):
        nbformat.validate(nbformat.read(NOTEBOOK, as_version=4))
        self.assertEqual(len(CELLS), len({cell.id for cell in CELLS}))
        for cell_id, source in SOURCES.items():
            compile(source, f"{NOTEBOOK}:{cell_id}", "exec")
        definition = RubricBasedEvaluatorDefinition(self.spec["definition"])
        self.assertEqual(definition.type, "rubric")
        self.assertEqual(definition.pass_threshold, 0.8)

    def test_dimensions_have_stable_ids_weights_and_applicability(self):
        self.ns["validate_dimensions"](self.dimensions, 0.8)
        self.assertEqual(
            [entry["id"] for entry in self.dimensions if entry["weight"] >= 8],
            ["policy_accuracy"],
        )
        general = next(entry for entry in self.dimensions if entry["id"] == "general_quality")
        self.assertTrue(general["always_applicable"])
        invalid = copy.deepcopy(self.dimensions)
        invalid[0]["weight"] = True
        with self.assertRaises(ValueError):
            self.ns["validate_dimensions"](invalid, 0.8)
        with self.assertRaises(ValueError):
            self.ns["validate_dimensions"](self.dimensions * 2, 0.8)
        with self.assertRaises(ValueError):
            self.ns["validate_dimensions"](self.dimensions, 1.1)

    def test_manual_registration_is_native_rubric(self):
        for absent in ([], ResourceNotFoundError("missing")):
            catalog = Mock()
            if isinstance(absent, Exception):
                catalog.list_versions.side_effect = absent
            else:
                catalog.list_versions.return_value = absent
            catalog.create_version.return_value = self.evaluator()
            result = self.ns["resolve_rubric"](
                catalog, self.spec["name"], "manual", self.dimensions, 0.8
            )
            self.assertEqual(result.definition.type, "rubric")
            sent = catalog.create_version.call_args.kwargs["evaluator_version"]
            self.assertEqual(sent["definition"], self.spec["definition"])
            catalog.begin_create_generation_job.assert_not_called()

    def test_matching_latest_rubric_is_reused(self):
        catalog = Mock()
        latest = self.evaluator(version="10")
        catalog.list_versions.return_value = [self.evaluator(version="2"), latest]
        self.assertIs(
            self.ns["resolve_rubric"](
                catalog, self.spec["name"], "manual", self.dimensions, 0.8
            ),
            latest,
        )
        catalog.create_version.assert_not_called()

    def test_incompatible_rubric_is_never_overwritten(self):
        catalog = Mock()
        changed = copy.deepcopy(self.spec)
        changed["definition"]["pass_threshold"] = 0.5
        catalog.list_versions.return_value = [self.evaluator(changed)]
        with self.assertRaisesRegex(ValueError, "nothing was overwritten"):
            self.ns["resolve_rubric"](
                catalog, self.spec["name"], "manual", self.dimensions, 0.8
            )
        catalog.create_version.assert_not_called()
        changed["definition"]["type"] = "prompt"
        catalog.list_versions.return_value = [self.evaluator(changed)]
        with self.assertRaisesRegex(ValueError, "not a native rubric"):
            self.ns["resolve_rubric"](
                catalog, self.spec["name"], "manual", self.dimensions, 0.8
            )

    def test_permission_errors_are_not_treated_as_missing(self):
        catalog = Mock()
        catalog.list_versions.side_effect = HttpResponseError("Forbidden")
        with self.assertRaises(HttpResponseError):
            self.ns["resolve_rubric"](
                catalog, self.spec["name"], "manual", self.dimensions, 0.8
            )
        catalog.create_version.assert_not_called()

    def test_agent_generation_uses_idempotent_operation_and_existing_agent_source(self):
        catalog = Mock()
        catalog.list_versions.return_value = []
        catalog.begin_create_generation_job.return_value.result.return_value = self.evaluator()
        job = {
            "model": "gpt-4.1",
            "evaluator_name": self.spec["name"],
            "sources": [{
                "type": "agent",
                "agent_name": "contoso-support-agent-eval",
                "agent_version": "1",
            }],
        }
        result = self.ns["resolve_rubric"](
            catalog, self.spec["name"], "agent", self.dimensions, 0.8, job, "operation-1"
        )
        self.assertEqual(result.definition.type, "rubric")
        catalog.begin_create_generation_job.assert_called_once_with(
            job=job, operation_id="operation-1", polling_interval=10
        )
        catalog.begin_create_generation_job.return_value.result.assert_called_once_with(
            timeout=600
        )
        catalog.create_version.assert_not_called()

    def test_generation_polling_errors_propagate(self):
        catalog = Mock()
        catalog.list_versions.return_value = []
        catalog.begin_create_generation_job.return_value.result.side_effect = TimeoutError()
        with self.assertRaises(TimeoutError):
            self.ns["resolve_rubric"](
                catalog, self.spec["name"], "agent", self.dimensions, 0.8,
                {"sources": []}, "operation-1",
            )

    def test_service_verdict_and_nonapplicable_dimensions_are_preserved(self):
        overall, dimensions, issues = self.tables([self.item()])
        self.assertEqual(issues, [])
        self.assertEqual(overall.iloc[0]["score"], 0.7)
        self.assertFalse(overall.iloc[0]["passed"])
        self.assertEqual(overall.iloc[0]["label"], "fail")
        escalation = dimensions[dimensions["id"] == "appropriate_escalation"].iloc[0]
        self.assertFalse(escalation["applicable"])
        self.assertTrue(pd.isna(escalation["score"]))
        self.assertTrue(dimensions["reason"].str.len().gt(0).all())

    def test_errors_missing_dimensions_and_duplicate_cases_are_explicit(self):
        for status in ("error", "skipped"):
            item = self.item()
            item["results"][0].update(status=status, score=None, passed=None)
            item["results"][0]["properties"] = {}
            overall, _, issues = self.tables([item])
            self.assertTrue(issues)
            self.assertEqual(len(overall), 1)
            self.assertIsNone(overall.iloc[0]["score"])
        item = self.item()
        item["results"][0]["properties"]["dimension_scores"].pop()
        self.assertTrue(self.tables([item])[2])
        item = self.item()
        self.assertTrue(self.tables([item, item])[2])
        item["results"] = []
        self.assertTrue(self.tables([item])[2])
        self.assertTrue(self.tables([])[2])

    def test_dimension_contract_mismatches_are_not_hidden(self):
        for field, value in (("score", 6), ("score", float("nan")), ("weight", 1), ("applicable", None)):
            item = self.item()
            item["results"][0]["properties"]["dimension_scores"][0][field] = value
            self.assertTrue(self.tables([item])[2])
        item = self.item()
        general = item["results"][0]["properties"]["dimension_scores"][-1]
        general.update(applicable=False, score=None)
        self.assertTrue(self.tables([item])[2])

    def test_polling_surfaces_failure_and_timeout_without_resubmitting(self):
        client = Mock()
        queued = SimpleNamespace(id="run1", status="queued")
        completed = SimpleNamespace(id="run1", status="completed")
        client.evals.runs.retrieve.return_value = completed
        self.assertIs(
            self.ns["wait_for_rubric_run"](client, "eval1", queued, poll_seconds=0),
            completed,
        )
        for status in ("failed", "canceled", "cancelled"):
            with self.assertRaises(RuntimeError):
                self.ns["wait_for_rubric_run"](
                    client, "eval1", SimpleNamespace(id="run1", status=status)
                )
        with self.assertRaisesRegex(TimeoutError, "not canceled"):
            self.ns["wait_for_rubric_run"](client, "eval1", queued, timeout_seconds=0)
        client.evals.runs.create.assert_not_called()

    def test_all_cells_run_offline_without_azure_calls_or_fake_scores(self):
        namespace = {}
        with (
            patch("azure.ai.projects.AIProjectClient") as project,
            patch("azure.identity.AzureCliCredential") as credential,
            patch("IPython.display.display"),
            patch("builtins.print"),
        ):
            for source in SOURCES.values():
                exec(compile(source, str(NOTEBOOK), "exec"), namespace)
        project.assert_not_called()
        credential.assert_not_called()
        self.assertIsNone(namespace["eval_run"])
        self.assertEqual(len(namespace["judge_items"]), 4)
        self.assertNotIn("overall_results", namespace)
        for entry in namespace["judge_items"]:
            self.assertEqual(set(entry["item"]), {"case_id", "query", "response"})
            self.assertNotIn("human_expectation", entry["item"])
            self.assertNotIn("ground_truth", entry["item"])

    def test_mocked_cloud_workflow_exports_real_shape_and_pins_evaluator(self):
        namespace = {}
        project = Mock()
        catalog = project.evaluators
        catalog.list_versions.return_value = []
        catalog.create_version.side_effect = lambda name, evaluator_version: EvaluatorVersion(
            {**evaluator_version, "version": "1"}
        )
        client = project.get_openai_client.return_value
        client.evals.create.return_value = SimpleNamespace(id="eval1")
        run_dict = {"id": "run1", "status": "completed", "report_url": "https://example.test/report"}
        run = SimpleNamespace(
            **run_dict, per_testing_criteria_results=[],
            model_dump=lambda **kwargs: run_dict,
        )
        client.evals.runs.create.return_value = run

        def output_items(**kwargs):
            result = []
            for entry in namespace["judge_items"]:
                item = self.item(entry["item"]["case_id"])
                item["datasource_item"] = entry["item"]
                result.append(SimpleNamespace(model_dump=lambda data=item, **kwargs: data))
            return result

        client.evals.runs.output_items.list.side_effect = output_items
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"AI_FOUNDRY_PROJECT_ENDPOINT": "https://example.test/project"}),
            patch("azure.ai.projects.AIProjectClient", return_value=project),
            patch("azure.identity.AzureCliCredential"),
            patch("IPython.display.display"),
            patch("builtins.print"),
        ):
            for cell_id, source in SOURCES.items():
                if cell_id == "rubric-configuration":
                    source = source.replace("RUN_CLOUD = False", "RUN_CLOUD = True")
                if cell_id == "rubric-review-approval":
                    source = source.replace("RUBRIC_REVIEWED = False", "RUBRIC_REVIEWED = True")
                exec(compile(source, str(NOTEBOOK), "exec"), namespace)
                if cell_id == "rubric-configuration":
                    namespace["output_dir"] = Path(directory)
            payload = json.loads(
                (Path(directory) / "rubric-evaluation-results.json").read_text(encoding="utf-8")
            )
            self.assertTrue(payload["complete_for_review"])
            self.assertFalse(payload["valid_for_release_gate"])
            self.assertEqual(len(payload["output_items"]), 4)
            self.assertEqual(payload["input_kind"], "hand_authored_calibration_responses")
        criteria = client.evals.create.call_args.kwargs["testing_criteria"][0]
        self.assertEqual(criteria["evaluator_version"], "1")
        self.assertEqual(criteria["data_mapping"]["response"], "{{item.response}}")
        self.assertEqual(criteria["initialization_parameters"]["deployment_name"], namespace["judge_deployment"])
        self.assertEqual(client.evals.runs.create.call_args.kwargs["data_source"]["type"], "jsonl")
        project.agents.create_version.assert_not_called()
        project.agents.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
