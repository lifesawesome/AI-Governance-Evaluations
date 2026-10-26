# Facilitator Guide — Microsoft Foundry Evaluation Engineering Workshop

## Overview

This labs-first workshop is designed for **1-day or 2-day sessions** where CSAs guide customers through building an AI evaluation program. There are nine core labs, Lab 03B reference-agent setup, optional Lab 06B advanced judge calibration, and a portal-only model exercise. Labs include live cloud calls, synthetic examples, and adaptation templates; do not present the repository as a production deployment package.

## Prerequisites (Verify Before Workshop)

### Azure Resources
- [ ] Existing Azure AI Foundry project and judge model deployment (for example, `gpt-4.1`); select an existing Contoso agent or create a minimal one in Lab 03B
- [ ] Participants have `az login` working with correct tenant
- [ ] Application Insights connected (for Labs 08+)
- [ ] Azure AI Search (for Lab 05 RAG scenarios)

### Participant Machines
- [ ] Python 3.10+
- [ ] Jupyter / VS Code with Jupyter extension
- [ ] Dependencies installed from [requirements.txt](../requirements.txt), including `azure-ai-projects>=2.8.0`
- [ ] Local environment configured from [.env.template](../.env.template)

### Quick Validation
```bash
az account show  # Confirm correct subscription
python -c "from azure.ai.projects import AIProjectClient; print('SDK ready')"
```

## Module Selection Guide

### Full Day (8 hours) — Recommended Path
| Time | Lab | Duration |
|------|-----|----------|
| 09:00 | Lab 01: Evaluation Charter | 30 min |
| 09:30 | Lab 02: Golden Dataset | 45 min |
| 10:15 | Break | 15 min |
| 10:30 | Lab 03: Evaluator Selection Matrix | 20 min |
| 10:50 | Lab 03B: Reference-Agent Setup | 10 min |
| 11:00 | Lab 04: Portal & SDK Evaluation | 60 min |
| 12:00 | Lunch | 60 min |
| 13:00 | Lab 06: Agent Evaluation | 60 min |
| 14:00 | Lab 07: CI/CD Evaluation Gate | 60 min |
| 15:00 | Break | 15 min |
| 15:15 | Lab 09: Operating Model | 30 min |
| 15:45 | Wrap-up & Q&A | 45 min |

### Half Day (4 hours) — Essential Path
| Time | Lab | Duration |
|------|-----|----------|
| 09:00 | Lab 01: Evaluation Charter | 20 min |
| 09:20 | Lab 02: Golden Dataset | 30 min |
| 09:50 | Lab 03B: Reference-Agent Setup | 10 min |
| 10:00 | Lab 04: SDK Evaluation | 35 min |
| 10:35 | Break | 15 min |
| 10:50 | Lab 07: CI/CD Gate | 45 min |
| 11:35 | Lab 09: Operating Model | 25 min |
| 12:00 | Wrap-up | 30 min |

### Advanced Track (add to full day or separate session)
| Lab | Duration | When |
|-----|----------|------|
| Lab 05: RAG Evaluation | 60 min | After Lab 04 |
| Lab 06B: Advanced Judge Calibration | 30-45 min | After Labs 05 and 06 |
| Lab 08: Continuous Evaluation | 60 min | After Lab 07 |

For the complete learning path, include Lab 05 between Labs 04 and 06 (use the
two-day format if necessary), then offer Lab 06B. The compressed full-day path
omits RAG and the advanced rubric; do not insert the rubric immediately after
Lab 04. Basic prompt-based judging in Lab 04 still introduces the mechanism.

## Common Troubleshooting

| Issue | Solution |
|-------|----------|
| `AuthenticationError` | Run `az login --tenant <TENANT_ID>` |
| `ResourceNotFoundError` | Verify `AI_FOUNDRY_PROJECT_ENDPOINT` in `.env` |
| `DeploymentNotFoundError` | Check `AZURE_AI_MODEL_DEPLOYMENT_NAME` matches actual deployment |
| Evaluation times out | Reduce dataset size; check model deployment quota |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Notebook kernel dies | Restart kernel; check Python version ≥ 3.10 |

