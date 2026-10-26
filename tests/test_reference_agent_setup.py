import ast
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import nbformat
from azure.ai.projects.models import PromptAgentDefinition
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from dotenv import dotenv_values, set_key


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = (
    ROOT / "labs" / "lab-03-evaluator-matrix" / "lab-03b-reference-agent-setup.ipynb"
)
SOURCES = {
    cell.id: cell.source
    for cell in nbformat.read(NOTEBOOK, as_version=4).cells
    if cell.cell_type == "code"
}


class ReferenceAgentSetupTests(unittest.TestCase):
    def setUp(self):
        namespace = {
            "ResourceNotFoundError": ResourceNotFoundError,
            "PromptAgentDefinition": PromptAgentDefinition,
        }
        functions = [
            node for node in ast.parse(SOURCES["setup-resolve-agent"]).body
            if isinstance(node, ast.FunctionDef)
        ]
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(NOTEBOOK), "exec"), namespace)
        self.select = namespace["select_reference_agent"]
        self.project = Mock()
        self.agent = SimpleNamespace(name="reference", version="7")

    def test_existing_latest_is_reused_without_creation(self):
        self.project.agents.get.return_value.versions.latest = self.agent
        selected = self.select(self.project, "reference", None, "model", "instructions", True)
        self.assertIs(selected, self.agent)
        self.project.agents.create_version.assert_not_called()

    def test_pinned_version_is_reused_without_resolving_latest(self):
        self.project.agents.get_version.return_value = self.agent
        self.assertIs(
            self.select(self.project, "reference", "7", "model", "instructions"),
            self.agent,
        )
        self.project.agents.get_version.assert_called_once_with(agent_name="reference", agent_version="7")
        self.project.agents.get.assert_not_called()
        self.project.agents.create_version.assert_not_called()

    def test_creation_requires_opt_in_and_no_missing_version_pin(self):
        for version, allow_creation in ((None, False), ("7", False), ("7", True)):
            with self.subTest(version=version, allow_creation=allow_creation):
                project = Mock()
                project.agents.get.side_effect = ResourceNotFoundError("missing")
                project.agents.get_version.side_effect = ResourceNotFoundError("missing")
                with self.assertRaisesRegex(RuntimeError, "was not found"):
                    self.select(project, "reference", version, "model", "instructions", allow_creation)
                project.agents.create_version.assert_not_called()

    def test_opt_in_creates_minimal_agent_with_reference_instructions(self):
        self.project.agents.get.side_effect = ResourceNotFoundError("missing")
        self.project.agents.create_version.return_value = self.agent
        result = self.select(self.project, "reference", None, "deployment", "reference instructions", True)
        self.assertIs(result, self.agent)
        sent = self.project.agents.create_version.call_args.kwargs
        self.assertEqual(sent["agent_name"], "reference")
        definition = sent["definition"].as_dict()
        self.assertEqual(definition["kind"], "prompt")
        self.assertEqual(definition["model"], "deployment")
        self.assertEqual(definition["instructions"], "reference instructions")
        self.assertFalse(definition.get("tools"))

    def test_permission_and_creation_errors_propagate(self):
        self.project.agents.get.side_effect = HttpResponseError("Forbidden")
        with self.assertRaises(HttpResponseError):
            self.select(self.project, "reference", None, "model", "instructions", True)
        self.project.agents.create_version.assert_not_called()
        self.project.agents.get.side_effect = ResourceNotFoundError("missing")
        self.project.agents.create_version.side_effect = HttpResponseError("creation failed")
        with self.assertRaises(HttpResponseError):
            self.select(self.project, "reference", None, "model", "instructions", True)

    def test_saving_pins_name_and_version_preserving_other_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text("OTHER_SETTING=keep\nAI_FOUNDRY_AGENT_VERSION=1\n", encoding="utf-8")
            namespace = {
                "SAVE_SELECTION": True, "env_path": env_path,
                "set_key": set_key, "agent": self.agent,
            }
            with contextlib.redirect_stdout(io.StringIO()):
                exec(SOURCES["setup-save-selection"], namespace)
            self.assertEqual(dotenv_values(env_path), {
                "OTHER_SETTING": "keep",
                "AI_FOUNDRY_AGENT_NAME": "reference",
                "AI_FOUNDRY_AGENT_VERSION": "7",
            })

    def test_save_is_opt_in(self):
        save = Mock()
        with contextlib.redirect_stdout(io.StringIO()):
            exec(SOURCES["setup-save-selection"], {
                "SAVE_SELECTION": False, "set_key": save, "agent": self.agent,
            })
        save.assert_not_called()
        self.assertIn("CREATE_IF_MISSING = False", SOURCES["setup-configuration"])
        self.assertIn("SAVE_SELECTION = False", SOURCES["setup-configuration"])

    def test_setup_and_evaluation_notebooks_use_the_same_reference_pin(self):
        notebooks = [
            NOTEBOOK,
            ROOT / "labs" / "lab-04-portal-sdk-custom" / "lab-04-portal-sdk-custom.ipynb",
            ROOT / "labs" / "lab-06-agent-evaluation" / "lab-06b-llm-as-judge-rubric.ipynb",
        ]
        for path in notebooks:
            with self.subTest(notebook=path.name):
                assignments = [
                    node
                    for cell in nbformat.read(path, as_version=4).cells
                    if cell.cell_type == "code"
                    for node in ast.parse(cell.source).body
                    if isinstance(node, ast.Assign)
                    and any(
                        isinstance(target, ast.Name)
                        and target.id in {"agent_name", "agent_version"}
                        for target in node.targets
                    )
                ]
                code = compile(ast.Module(body=assignments, type_ignores=[]), str(path), "exec")
                for environment in (
                    {},
                    {"AI_FOUNDRY_AGENT_NAME": "selected", "AI_FOUNDRY_AGENT_VERSION": "7"},
                ):
                    namespace = {"os": SimpleNamespace(environ=environment)}
                    exec(code, namespace)
                    self.assertEqual(namespace["agent_name"], environment.get(
                        "AI_FOUNDRY_AGENT_NAME", "contoso-support-agent-eval"
                    ))
                    self.assertEqual(namespace["agent_version"], environment.get("AI_FOUNDRY_AGENT_VERSION"))


if __name__ == "__main__":
    unittest.main()
