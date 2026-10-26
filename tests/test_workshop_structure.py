import ast
import contextlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

import nbformat
import yaml


ROOT = Path(__file__).resolve().parents[1]
LAB7 = ROOT / "labs" / "lab-07-cicd"


class WorkshopStructureTests(unittest.TestCase):
    def test_nine_core_labs_with_setup_and_rubric_extensions(self):
        folders = sorted((ROOT / "labs").glob("lab-*"))
        self.assertEqual(len(folders), 9)
        notebooks = list((ROOT / "labs").glob("*/*.ipynb"))
        self.assertEqual(len(notebooks), 11)
        for path in notebooks:
            with self.subTest(notebook=path.name):
                notebook = nbformat.read(path, as_version=4)
                nbformat.validate(notebook)
                ids = [cell.id for cell in notebook.cells]
                self.assertEqual(len(ids), len(set(ids)))
                for cell in notebook.cells:
                    if cell.cell_type == "code":
                        compile(cell.source, str(path), "exec")

    def test_dependency_first_learning_order(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        table = readme.split("## Learning order", 1)[1].split("For a shorter", 1)[0]
        expected = [
            "lab-03-evaluator-matrix/lab-03-evaluator-matrix.ipynb",
            "lab-03-evaluator-matrix/lab-03b-reference-agent-setup.ipynb",
            "lab-04-portal-sdk-custom/lab-04-portal-sdk-custom.ipynb",
            "lab-05-rag-evaluation/lab-05-rag-evaluation.ipynb",
            "lab-06-agent-evaluation/lab-06-agent-evaluation.ipynb",
            "lab-06-agent-evaluation/lab-06b-llm-as-judge-rubric.ipynb",
            "lab-07-cicd/lab-07-cicd-evaluation-gate.ipynb",
        ]
        positions = [table.index(path) for path in expected]
        self.assertEqual(positions, sorted(positions))
        for path in (
            ROOT / "README.md",
            ROOT / "facilitator" / "facilitator-guide.md",
            ROOT / "labs" / "lab-04-portal-sdk-custom" / "README.md",
        ):
            self.assertNotIn("lab-04b-llm-as-judge-rubric.ipynb", path.read_text(encoding="utf-8"))

    def test_local_documentation_links_resolve(self):
        documents = list(ROOT.glob("*.md"))
        documents += list((ROOT / "facilitator").glob("*.md"))
        documents += list((ROOT / "labs").rglob("*.md"))
        content = [(path, path.read_text(encoding="utf-8")) for path in documents]
        for path in (ROOT / "labs").glob("*/*.ipynb"):
            notebook = nbformat.read(path, as_version=4)
            content.extend(
                (path, cell.source)
                for cell in notebook.cells
                if cell.cell_type == "markdown"
            )
        for path, text in content:
            for target in re.findall(r"\[[^\]\n]+\]\(([^)\s]+)\)", text):
                if re.match(r"^[a-zA-Z][\w+.-]*:", target) or target.startswith("#"):
                    continue
                local = unquote(target.split("#", 1)[0])
                with self.subTest(document=path.name, target=target):
                    self.assertTrue((path.parent / local).exists(), target)

    def test_no_stale_standalone_paths_in_learning_material(self):
        paths = list((ROOT / "labs").glob("*/*.ipynb"))
        paths += list(ROOT.glob("*.md"))
        paths += list((ROOT / "labs").rglob("*.md"))
        paths += list((ROOT / "facilitator").glob("*.md"))
        for path in paths:
            with self.subTest(document=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("accelerators/", text)
                self.assertNotIn("accelerators\\\\", text)
                self.assertNotIn("llm_judge_evaluators.py", text)
                self.assertNotIn("evaluators/**", text)
                self.assertNotIn("evaluators/*", text)

    def test_lab7_generated_templates_reference_retained_support(self):
        notebook = nbformat.read(
            LAB7 / "lab-07-cicd-evaluation-gate.ipynb", as_version=4
        )
        sources = {
            cell.id: cell.source
            for cell in notebook.cells
            if cell.cell_type == "code"
        }
        with tempfile.TemporaryDirectory() as directory:
            namespace = {"Path": Path, "lab_dir": Path(directory), "json": json}
            with contextlib.redirect_stdout(io.StringIO()):
                for cell_id in ("0bceb774", "fc3aba9a", "6dd061e5"):
                    exec(sources[cell_id], namespace)
            for key in ("gh_path", "ado_path"):
                path = namespace[key]
                self.assertTrue(path.is_relative_to(Path(directory)))
                text = path.read_text(encoding="utf-8")
                self.assertIsInstance(yaml.safe_load(text), dict)
                for reference in re.findall(
                    r"(?:python (?!-)|--gate-config |--dataset )([^\s]+)", text
                ):
                    self.assertTrue((ROOT / reference).is_file(), reference)
            self.assertTrue(namespace["gate_config_path"].is_file())

    def test_lab7_synthetic_pass_and_fail_examples_still_work(self):
        notebook = nbformat.read(
            LAB7 / "lab-07-cicd-evaluation-gate.ipynb", as_version=4
        )
        sources = [
            cell.source for cell in notebook.cells if cell.cell_type == "code"
        ]
        with tempfile.TemporaryDirectory() as directory:
            namespace = {"lab_dir": Path(directory), "json": json}
            for source in sources:
                functions = [
                    node for node in ast.parse(source).body
                    if isinstance(node, ast.FunctionDef)
                ]
                exec(
                    compile(
                        ast.Module(body=functions, type_ignores=[]),
                        str(LAB7),
                        "exec",
                    ),
                    namespace,
                )
            with contextlib.redirect_stdout(io.StringIO()):
                for marker in (
                    "gate_config = {",
                    "baseline_scores = {",
                    "failing_candidate =",
                ):
                    source = next(source for source in sources if marker in source)
                    exec(source, namespace)
            self.assertEqual(namespace["gate_result"]["overall_decision"], "PASS")
            self.assertEqual(namespace["failing_result"]["overall_decision"], "FAIL")


if __name__ == "__main__":
    unittest.main()
