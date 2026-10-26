# Facilitator Guide — Microsoft Foundry Evaluation Engineering Workshop

## Overview

This labs-first workshop is designed for **1-day or 2-day sessions** where CSAs guide customers through building an AI evaluation program. There are nine core labs plus optional Lab 4B and a portal-only model exercise. Labs include live cloud calls, synthetic examples, and adaptation templates; do not present the repository as a production deployment package.

## Prerequisites (Verify Before Workshop)

### Azure Resources
- [ ] Existing Azure AI Foundry project, Contoso agent, and judge model deployment (for example, `gpt-4.1`)
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
| 10:30 | Lab 03: Evaluator Selection Matrix | 30 min |
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
| 09:50 | Lab 04: SDK Evaluation | 45 min |
| 10:35 | Break | 15 min |
| 10:50 | Lab 07: CI/CD Gate | 45 min |
| 11:35 | Lab 09: Operating Model | 25 min |
| 12:00 | Wrap-up | 30 min |

### Advanced Track (add to full day or separate session)
| Lab | Duration | When |
|-----|----------|------|
| Lab 05: RAG Evaluation | 60 min | After Lab 04 |
| Lab 08: Continuous Evaluation | 60 min | After Lab 07 |

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

### Lab 04 — SDK Evaluation
- Optional extension: use [Lab 4B: interactive LLM-as-judge rubric](../labs/lab-04-portal-sdk-custom/lab-04b-llm-as-judge-rubric.ipynb) to teach native weighted rubrics, dimension applicability, and judge explanations. Allow 30-45 minutes; cloud calls are opt-in and require `azure-ai-projects>=2.8.0`. Its responses are hand-authored calibration examples, not live agent outputs.
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
