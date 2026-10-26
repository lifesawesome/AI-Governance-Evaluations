# Microsoft Foundry Evaluation Engineering Workshop

Start here for a **labs-first learning path** using the existing Contoso support
agent and Microsoft Foundry project. There are **nine core lab notebooks**, one
**Lab 03B reference-agent setup**, optional **Lab 06B native-rubric notebook**, and a portal-only model evaluation
exercise. Standalone examples and unused evaluator templates have been removed;
the lab notebooks are the source of the exercises.

These are instructional labs, not a production deployment package. Lab 4 runs
real cloud evaluations; other labs include simulations or adaptation templates
as indicated in their instructions.

## 📋 Prerequisites

- Azure subscription with AI Foundry access
- Azure CLI authenticated (`az login`)
- Python 3.10+
- `azure-ai-projects>=2.8.0` (installed from the requirements below)
- A judge model deployment such as `gpt-4.1`
- An existing Foundry project and model deployment; Lab 03B selects an existing
  Contoso agent or explicitly creates a minimal reference agent
- Application Insights and a Log Analytics workspace for Lab 8's live trace option

## 🚀 Quick Start

Run these commands from the folder containing this README and
[requirements.txt](requirements.txt). Use a virtual environment; do not overwrite
an existing local configuration.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.template .env }
# Edit .env with your existing project, model, and agent settings.
jupyter notebook .\labs\lab-01-charter\lab-01-evaluation-charter.ipynb
```

Alternatively, open a notebook in VS Code and select the virtual environment's
kernel. Run cells from top to bottom. Keep the folder structure intact and use
each notebook's own directory as its working directory; some earlier labs write
outputs using notebook-relative paths. Cloud exercises incur usage charges.

### Using existing Azure resources

The notebooks and Lab 7 support runner load the `.env` beside
`.env.template`. Existing process environment variables take precedence, so CI/CD
secrets and model settings continue to work without a local file. The local
`.env` is ignored by Git.

For the supplied environment, use:

| Variable | Value |
|----------|-------|
| `AI_FOUNDRY_PROJECT_ENDPOINT` | `https://demopocaifoundry.services.ai.azure.com/api/projects/demoproject` |
| `TENANT_ID` | `16b3c013-d300-468d-ac64-7eda0820b6d3` |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | `gpt-4.1` |
| `AZURE_AI_SEARCH_ENDPOINT` | `https://demofoundryaisearch.search.windows.net` |
| `AZURE_AI_SEARCH_INDEX` | `underwriting-index` |

The endpoint uses `demoproject`, matching the supplied project resource ID.
This workshop reads `AI_FOUNDRY_PROJECT_ENDPOINT`, not
`AZURE_AI_PROJECT_ENDPOINT`. Its search index variable is
`AZURE_AI_SEARCH_INDEX`, not `AZURE_SEARCH_INDEX_NAME`; the search settings are
reserved in the template and are not currently consumed by the Python scripts
or notebooks. Unused settings (Bing, MCP, embeddings, OpenAI direct
access, and sensitive-content tracing) are not needed here.

Authenticate before running the notebooks or scripts:

```powershell
az login --tenant 16b3c013-d300-468d-ac64-7eda0820b6d3
az account set --subscription 93c5449c-bbb2-4249-9461-ddf749e03430
```

No API key or infrastructure deployment is required to use the existing project.
Before Lab 4, complete [Lab 03B reference-agent setup](labs/lab-03-evaluator-matrix/lab-03b-reference-agent-setup.ipynb).
It reuses an existing agent without modifying it; `CREATE_IF_MISSING=True`
explicitly permits creating a missing minimal prompt agent. Save the resolved
name and version in `.env` using its opt-in save cell (or copy the printed
settings). Restart already-running evaluation kernels after changing settings;
process environment variables still take precedence.
Lab 4 reuses the existing `contoso-support-agent-eval` agent by default, without
creating a new version. Set `AI_FOUNDRY_AGENT_NAME` and optionally
`AI_FOUNDRY_AGENT_VERSION` to select another existing agent/version. It registers
or reuses matching code-based and prompt-based custom evaluators, then runs them
alongside six built-in evaluators against real agent responses. Follow the
printed Foundry report URL to inspect results under **Automatic Evaluation** or
the project-level **Evaluations** page, not **Human Evaluation**.
Optional `LAB04_CODE_EVALUATOR_NAME`, `LAB04_TONE_EVALUATOR_NAME`, and their
`_VERSION` settings select existing compatible catalog entries; incompatible
definitions are never overwritten. These custom evaluator APIs are in preview.
The lab saves actual scores, pinned evaluator versions, and run IDs in its
baseline report, plus full per-item results with judge explanations. Compare
only reports with `valid_for_comparison: true` using matching datasets,
evaluator definitions, thresholds, and scales. All cases are retained, including
content-filter blocks and evaluator errors/skips; these make the report invalid
for CI/CD comparison. Missing scores are never counted as passes, and averages
include explicit usable/total/error counts;
Lab 7's simulated gate examples are not comparable cloud candidate results.

