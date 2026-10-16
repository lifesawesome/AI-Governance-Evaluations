# Continuous Evaluation Accelerator

Monitor production AI agent quality with automated trace sampling, scoring, and drift detection.

## Architecture

```
Application Insights → Sample Traces → Score with Evaluators → Drift Detection → Alert
                                                                       ↓
                                                              High-quality traces → Dataset
```

## Usage

### CLI

```bash
python continuous_evaluator.py \
    --sample-size 20 \
    --lookback-hours 1 \
    --baseline ./baseline-scores.json \
    --drift-threshold 0.1 \
    --output ./results.json
```

### As Library

```python
from continuous_evaluator import ContinuousEvaluator

evaluator = ContinuousEvaluator(
    project_endpoint="https://...",
    app_insights_connection="InstrumentationKey=...",
    sample_size=20,
    lookback_hours=1,
)

traces = evaluator.sample_traces()
results = evaluator.evaluate_traces(traces)
drift = evaluator.check_drift(current_scores, "baseline.json")
```

### Scheduled Execution

**Azure Functions Timer Trigger** (recommended):
```python
# function_app.py
@app.timer_trigger(schedule="0 0 * * * *")  # Hourly
def run_evaluation(timer: func.TimerRequest):
    evaluator = ContinuousEvaluator(...)
    traces = evaluator.sample_traces()
    evaluator.evaluate_traces(traces)
```

**GitHub Actions Schedule**:
```yaml
on:
  schedule:
    - cron: '0 * * * *'  # Hourly
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AI_FOUNDRY_PROJECT_ENDPOINT` | Yes | Azure AI Foundry project endpoint |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Yes | App Insights connection string |
| `APP_INSIGHTS_WORKSPACE_ID` | Yes | Log Analytics workspace ID |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | No | Model for evaluation (default: gpt-4o) |

## Drift Detection

Drift is calculated as: `(baseline_mean - current_mean) / baseline_mean`

| Drift % | Severity | Action |
|---------|----------|--------|
| < 5% | Normal | No action |
| 5-15% | Warning | Review recommended |
| > 15% | Critical | Alert + investigate |
