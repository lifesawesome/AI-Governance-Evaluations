# Microsoft Foundry Evaluation Engineering Accelerator

A comprehensive, deployable accelerator for evaluating AI agents using Azure AI Foundry. This repository provides **hands-on labs**, **CI/CD pipelines**, **LLM-as-judge evaluators**, and **production monitoring** — all deployable to customer Azure infrastructure.

## 🎯 What's Included

| Component | Description |
|-----------|-------------|
| **9 Lab Notebooks** | Step-by-step Jupyter notebooks CSAs walk through with customers |
| **CI/CD Accelerator** | GitHub Actions + Azure DevOps pipelines with evaluation gates |
| **LLM-as-Judge Accelerator** | Custom prompt-based evaluators with rubrics |
| **Continuous Evaluation** | Production monitoring with trace-based scoring |
| **Infrastructure as Code** | Bicep templates for full environment deployment |
| **Golden Datasets** | Versioned evaluation datasets with coverage validation |
| **Reference Agent** | Contoso Support Agent exercising RAG + tools + multi-turn |

## 📋 Prerequisites

- Azure subscription with AI Foundry access
- Azure CLI authenticated (`az login`)
- Python 3.10+
- `azure-ai-projects>=2.0.0`
- GPT-4o model deployment (for LLM-as-judge evaluators)
- Application Insights resource (for production monitoring)

## 🚀 Quick Start

```bash
# 1. Clone and setup
cd Evaluations_Accelerator
pip install -r requirements.txt

# 2. Configure environment
cp .env.template .env
# Edit .env with your Azure AI Foundry endpoint

# 3. Deploy infrastructure (optional - for full deployment)
az deployment group create --template-file infrastructure/bicep/main.bicep --parameters infrastructure/bicep/parameters.json

# 4. Start with Lab 01
jupyter notebook labs/lab-01-charter/lab-01-evaluation-charter.ipynb
```

### Using existing Azure resources

The notebooks and standalone accelerator scripts load the `.env` beside
`.env.template`. Existing process environment variables take precedence, so CI/CD
secrets and model settings continue to work without a local file. The local
`.env` is ignored by Git.

Configure your own existing resources using these variable names:

| Variable | Value |
|----------|-------|
| `AI_FOUNDRY_PROJECT_ENDPOINT` | `https://<your-account>.services.ai.azure.com/api/projects/<your-project>` |
| `TENANT_ID` | `<your-tenant-id>` |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | `gpt-4.1` |
| `AZURE_AI_SEARCH_ENDPOINT` | `https://<your-search>.search.windows.net` |
| `AZURE_AI_SEARCH_INDEX` | `<your-index-name>` |

Use the project endpoint shown in your Foundry project.
This accelerator reads `AI_FOUNDRY_PROJECT_ENDPOINT`, not
`AZURE_AI_PROJECT_ENDPOINT`. Its search index variable is
`AZURE_AI_SEARCH_INDEX`, not `AZURE_SEARCH_INDEX_NAME`; the search settings are
reserved in the template and are not currently consumed by the Python scripts
or notebooks. Unused workshop settings (Bing, MCP, embeddings, OpenAI direct
access, and sensitive-content tracing) are not needed here.

Authenticate before running the notebooks or scripts:

```powershell
az login --tenant "<your-tenant-id>"
az account set --subscription "<your-subscription-id>"
```

No API key or infrastructure deployment is required to use the existing project.
For live production monitoring in Lab 8, also supply
`APPLICATIONINSIGHTS_CONNECTION_STRING` and `APP_INSIGHTS_WORKSPACE_ID` in `.env`.
The latter is the Log Analytics workspace ID, not the Application Insights
application ID or instrumentation key.

## 📁 Repository Structure

```
Evaluations_Accelerator/
├── labs/                          # 9 hands-on lab notebooks
│   ├── lab-01-charter/            # Evaluation Strategy Charter
│   ├── lab-02-golden-dataset/     # Dataset Engineering
│   ├── lab-03-evaluator-matrix/   # Evaluator Selection
│   ├── lab-04-portal-sdk-custom/  # Portal, SDK & Custom Evaluations
│   ├── lab-05-rag-evaluation/     # RAG Evaluation & Optimization
│   ├── lab-06-agent-evaluation/   # Agent & Tool-Use Evaluation
│   ├── lab-07-cicd/               # Evaluation-Driven CI/CD
│   ├── lab-08-continuous-eval/    # Production Monitoring
│   └── lab-09-operating-model/    # Governance & Operating Model
├── accelerators/                  # Deployable accelerator solutions
│   ├── cicd-evaluation-gate/      # CI/CD pipeline with eval gates
│   ├── llm-as-judge/             # Custom LLM judge evaluators
│   └── continuous-evaluation/     # Production evaluation setup
├── infrastructure/                # Bicep IaC for Azure deployment
├── datasets/                      # Golden, adversarial, expected-actions
├── evaluators/                    # Code-based & prompt-based evaluators
├── src/                          # Reference agent implementation
└── facilitator/                  # CSA delivery guides
```

## 🔄 Module Overview

| Module | Lab | Duration | Key Output |
|--------|-----|----------|------------|
| 1. Evaluation Strategy | Charter creation | 30-45 min | Evaluation Charter |
| 2. Dataset Engineering | Build golden dataset | 45-60 min | Golden Dataset v1 |
| 3. Evaluator Selection | Map failures to evaluators | 30-45 min | Evaluator Matrix |
| 4. Portal, SDK & Custom | Run evaluations both ways | 60-75 min | Baseline Report |
| 5. RAG Evaluation | Parameter sweep & optimize | 60-75 min | RAG Optimization Report |
| 6. Agent Evaluation | System + process eval | 75-90 min | Agent Scorecard |
| 7. CI/CD Gates | Release gate pipeline | 60-75 min | Evaluation Gate |
| 8. Production Monitoring | Continuous evaluation | 60-75 min | Monitoring Plan |
| 9. Governance | Operating model | 45-60 min | Governance Runbook |

## 🏗️ Accelerators (Deployable Solutions)

### 1. CI/CD Evaluation Gate
Deploy a complete evaluation gate into GitHub Actions or Azure DevOps:
- Runs evaluators on every PR/release
- Compares candidate vs baseline scores
- Blocks deployment on safety or quality regression
- Posts evaluation summary to PR

### 2. LLM-as-Judge
Deploy custom evaluators powered by GPT-4o:
- Professional tone evaluator with rubric
- Domain accuracy evaluator
- Escalation appropriateness evaluator
- Configurable thresholds and scoring

### 3. Continuous Evaluation
Deploy production monitoring with automated scoring:
- Samples production traces from Application Insights
- Scores responses on schedule
- Alerts on drift/degradation
- Feeds back into golden dataset

## 📄 License

Microsoft Internal - Customer Delivery IP
