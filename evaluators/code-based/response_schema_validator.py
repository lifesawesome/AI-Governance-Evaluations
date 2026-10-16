"""
Response Schema Validator - Code-based evaluator

Checks that agent responses conform to expected output schemas.
Useful for ensuring agents produce structured, parseable responses.
"""

import json
import re


def validate_response_schema(response: str, expected_format: str = "text") -> dict:
    """
    Validate that the response matches the expected format.

    Args:
        response: The agent's response text
        expected_format: One of 'text', 'json', 'markdown_list', 'citation_required'

    Returns:
        dict with score (0-1), passed (bool), and details
    """
    if not response or not response.strip():
        return {"score": 0, "passed": False, "reason": "Empty response"}

    if expected_format == "json":
        try:
            json.loads(response)
            return {"score": 1.0, "passed": True, "reason": "Valid JSON"}
        except json.JSONDecodeError as e:
            return {"score": 0, "passed": False, "reason": f"Invalid JSON: {e}"}

    elif expected_format == "markdown_list":
        lines = response.strip().split("\n")
        list_lines = [l for l in lines if re.match(r"^\s*[-*\d+\.]\s+", l)]
        ratio = len(list_lines) / max(len(lines), 1)
        passed = ratio >= 0.5
        return {"score": ratio, "passed": passed, "reason": f"{len(list_lines)}/{len(lines)} lines are list items"}

    elif expected_format == "citation_required":
        has_citation = bool(re.search(r"(Policy\s+\d|Section\s+\d|Article\s+\d|per\s+\w+\s+policy)", response, re.I))
        return {"score": 1.0 if has_citation else 0, "passed": has_citation, "reason": "Citation found" if has_citation else "No policy citation found"}

    else:  # text
        word_count = len(response.split())
        passed = 5 <= word_count <= 500
        return {"score": 1.0 if passed else 0.5, "passed": passed, "reason": f"Word count: {word_count}"}


def validate_response_length(response: str, min_words: int = 10, max_words: int = 300) -> dict:
    """Check response length is within acceptable bounds."""
    word_count = len(response.split())
    if word_count < min_words:
        return {"score": 0, "passed": False, "reason": f"Too short: {word_count} words (min: {min_words})"}
    elif word_count > max_words:
        return {"score": 0.5, "passed": False, "reason": f"Too long: {word_count} words (max: {max_words})"}
    return {"score": 1.0, "passed": True, "reason": f"Acceptable length: {word_count} words"}


if __name__ == "__main__":
    # Quick test
    test_response = "Per HR Policy 3.1, full-time employees receive 20 days of annual leave."
    print(validate_response_schema(test_response, "citation_required"))
    print(validate_response_length(test_response))
