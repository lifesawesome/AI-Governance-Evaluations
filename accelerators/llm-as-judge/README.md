# LLM-as-Judge Accelerator

Custom evaluators powered by GPT-4o that assess quality dimensions not covered by built-in evaluators.

## Included Evaluators

| Evaluator | Measures | Best For |
|-----------|----------|----------|
| Professional Tone | Workplace communication quality | Customer-facing agents |
| Domain Accuracy | Factual correctness against source docs | RAG/knowledge agents |
| Escalation Appropriateness | Correct human handoff decisions | Support agents |

## Usage

### As Python Library

```python
from llm_judge_evaluators import LLMJudgeEvaluator

evaluator = LLMJudgeEvaluator(openai_client, "gpt-4o")

# Single evaluator
result = evaluator.evaluate_professional_tone(query="How do I reset my password?", response="...")
print(f"Score: {result.score}/5, Label: {result.label}")

# All evaluators
results = evaluator.evaluate_all(query="...", response="...", context="...")
```

### From Command Line (CI/CD)

```bash
python llm_judge_evaluators.py \
    --dataset datasets/golden/contoso-golden-v1.jsonl \
    --evaluators professional_tone escalation \
    --output ./results.json \
    --threshold 4.0
```

## Customization

Each evaluator is a prompt template. To create your own:

1. Define the rubric (1-5 scale with clear criteria per level)
2. Specify the input fields (query, response, context, etc.)
3. Require JSON output format
4. Add to `LLMJudgeEvaluator` class

### Example: Custom Brand Voice Evaluator

```python
BRAND_VOICE_PROMPT = """
You are evaluating whether the response matches our brand voice guidelines:
- Friendly but professional
- Uses "we" not "the company"
- Avoids jargon
- Maximum 3 sentences per paragraph

Score 1-5:
5: Perfect brand voice
4: Minor deviation
3: Noticeable issues
2: Significant mismatch
1: Completely off-brand

Input: {query} / {response}
Output: {{"score": <1-5>, "reasoning": "<explanation>"}}
"""
```

## Cost Estimation

| Dataset Size | Evaluators | Approx. Tokens | Approx. Cost (GPT-4o) |
|-------------|------------|----------------|----------------------|
| 20 cases | 2 | ~20,000 | ~$0.10 |
| 50 cases | 3 | ~75,000 | ~$0.38 |
| 100 cases | 3 | ~150,000 | ~$0.75 |

## Integration with CI/CD Gate

Add LLM-as-judge results to the gate config:

```json
{
  "blocking_criteria": [
    {"evaluator": "professional_tone", "type": "absolute", "threshold": 4.0, "metric": "mean_score"}
  ]
}
```
