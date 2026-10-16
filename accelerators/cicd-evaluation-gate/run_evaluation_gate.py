"""
Evaluation Gate Runner - CI/CD Accelerator

This script orchestrates the full evaluation gate process:
1. Deploys/references the agent under test
2. Runs evaluation suite against golden dataset
3. Compares results against baseline
4. Applies gate logic (blocking + advisory criteria)
5. Generates reports (gate decision, PR summary, JUnit XML)

Usage:
    python run_evaluation_gate.py \
        --dataset datasets/golden/contoso-golden-v1.jsonl \
        --gate-config accelerators/cicd-evaluation-gate/gate-config.json \
        --output-dir ./evaluation-results \
        --baseline-file ./evaluation-results/baseline-scores.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


def load_dataset(dataset_path: str) -> list:
    """Load JSONL dataset and format for evaluation."""
    entries = []
    with open(dataset_path) as f:
        for line in f:
            entry = json.loads(line)
            entries.append({"item": {
                "query": entry["query"],
                "ground_truth": entry.get("ground_truth", ""),
                "context": entry.get("context", ""),
            }})
    return entries


def run_evaluation(project_client, openai_client, agent_name: str, test_data: list, model_deployment: str) -> dict:
    """Run evaluation suite and return per-evaluator scores."""
    from openai.types.eval_create_params import DataSourceConfigCustom

    data_source_config = DataSourceConfigCustom(
        type="custom",
        item_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "ground_truth": {"type": "string"},
                "context": {"type": "string"}
            },
            "required": ["query"]
        },
        include_sample_schema=True,
    )

    testing_criteria = [
        {
            "type": "azure_ai_evaluator",
            "name": "task_adherence",
            "evaluator_name": "builtin.task_adherence",
            "initialization_parameters": {"deployment_name": model_deployment},
            "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_items}}"},
        },
        {
            "type": "azure_ai_evaluator",
            "name": "fluency",
            "evaluator_name": "builtin.fluency",
            "initialization_parameters": {"deployment_name": model_deployment},
            "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_text}}"},
        },
        {
            "type": "azure_ai_evaluator",
            "name": "coherence",
            "evaluator_name": "builtin.coherence",
            "initialization_parameters": {"deployment_name": model_deployment},
            "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_text}}"},
        },
        {
            "type": "azure_ai_evaluator",
            "name": "violence",
            "evaluator_name": "builtin.violence",
            "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_text}}"},
        },
        {
            "type": "azure_ai_evaluator",
            "name": "sexual",
            "evaluator_name": "builtin.sexual",
            "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_text}}"},
        },
        {
            "type": "azure_ai_evaluator",
            "name": "hate_unfairness",
            "evaluator_name": "builtin.hate_unfairness",
            "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_text}}"},
        },
    ]

    # Create evaluation
    eval_object = openai_client.evals.create(
        name=f"CI/CD Gate - {time.strftime('%Y%m%d-%H%M%S')}",
        data_source_config=data_source_config,
        testing_criteria=testing_criteria,
    )

    # Get latest agent version
    agent = project_client.agents.get_latest_version(agent_name=agent_name)

    # Run evaluation
    data_source = {
        "type": "azure_ai_target_completions",
        "source": {"type": "file_content", "content": test_data},
        "input_messages": {
            "type": "template",
            "template": [{"type": "message", "role": "user", "content": {"type": "input_text", "text": "{{item.query}}"}}],
        },
        "target": {"type": "azure_ai_agent", "name": agent.name, "version": agent.version},
    }

    eval_run = openai_client.evals.runs.create(
        eval_id=eval_object.id,
        name=f"Gate Run {time.strftime('%Y%m%d-%H%M%S')}",
        data_source=data_source,
    )

    # Poll for completion
    while eval_run.status not in ["completed", "failed", "canceled"]:
        time.sleep(15)
        eval_run = openai_client.evals.runs.retrieve(eval_id=eval_object.id, run_id=eval_run.id)
        print(f"  Evaluation status: {eval_run.status}")

    if eval_run.status != "completed":
        raise RuntimeError(f"Evaluation failed with status: {eval_run.status}")

    # Extract scores from results
    scores = extract_scores(eval_run)
    return scores


def extract_scores(eval_run) -> dict:
    """Extract per-evaluator scores from evaluation run results."""
    scores = {}
    if hasattr(eval_run, 'per_testing_criteria_results') and eval_run.per_testing_criteria_results:
        for criteria_result in eval_run.per_testing_criteria_results:
            name = criteria_result.testing_criteria
            scores[name] = {
                "mean_score": getattr(criteria_result, 'mean_score', None),
                "defect_count": getattr(criteria_result, 'defect_count', 0),
                "accuracy": getattr(criteria_result, 'accuracy', None),
            }
    return scores


def evaluate_gate(baseline_scores: dict, candidate_scores: dict, gate_config: dict) -> dict:
    """Apply gate logic to compare baseline vs candidate."""
    blocking_results = []
    advisory_results = []
    overall_pass = True

    for criteria in gate_config["blocking_criteria"]:
        evaluator = criteria["evaluator"]
        candidate_value = candidate_scores.get(evaluator, {}).get(criteria["metric"])

        if candidate_value is None:
            blocking_results.append({"evaluator": evaluator, "status": "SKIP", "reason": "No data"})
            continue

        if criteria["type"] == "absolute":
            if criteria["metric"] == "defect_count":
                passed = candidate_value <= criteria["threshold"]
            else:
                passed = candidate_value >= criteria["threshold"]
            result = {
                "evaluator": evaluator, "status": "PASS" if passed else "FAIL",
                "value": candidate_value, "threshold": criteria["threshold"], "type": "absolute"
            }
        elif criteria["type"] == "relative":
            baseline_value = baseline_scores.get(evaluator, {}).get(criteria["metric"], 0)
            regression = (baseline_value - candidate_value) / baseline_value if baseline_value > 0 else 0
            passed = regression <= criteria["max_regression"]
            result = {
                "evaluator": evaluator, "status": "PASS" if passed else "FAIL",
                "baseline": baseline_value, "candidate": candidate_value,
                "regression": f"{regression:.1%}", "max_allowed": f"{criteria['max_regression']:.1%}",
                "type": "relative"
            }

        if result["status"] == "FAIL":
            overall_pass = False
        blocking_results.append(result)

    for criteria in gate_config["advisory_criteria"]:
        evaluator = criteria["evaluator"]
        candidate_value = candidate_scores.get(evaluator, {}).get(criteria["metric"])
        advisory_results.append({
            "evaluator": evaluator,
            "status": "OK" if candidate_value and candidate_value >= criteria.get("threshold", 0) else "WARN",
            "value": candidate_value,
        })

    return {
        "overall_decision": "PASS" if overall_pass else "FAIL",
        "blocking_results": blocking_results,
        "advisory_results": advisory_results,
    }


def generate_pr_summary(gate_result: dict) -> str:
    """Generate markdown PR comment."""
    decision = gate_result["overall_decision"]
    icon = "✅" if decision == "PASS" else "❌"

    summary = f"## {icon} Evaluation Gate: {decision}\n\n"
    summary += "### Blocking Criteria\n\n"
    summary += "| Evaluator | Status | Value | Threshold |\n|-----------|--------|-------|----------|\n"

    for r in gate_result["blocking_results"]:
        status_icon = "✅" if r["status"] == "PASS" else "❌" if r["status"] == "FAIL" else "⏭️"
        val = r.get("value", r.get("candidate", "-"))
        threshold = r.get("threshold", r.get("max_allowed", "-"))
        summary += f"| {r['evaluator']} | {status_icon} {r['status']} | {val} | {threshold} |\n"

    summary += "\n### Advisory Criteria\n\n"
    summary += "| Evaluator | Status | Value |\n|-----------|--------|-------|\n"
    for r in gate_result["advisory_results"]:
        status_icon = "✅" if r["status"] == "OK" else "⚠️"
        summary += f"| {r['evaluator']} | {status_icon} {r['status']} | {r['value']} |\n"

    return summary


def generate_junit_xml(gate_result: dict) -> str:
    """Generate JUnit XML for Azure DevOps test reporting."""
    tests = gate_result["blocking_results"] + gate_result["advisory_results"]
    failures = [t for t in gate_result["blocking_results"] if t.get("status") == "FAIL"]

    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += f'<testsuites tests="{len(tests)}" failures="{len(failures)}">\n'
    xml += f'  <testsuite name="EvaluationGate" tests="{len(tests)}" failures="{len(failures)}">\n'

    for t in tests:
        xml += f'    <testcase name="{t["evaluator"]}" classname="EvaluationGate">\n'
        if t.get("status") == "FAIL":
            xml += f'      <failure message="{t["evaluator"]} failed gate criteria">{json.dumps(t)}</failure>\n'
        xml += f'    </testcase>\n'

    xml += '  </testsuite>\n</testsuites>\n'
    return xml


def main():
    parser = argparse.ArgumentParser(description="Run AI Agent Evaluation Gate")
    parser.add_argument("--dataset", required=True, help="Path to JSONL dataset")
    parser.add_argument("--gate-config", required=True, help="Path to gate configuration JSON")
    parser.add_argument("--output-dir", required=True, help="Output directory for results")
    parser.add_argument("--baseline-file", help="Path to baseline scores JSON (optional)")
    parser.add_argument("--agent-name", default="contoso-support-agent-eval", help="Agent name to evaluate")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load configs
    with open(args.gate_config) as f:
        gate_config = json.load(f)

    test_data = load_dataset(args.dataset)
    print(f"Loaded {len(test_data)} test cases from {args.dataset}")

    # Initialize clients
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    project_endpoint = os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"]
    model_deployment = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o")

    credential = DefaultAzureCredential()
    project_client = AIProjectClient(endpoint=project_endpoint, credential=credential)
    openai_client = project_client.get_openai_client()

    # Run evaluation
    print("Running evaluation...")
    candidate_scores = run_evaluation(project_client, openai_client, args.agent_name, test_data, model_deployment)

    # Load or create baseline
    if args.baseline_file and Path(args.baseline_file).exists():
        with open(args.baseline_file) as f:
            baseline_scores = json.load(f)
    else:
        baseline_scores = candidate_scores  # First run becomes baseline

    # Apply gate logic
    gate_result = evaluate_gate(baseline_scores, candidate_scores, gate_config)

    # Save outputs
    with open(output_dir / "gate-decision.json", "w") as f:
        json.dump(gate_result, f, indent=2)

    with open(output_dir / "candidate-scores.json", "w") as f:
        json.dump(candidate_scores, f, indent=2)

    with open(output_dir / "pr-summary.md", "w") as f:
        f.write(generate_pr_summary(gate_result))

    with open(output_dir / "junit-results.xml", "w") as f:
        f.write(generate_junit_xml(gate_result))

    # Save as new baseline if passing
    if gate_result["overall_decision"] == "PASS":
        with open(output_dir / "baseline-scores.json", "w") as f:
            json.dump(candidate_scores, f, indent=2)

    print(f"\nGate Decision: {gate_result['overall_decision']}")
    sys.exit(0 if gate_result["overall_decision"] == "PASS" else 1)


if __name__ == "__main__":
    main()
