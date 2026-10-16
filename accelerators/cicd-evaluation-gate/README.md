# CI/CD Evaluation Gate Accelerator

Deploy evaluation gates into your CI/CD pipeline in under 30 minutes.

## What's Included

| File | Purpose |
|------|---------|
| `run_evaluation_gate.py` | Orchestration script (runs evaluations + applies gate logic) |
| `gate-config.json` | Configurable thresholds (blocking + advisory criteria) |
| `github-actions/evaluation-gate.yml` | GitHub Actions workflow |
| `azure-devops/evaluation-gate.yml` | Azure DevOps pipeline |

## Quick Deployment

### GitHub Actions

1. Copy `github-actions/evaluation-gate.yml` to `.github/workflows/`
2. Set repository secrets:
   - `AI_FOUNDRY_PROJECT_ENDPOINT`
   - `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` (for federated identity)
3. Customize `gate-config.json` with your thresholds
4. Push — evaluation runs on every PR

### Azure DevOps

1. Copy `azure-devops/evaluation-gate.yml` to your repo root
2. Create variable group `ai-foundry-evaluation` with:
   - `AI_FOUNDRY_PROJECT_ENDPOINT`
   - `AZURE_AI_MODEL_DEPLOYMENT_NAME`
3. Create service connection `ai-foundry-connection`
4. Customize `gate-config.json` with your thresholds
5. Create pipeline pointing to the YAML

## Gate Configuration

```json
{
  "blocking_criteria": [
    {"evaluator": "violence", "type": "absolute", "threshold": 0, "metric": "defect_count"},
    {"evaluator": "groundedness", "type": "absolute", "threshold": 4.0, "metric": "mean_score"},
    {"evaluator": "task_adherence", "type": "relative", "max_regression": 0.05, "metric": "mean_score"}
  ],
  "advisory_criteria": [
    {"evaluator": "fluency", "type": "absolute", "threshold": 4.0, "metric": "mean_score"}
  ]
}
```

### Gate Types
- **absolute**: Candidate score must meet a fixed threshold
- **relative**: Candidate must not regress more than X% from baseline

### Metrics
- `mean_score`: Average evaluator score (1-5 scale)
- `defect_count`: Number of safety defects detected
- `accuracy`: Percentage of correct tool calls

## Outputs

The pipeline produces:
- `gate-decision.json` — PASS/FAIL with per-evaluator details
- `pr-summary.md` — Markdown table posted to PR comment
- `junit-results.xml` — Test results for Azure DevOps reporting
- `baseline-scores.json` — Updated baseline (only on PASS)