For live production monitoring in Lab 8, also supply
`APPLICATIONINSIGHTS_CONNECTION_STRING` and `APP_INSIGHTS_WORKSPACE_ID` in `.env`.
The latter is the Log Analytics workspace ID, not the Application Insights
application ID or instrumentation key.

## Learning order

| Lab | Open | What you learn |
| --- | --- | --- |
| 1 | [Evaluation charter](labs/lab-01-charter/lab-01-evaluation-charter.ipynb) | Define risks, quality, and ownership |
| 2 | [Golden dataset](labs/lab-02-golden-dataset/lab-02-golden-dataset.ipynb) | Build and validate test coverage |
| 3 | [Evaluator selection](labs/lab-03-evaluator-matrix/lab-03-evaluator-matrix.ipynb) | Map failures to metrics |
| 3B, setup | [Create/select reference agent](labs/lab-03-evaluator-matrix/lab-03b-reference-agent-setup.ipynb) | Resolve the evaluation target before using it; pin its name and version |
| 4 | [Basic agent evaluation](labs/lab-04-portal-sdk-custom/lab-04-portal-sdk-custom.ipynb) | Score real agent responses with built-in and custom evaluators; open the Foundry report |
| 4, optional | [Portal model exercise](labs/lab-04-portal-sdk-custom/README.md) | Evaluate the underlying model without modifying the agent |
| 5 | [RAG evaluation](labs/lab-05-rag-evaluation/lab-05-rag-evaluation.ipynb) | Compare simulated answering and retrieval configurations |
| 6 | [Agent/tool-trajectory evaluation](labs/lab-06-agent-evaluation/lab-06-agent-evaluation.ipynb) | Inspect answers and tool-use trajectories using a separate tool-enabled target |
| 6B, optional | [Advanced LLM-as-judge rubric](labs/lab-06-agent-evaluation/lab-06b-llm-as-judge-rubric.ipynb) | Calibrate weighted judging criteria after exploring RAG and agent failure modes |
| 7 | [CI/CD gate](labs/lab-07-cicd/lab-07-cicd-evaluation-gate.ipynb) | Practice passing/failing gates with synthetic scores and inspect pipeline templates |
| 8 | [Continuous evaluation](labs/lab-08-continuous-evaluation/lab-08-continuous-evaluation.ipynb) | Sample traces, judge responses, and plan monitoring |
| 9 | [Operating model](labs/lab-09-operating-model/lab-09-operating-model.ipynb) | Build the governance runbook |

For a shorter session, use Labs 1, 2, 3B, 4, 7, and 9. See the
[facilitator guide](facilitator/facilitator-guide.md) for timing.

### Basic evaluation before advanced judge calibration

Start with the [Lab 4 guide](labs/lab-04-portal-sdk-custom/README.md).
The main notebook evaluates the reference agent selected in Lab 03B. Follow it
with RAG (Lab 05), agent/tool trajectories (Lab 06), and then optional
[Lab 06B](labs/lab-06-agent-evaluation/lab-06b-llm-as-judge-rubric.ipynb), which demonstrates native rubric
evaluators using four hand-authored calibration responses, not new agent output;
`RUN_CLOUD=False` and `RUBRIC_REVIEWED=False` make cloud registration/scoring
explicit opt-ins. The portal exercise evaluates a model with policy context,
not the agent's retrieval or tools. Keep their results separate.
Lab 06 creates `contoso-support-agent-tools-eval`, a separate specialized target;
it does not replace the reference agent used by Labs 04 and 06B. The new minimal
reference agent has neither retrieval nor executable tools. Lab 05 remains a
simulation, not a live RAG deployment.

### Supporting files

- [datasets/](datasets/): golden, adversarial, and expected-action datasets used
  or produced by Lab 2.
- [Lab 7 support](labs/lab-07-cicd/README.md): the required runner and preserved
  gate configuration; pipeline YAML is generated by the notebook, not maintained
  as duplicate standalone templates. Read its limitations before adapting a pipeline.
- [Reference agent configuration](src/reference-agent/agent-config.yaml):
  Lab 03B uses its instructions only when explicitly creating a missing agent.
  Its tool entries are scenario references, not executable integrations.
- [Optional infrastructure](infrastructure/bicep/main.bicep): provisions supporting
  Azure resources (Log Analytics, Application Insights, Search, and Key Vault).
  It does **not** create the Foundry project, deploy a model, or deploy the agent.
  Existing-resource learners can skip it.
- [tests/](tests/): local regression tests for the evaluation notebooks.

Saved Lab 4 run identifiers and actual results remain in its lab folder.
Keep them for diagnosis and Lab 7 discussion, but do not use an incomplete or
`valid_for_comparison: false` report as a release baseline.

## Local validation

```powershell
python -m unittest discover -s tests -v
```

These tests do not submit paid cloud evaluations. They do not certify production
pipeline deployment or replace review of actual Foundry evaluation errors.

## 📄 License

Microsoft Internal - Customer Delivery IP