## Talking Points Per Module

### Lab 01 — Charter
- "Before writing any evaluation code, define what quality means for YOUR use case"
- "Failure modes are more useful than success criteria"

### Lab 02 — Dataset
- "Your dataset is your contract with the model"
- "Cover: happy path, edge cases, adversarial, tool-calling"
- "18-25 cases is enough to start; grow organically from production"

### Lab 03B — Reference-Agent Setup
- Complete [reference-agent setup](../labs/lab-03-evaluator-matrix/lab-03b-reference-agent-setup.ipynb) before any Lab 04 live evaluation, including the short track.
- Reuse existing agents unchanged. Creation requires explicit `CREATE_IF_MISSING=True`; the minimal prompt agent has no retrieval or executable tools.
- Save the selected name/version to `.env` with the opt-in save cell or copy its output. Restart evaluation kernels and check process environment overrides.

### Lab 04 — SDK Evaluation
- Optional portal-only extension: follow the [Lab 4 guide](../labs/lab-04-portal-sdk-custom/README.md) to evaluate a model with Developer/User prompts. Explain that model-only results do not exercise the agent's retrieval or tools.
- "The SDK gives you repeatability; the portal gives you visibility"
- "Custom evaluators let you encode domain-specific quality"
- Reuse `contoso-support-agent-eval` (or the configured existing agent); the lab does not redeploy it.
- Show the combined run through its printed Foundry report URL. Use **Automatic Evaluation**, not **Human Evaluation**, or the project-level **Evaluations** page.
- Open the evaluator catalog to show the reusable Response Quality Checker and Professional Tone definitions. Matching definitions are reused; incompatible definitions fail without overwriting them.
- Inspect an actual agent response, all eight criteria, and the tone judge's explanation. Code scores are normalized to 0-1; tone scores remain 1-5.
- Export `baseline-report.json` and `evaluation-results.json` for Lab 7. Retain all cases, including content-filter blocks and evaluator errors/skips. Require `valid_for_comparison: true` before comparing scores; an invalid report is diagnostic only. Averages exclude generation/evaluator failures with explicit sample/total/error counts, never counting missing scores as passes. Failed quality checks remain valid results. Lab 7's synthetic example scores must not be compared to these cloud scores.

### Lab 06 — Agent Evaluation
- "Agents need TWO evaluations: what they say AND what they do"
- "Tool trajectory = the sequence of actions an agent takes"
- This lab creates a separate `contoso-support-agent-tools-eval` target. Do not replace the reference-agent pin or compare its scorecard directly with a different target's baseline.

### Lab 06B — Advanced Judge Calibration
- After RAG and agent/tool evaluation, use [Lab 06B: advanced LLM-as-judge rubric](../labs/lab-06-agent-evaluation/lab-06b-llm-as-judge-rubric.ipynb) to teach native weighted rubrics, dimension applicability, and judge explanations. Allow 30-45 minutes; cloud calls are opt-in and require `azure-ai-projects>=2.8.0`.
- Its scored responses are hand-authored calibration examples, not live agent outputs or tool traces. Optional agent-based generation uses the Lab 03B reference-agent pin.
- Use the observed retrieval and action failure modes to discuss what answer-only rubrics cannot measure.

### Lab 07 — CI/CD Gate
- "Quality gates turn evaluation from a manual step into an automated checkpoint"
- "Both absolute thresholds and regression detection matter"
- The notebook's pass/fail demonstrations use synthetic scores. The retained runner and generated pipeline YAML are adaptation templates, not a certified production release gate. Follow the [Lab 7 limitations](../labs/lab-07-cicd/README.md); do not claim the current invalid Lab 4 report is a usable baseline.

### Lab 09 — Governance
- "Evaluation without governance is just an experiment"
- "Measure the program, not just the agent"

## Post-Workshop Follow-Up

1. Share the [workshop learning path](../README.md) and completed lab notebooks
2. Point to the [datasets](../datasets/) as templates for their own domains
3. Schedule 2-week check-in to review their evaluation charter progress
4. Review the [Lab 7 adaptation checklist](../labs/lab-07-cicd/README.md) before planning live CI/CD integration
