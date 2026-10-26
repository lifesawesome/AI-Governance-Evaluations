# Lab 7: instructional CI/CD evaluation gates

Start with the [Lab 7 notebook](lab-07-cicd-evaluation-gate.ipynb).
Run it top-to-bottom to define thresholds, compare synthetic baseline/candidate
scores, demonstrate a blocked release, and generate pipeline YAML and PR summaries.

## Files and outputs

- [gate-config.json](gate-config.json): preserved gate configuration; the notebook
  rewrites it from the editable configuration cell when that cell runs.
- [run_evaluation_gate.py](run_evaluation_gate.py): retained support template for
  the generated pipeline examples, not a separate accelerator.
- The notebook creates `github-actions/evaluation-gate.yml` and
  `azure-devops/evaluation-gate.yml` under this lab. These are outputs, not
  duplicate templates to maintain. They do not activate pipelines automatically.

The workflow paths assume the workshop folder is the checkout root. If the
workshop lives in a subfolder, adjust the checkout working directory, trigger
filters, requirements path, datasets, and runner path before using a template.
For GitHub, the workflow must also be placed under the repository's workflow
directory.

## Important boundaries before live pipeline use

The notebook's demonstrated PASS/FAIL scores are synthetic. They are **not**
the real Lab 4 baseline or a candidate Foundry run.

The retained cloud runner is an instructional integration template. Its live
execution has not been validated as part of this repository cleanup, and it
requires further adaptation before it can safely block production releases:

1. Update the agent-version lookup for the installed Projects SDK and pin the
   intended candidate agent/version.
2. Aggregate actual per-item evaluator output. A run summary's pass/fail counts
   are not raw mean scores, defect counts, or tool-selection accuracy. The runner's
   current summary extraction does not establish those metrics, and its evaluator
   set does not yet supply every metric in the example configuration.
3. Require a separately reviewed baseline and complete candidate evidence.
   Missing metrics must block comparison, not be skipped; do not use the
   runner's candidate-as-first-baseline fallback for release approval.
4. Adapt the validated Lab 4 export: require `valid_for_comparison: true`, matching
   datasets, evaluator versions, scales, and thresholds. Retain generation errors,
   evaluator failures, and skipped/missing results. The saved workshop cloud run
   is currently invalid for comparison and is diagnostic evidence only.
5. Configure your own Azure identity, permissions, project/model settings, and
   baseline storage. GitHub OIDC also requires `id-token: write`. Verify artifact
   publication, PR permissions, timeouts, and failed-run behavior in your CI system.
6. Enforce any declared sample-size/confidence requirements; configuration fields
   alone do not implement statistical validation.

Do not deploy the examples unchanged as a production release gate. This lab teaches
gate design and pipeline structure; production integration needs its own end-to-end
validation against real candidate runs.

Continue with [Lab 8](../lab-08-continuous-evaluation/lab-08-continuous-evaluation.ipynb)
to explore trace sampling and the monitoring feedback loop.
