# Facilitator Guide — Microsoft Foundry Evaluation Engineering Accelerator

## Overview

This accelerator is designed for **1-day or 2-day workshops** where CSAs guide customers through building a complete AI evaluation program. Labs are self-contained Jupyter notebooks that participants run against their own Azure AI Foundry projects.

## Prerequisites (Verify Before Workshop)

### Azure Resources
- [ ] Azure AI Foundry project with GPT-4o deployed
- [ ] Participants have `az login` working with correct tenant
- [ ] Application Insights connected (for Labs 08+)
- [ ] Azure AI Search (for Lab 05 RAG scenarios)

### Participant Machines
- [ ] Python 3.10+
- [ ] Jupyter / VS Code with Jupyter extension
- [ ] `pip install -r requirements.txt` completed
- [ ] `.env` file configured from `.env.template`

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
- "The SDK gives you repeatability; the portal gives you visibility"
- "Custom evaluators let you encode domain-specific quality"

### Lab 06 — Agent Evaluation
- "Agents need TWO evaluations: what they say AND what they do"
- "Tool trajectory = the sequence of actions an agent takes"

### Lab 07 — CI/CD Gate
- "Quality gates turn evaluation from a manual step into an automated checkpoint"
- "Both absolute thresholds and regression detection matter"

### Lab 09 — Governance
- "Evaluation without governance is just an experiment"
- "Measure the program, not just the agent"

## Post-Workshop Follow-Up

1. Share the `accelerators/` folder as deployable solutions
2. Point to `datasets/` as templates for their own domains
3. Schedule 2-week check-in to review their evaluation charter progress
4. Connect them to the CI/CD accelerator for immediate pipeline setup
